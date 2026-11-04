-- Private image OCR extension. Hosted apply requires explicit approval.
begin;
alter table gather_private.ingestion_jobs drop constraint ingestion_jobs_media_type_check;
alter table gather_private.ingestion_jobs add constraint ingestion_jobs_media_type_check check(media_type in
 ('text/plain','text/markdown','application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','image/png','image/jpeg'));
create table gather_private.image_text (
 version_id uuid primary key references gather_private.staged_text(version_id) on delete cascade,
 text_sha256 text not null check(text_sha256 ~ '^[0-9a-f]{64}$'),
 metadata jsonb not null check(jsonb_typeof(metadata)='object' and octet_length(metadata::text)<=32768)
);
alter table gather_private.image_text enable row level security;
alter table gather_private.image_text force row level security;
revoke all on gather_private.image_text from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;

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
    p_media is null or p_media not in ('text/plain','text/markdown','application/pdf','application/vnd.openxmlformats-officedocument.wordprocessingml.document','image/png','image/jpeg') or
    (p_media='application/pdf' and p_parser is distinct from 'pdf-pypdf6.21.4-text-v1') or
    (p_media='application/vnd.openxmlformats-officedocument.wordprocessingml.document' and p_parser is distinct from 'docx-ooxml-body-v1') or
    (p_media in ('image/png','image/jpeg') and p_parser is distinct from 'image-tesseract-5.5.0-eng-v1') or
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

