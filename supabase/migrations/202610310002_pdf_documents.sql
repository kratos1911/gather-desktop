-- Additive private PDF support. Hosted application requires separate approval.
begin;
alter table gather_private.ingestion_jobs drop constraint ingestion_jobs_media_type_check;
alter table gather_private.ingestion_jobs add constraint ingestion_jobs_media_type_check
  check(media_type in ('text/plain','text/markdown','application/pdf'));
create table gather_private.pdf_text (
  version_id uuid primary key references gather_private.staged_text(version_id) on delete cascade,
  text_sha256 text not null check(text_sha256 ~ '^[0-9a-f]{64}$'),
  pages jsonb not null check(jsonb_typeof(pages)='array' and octet_length(pages::text)<=8192)
);
alter table gather_private.pdf_text enable row level security;
revoke all on gather_private.pdf_text from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;

create or replace function gather_private.enqueue_text_job(p_owner uuid,p_source uuid,p_request uuid,
  p_sha256 text,p_parser text,p_bytes integer,p_media text,p_chunker text,
  p_model text,p_revision text,p_dimensions integer) returns uuid
language plpgsql security definer set search_path='' as $$
declare v_fingerprint bytea; v_job gather_private.ingestion_jobs%rowtype; v_version uuid; v_id uuid;
begin
  if p_owner is null or p_source is null or p_request is null or
    p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or
    p_parser is null or length(p_parser) not between 1 and 200 or
    p_bytes is null or p_bytes not between 1 and 65536 or
    p_media is null or p_media not in ('text/plain','text/markdown','application/pdf') or
    (p_media='application/pdf' and p_parser is distinct from 'pdf-pypdf6.21.4-text-v1') or
    p_chunker is null or length(p_chunker) not between 1 and 200 or
    p_model is null or length(p_model) not between 1 and 200 or
    p_revision is null or length(p_revision) not between 1 and 200 or
    p_dimensions is null or p_dimensions not in (256,512,1024) then
    raise exception 'invalid_job' using errcode='22023';
  end if;
  -- Same quota -> source -> job lock order as save/delete/cleanup.
  perform 1 from gather_private.source_quotas where owner_id=p_owner for update;
  if not found then raise exception 'quota_not_configured' using errcode='P0001'; end if;
  perform 1 from public.sources where id=p_source and owner_id=p_owner
    and kind='file' and deleted_at is null for update;
  if not found then raise exception 'source_not_writable' using errcode='23503'; end if;
  v_fingerprint := sha256(convert_to(jsonb_build_array(p_source,p_sha256,p_parser,p_bytes,
    p_media,p_chunker,p_model,p_revision,p_dimensions)::text,'UTF8'));
  select * into v_job from gather_private.ingestion_jobs where owner_id=p_owner and request_key=p_request;
  if found then
    if v_job.fingerprint<>v_fingerprint then raise exception 'request_key_conflict' using errcode='22023'; end if;
    return v_job.id;
  end if;
  -- Bound retained scheduling metadata. No eviction or silent receipt loss.
  if (select count(*) from gather_private.ingestion_jobs where source_id=p_source)>=16 then
    raise exception 'version_limit_reached' using errcode='P0001';
  end if;
  insert into public.source_versions(source_id,owner_id,content_sha256,parser_version)
    values(p_source,p_owner,p_sha256,p_parser) returning id into v_version;
  update gather_private.ingestion_jobs set state='cancelled',error_code='superseded',
    lease_token=null,lease_started_at=null,lease_expires_at=null where source_id=p_source;
  insert into gather_private.ingestion_jobs(owner_id,source_id,version_id,request_key,fingerprint,
    input_bytes,media_type,chunker_version,model_id,model_revision,dimensions)
    values(p_owner,p_source,v_version,p_request,v_fingerprint,p_bytes,p_media,p_chunker,p_model,p_revision,p_dimensions)
    returning id into v_id;
  insert into gather_private.ingestion_targets values(p_source,p_owner,v_version)
    on conflict(source_id) do update set version_id=excluded.version_id;
  return v_id;
end $$;

create function gather_private.stage_pdf(p_job uuid,p_token uuid,p_original bytea,p_body text,p_pages jsonb,p_manifest jsonb)
returns uuid language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; v public.source_versions%rowtype;
  body text; m jsonb; n integer; a integer; b integer; prev_a integer:=-1; prev_b integer:=0;
  fingerprint bytea; existing bytea; idx integer:=0;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  select * into v from public.source_versions where id=j.version_id;
  if p_original is null or octet_length(p_original)<>j.input_bytes or octet_length(p_original)>65536
     or j.media_type<>'application/pdf' or v.parser_version<>'pdf-pypdf6.21.4-text-v1'
     or encode(sha256(p_original),'hex')<>v.content_sha256 then
    raise exception 'source_integrity' using errcode='22023';
  end if;
  body:=p_body;
  if body is null or octet_length(body) not between 1 and 65536
    or substring(p_original from 1 for 5)<>decode('255044462d','hex')
    or not exists(select 1 from gather_private.job_originals o where o.version_id=j.version_id and o.original=p_original)
    or p_pages is null or jsonb_typeof(p_pages)<>'array' then
    raise exception 'source_integrity' using errcode='22023'; end if;
  if jsonb_array_length(p_pages) not between 1 and 20 then
    raise exception 'page_limit' using errcode='22023'; end if;
  for m in select value from jsonb_array_elements(p_pages) loop
    if jsonb_typeof(m)<>'object' or not (m ?& array['number','start','end'])
      or (m-array['number','start','end'])<>'{}'::jsonb
      or jsonb_typeof(m->'number')<>'number' or jsonb_typeof(m->'start')<>'number' or jsonb_typeof(m->'end')<>'number'
      or (m->>'number')!~'^[1-9][0-9]?$' or (m->>'start')!~'^(0|[1-9][0-9]{0,5})$'
      or (m->>'end')!~'^[1-9][0-9]{0,5}$' then
      raise exception 'page_coverage' using errcode='22023'; end if;
    if (m->>'number')::integer<>idx+1 or (m->>'start')::integer<>prev_b
      or (m->>'end')::integer<=prev_b or (m->>'end')::integer>length(body)
      or btrim(substr(body,prev_b+1,(m->>'end')::integer-prev_b),E' \t\r\n')='' then
      raise exception 'page_coverage' using errcode='22023'; end if;
    prev_b:=(m->>'end')::integer; idx:=idx+1;
  end loop;
  if prev_b<>length(body) then raise exception 'page_coverage' using errcode='22023'; end if;
  idx:=0; prev_b:=0;
  -- Match Python's Unicode whitespace policy without normalizing source bytes.
  if btrim(ltrim(body,chr(65279)),E' \t\r\n'||chr(160)||chr(5760)||
    chr(8192)||chr(8193)||chr(8194)||chr(8195)||chr(8196)||chr(8197)||chr(8198)||
    chr(8199)||chr(8200)||chr(8201)||chr(8202)||chr(8232)||chr(8233)||chr(8239)||chr(8287)||chr(12288))='' or
    body ~ ('['||chr(1)||'-'||chr(8)||chr(11)||chr(12)||chr(14)||'-'||chr(31)||chr(127)||'-'||chr(159)||']') then
    raise exception 'invalid_text' using errcode='22023';
  end if;
  if p_manifest is null or jsonb_typeof(p_manifest)<>'array' or octet_length(p_manifest::text)>524288 then
    raise exception 'invalid_manifest' using errcode='22023';
  end if;
  n:=jsonb_array_length(p_manifest);
  if n not between 1 and 256 then raise exception 'passage_limit' using errcode='22023'; end if;
  fingerprint:=sha256(convert_to(jsonb_build_array(p_manifest,p_pages,encode(sha256(convert_to(body,'UTF8')),'hex'))::text,'UTF8'));
  select manifest_hash into existing from gather_private.staged_text where version_id=j.version_id;
  if found then
    if existing<>fingerprint then raise exception 'manifest_conflict' using errcode='22023'; end if;
    return j.version_id;
  end if;
  insert into gather_private.staged_text values(j.version_id,p_original,body,fingerprint,n);
  insert into gather_private.pdf_text values(j.version_id,encode(sha256(convert_to(body,'UTF8')),'hex'),p_pages);
  for m in select value from jsonb_array_elements(p_manifest) loop
    if jsonb_typeof(m)<>'object' or not (m ?& array['id','start','end'])
      or (m-array['id','start','end'])<>'{}'::jsonb or jsonb_typeof(m->'id')<>'string'
      or jsonb_typeof(m->'start')<>'number' or jsonb_typeof(m->'end')<>'number'
      or (m->>'id')!~'^[0-9a-f]{64}$' or (m->>'start')!~'^(0|[1-9][0-9]{0,5})$'
      or (m->>'end')!~'^[1-9][0-9]{0,5}$' then
      raise exception 'invalid_passage' using errcode='22023';
    end if;
    a:=(m->>'start')::integer; b:=(m->>'end')::integer;
    if a<=prev_a or a>prev_b or b<=prev_b or b>length(body) or b<=a
      or octet_length(substr(body,a+1,b-a))>8192 then
      raise exception 'passage_coverage' using errcode='22023';
    end if;
    insert into gather_private.staged_passages(version_id,ordinal,passage_id,start_offset,end_offset,body)
      values(j.version_id,idx,m->>'id',a,b,substr(body,a+1,b-a));
    prev_a:=a; prev_b:=b; idx:=idx+1;
  end loop;
  if prev_b<>length(body) then raise exception 'passage_coverage' using errcode='22023'; end if;
  -- Validation may be nontrivial; fence again immediately before returning.
  perform gather_private.lock_live_job(p_job,p_token);
  return j.version_id;
end $$;

-- Separate exact-version metadata keeps the existing text RPC compatible.
create function public.read_published_pdf(p_source uuid,p_version uuid) returns jsonb
language sql security definer set search_path='' stable as $$
  select jsonb_build_object('media_type','application/pdf','text_sha256',d.text_sha256,'pages',d.pages)
  from gather_private.published_sources p
  join public.sources s on s.id=p.source_id
  join gather_private.pdf_text d on d.version_id=p.version_id
  where s.owner_id=auth.uid() and s.deleted_at is null and s.id=p_source and p.version_id=p_version
$$;
revoke all on function gather_private.stage_pdf(uuid,uuid,bytea,text,jsonb,jsonb),public.read_published_pdf(uuid,uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function gather_private.stage_pdf(uuid,uuid,bytea,text,jsonb,jsonb) to gather_ingestion_worker;
grant execute on function public.read_published_pdf(uuid,uuid) to authenticated;
commit;