create or replace function gather_private.stage_extracted_document(p_job uuid,p_token uuid,p_original bytea,p_body text,p_locations jsonb,p_manifest jsonb,p_expected_media text)
returns uuid language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; v public.source_versions%rowtype;
  body text; m jsonb; n integer; a integer; b integer; prev_a integer:=-1; prev_b integer:=0;
  fingerprint bytea; existing bytea; idx integer:=0;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  select * into v from public.source_versions where id=j.version_id;
  if p_original is null or octet_length(p_original)<>j.input_bytes or octet_length(p_original)>65536
     or j.media_type is distinct from p_expected_media
     or not ((j.media_type='application/pdf' and v.parser_version='pdf-pypdf6.21.4-text-v1')
       or (j.media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document' and v.parser_version='docx-ooxml-body-v1')
       or (j.media_type in ('image/png','image/jpeg') and v.parser_version='image-tesseract-5.5.0-eng-v1'))
     or encode(sha256(p_original),'hex')<>v.content_sha256 then
    raise exception 'source_integrity' using errcode='22023';
  end if;
  body:=p_body;
  if body is null or octet_length(body) not between 1 and 65536
    or (j.media_type='application/pdf' and substring(p_original from 1 for 5)<>decode('255044462d','hex'))
    or (j.media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document' and substring(p_original from 1 for 4)<>decode('504b0304','hex'))
    or (j.media_type='image/png' and substring(p_original from 1 for 8)<>decode('89504e470d0a1a0a','hex'))
    or (j.media_type='image/jpeg' and substring(p_original from 1 for 3)<>decode('ffd8ff','hex'))
    or not exists(select 1 from gather_private.job_originals o where o.version_id=j.version_id and o.original=p_original)
    or p_locations is null or jsonb_typeof(p_locations)<>'array' then
    raise exception 'source_integrity' using errcode='22023'; end if;
  if octet_length(p_locations::text)>8192 or jsonb_array_length(p_locations) not between 1 and
    (case when j.media_type='application/pdf' then 20 else 128 end) then
    raise exception 'page_limit' using errcode='22023'; end if;
  for m in select value from jsonb_array_elements(p_locations) loop
    if jsonb_typeof(m)<>'object' or not (m ?& array['number','start','end'])
      or (m-array['number','start','end'])<>'{}'::jsonb
      or jsonb_typeof(m->'number')<>'number' or jsonb_typeof(m->'start')<>'number' or jsonb_typeof(m->'end')<>'number'
      or (m->>'number')!~'^[1-9][0-9]{0,2}$' or (m->>'start')!~'^(0|[1-9][0-9]{0,5})$'
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
  fingerprint:=sha256(convert_to(jsonb_build_array(p_manifest,p_locations,encode(sha256(convert_to(body,'UTF8')),'hex'))::text,'UTF8'));
  select manifest_hash into existing from gather_private.staged_text where version_id=j.version_id;
  if found then
    if existing<>fingerprint then raise exception 'manifest_conflict' using errcode='22023'; end if;
    return j.version_id;
  end if;
  insert into gather_private.staged_text values(j.version_id,p_original,body,fingerprint,n);
  if j.media_type='application/pdf' then
    insert into gather_private.pdf_text values(j.version_id,encode(sha256(convert_to(body,'UTF8')),'hex'),p_locations);
  elsif j.media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document' then
    insert into gather_private.docx_text values(j.version_id,encode(sha256(convert_to(body,'UTF8')),'hex'),p_locations);
  end if;
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


create function gather_private.stage_image(p_job uuid,p_token uuid,p_original bytea,p_body text,p_metadata jsonb,p_manifest jsonb)
returns uuid language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; r jsonb; k text; w integer; h integer;
 locations jsonb:='[]'::jsonb; v_id uuid; existing jsonb;
begin
 j:=gather_private.lock_live_job(p_job,p_token);
 if j.media_type not in ('image/png','image/jpeg') or p_metadata is null or jsonb_typeof(p_metadata)<>'object'
  or not(p_metadata ?& array['media_type','width','height','engine','ocr_model_sha256','language','regions'])
  or (p_metadata-array['media_type','width','height','engine','ocr_model_sha256','language','regions'])<>'{}'::jsonb
  or p_metadata->>'media_type' is distinct from j.media_type
  or p_metadata->>'engine' is distinct from 'tesseract-5.5.0-lstm'
  or p_metadata->>'ocr_model_sha256' is distinct from '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'
  or p_metadata->>'language' is distinct from 'eng'
  or jsonb_typeof(p_metadata->'width')<>'number' or jsonb_typeof(p_metadata->'height')<>'number'
  or (p_metadata->>'width')!~'^[1-9][0-9]{0,3}$' or (p_metadata->>'height')!~'^[1-9][0-9]{0,3}$'
  or jsonb_typeof(p_metadata->'regions')<>'array' or octet_length(p_metadata::text)>32768 then
  raise exception 'image_metadata' using errcode='22023';
 end if;
 w:=(p_metadata->>'width')::integer; h:=(p_metadata->>'height')::integer;
 if w>4096 or h>4096 or w*h>1048576 or jsonb_array_length(p_metadata->'regions') not between 1 and 128 then
  raise exception 'image_dimensions' using errcode='22023'; end if;
 for r in select value from jsonb_array_elements(p_metadata->'regions') loop
  if jsonb_typeof(r)<>'object' or not(r ?& array['number','start','end','x','y','width','height','confidence'])
   or (r-array['number','start','end','x','y','width','height','confidence'])<>'{}'::jsonb then
   raise exception 'image_regions' using errcode='22023'; end if;
  foreach k in array array['number','start','end','x','y','width','height'] loop
   if jsonb_typeof(r->k)<>'number' or (r->>k)!~'^(0|[1-9][0-9]{0,5})$' then
    raise exception 'image_regions' using errcode='22023'; end if;
  end loop;
  if jsonb_typeof(r->'confidence')<>'number' or (r->>'confidence')::numeric not between 0 and 100
   or (r->>'width')::integer<1 or (r->>'height')::integer<1
   or (r->>'x')::integer+(r->>'width')::integer>w
   or (r->>'y')::integer+(r->>'height')::integer>h then
   raise exception 'image_regions' using errcode='22023'; end if;
  locations:=locations||jsonb_build_array(jsonb_build_object('number',r->'number','start',r->'start','end',r->'end'));
 end loop;
 v_id:=gather_private.stage_extracted_document(p_job,p_token,p_original,p_body,locations,p_manifest,j.media_type);
 select metadata into existing from gather_private.image_text where version_id=v_id;
 if found then
  if existing<>p_metadata then raise exception 'manifest_conflict' using errcode='22023'; end if;
 else
  insert into gather_private.image_text values(v_id,encode(sha256(convert_to(p_body,'UTF8')),'hex'),p_metadata);
 end if;
 perform gather_private.lock_live_job(p_job,p_token);
 return v_id;
end $$;

create function public.read_published_image(p_source uuid,p_version uuid) returns jsonb
language sql security definer set search_path='' stable as $$
 select d.metadata||jsonb_build_object('text_sha256',d.text_sha256)
 from gather_private.published_sources p join public.sources s on s.id=p.source_id
 join gather_private.image_text d on d.version_id=p.version_id
 where s.owner_id=auth.uid() and s.deleted_at is null and s.id=p_source and p.version_id=p_version
$$;
create function public.read_published_image_original(p_source uuid,p_version uuid) returns jsonb
language sql security definer set search_path='' stable as $$
 select jsonb_build_object('media_type',d.metadata->>'media_type','source_sha256',v.content_sha256,
  'content_base64',replace(encode(t.original,'base64'),E'\n',''))
 from gather_private.published_sources p join public.sources s on s.id=p.source_id
 join public.source_versions v on v.id=p.version_id
 join gather_private.staged_text t on t.version_id=p.version_id
 join gather_private.image_text d on d.version_id=p.version_id
 where s.owner_id=auth.uid() and s.deleted_at is null and s.id=p_source and p.version_id=p_version
$$;
revoke all on function gather_private.stage_image(uuid,uuid,bytea,text,jsonb,jsonb),
 public.read_published_image(uuid,uuid),public.read_published_image_original(uuid,uuid)
 from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function gather_private.stage_image(uuid,uuid,bytea,text,jsonb,jsonb) to gather_ingestion_worker;
grant execute on function public.read_published_image(uuid,uuid),public.read_published_image_original(uuid,uuid) to authenticated;
commit;
