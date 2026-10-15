begin;
create schema if not exists extensions;
create extension if not exists vector with schema extensions;
-- A ready job requires an active publication receipt, enforced below.
alter table gather_private.ingestion_jobs drop constraint ingestion_jobs_state_check;
alter table gather_private.ingestion_jobs add constraint ingestion_jobs_state_check
  check(state in ('queued','processing','failed','cancelled','ready'));
create table gather_private.staged_text (
  version_id uuid primary key references public.source_versions(id) on delete cascade,
  original bytea not null check(octet_length(original) between 1 and 65536),
  body text not null,
  manifest_hash bytea not null,
  expected_count integer not null check(expected_count between 1 and 256)
);
create table gather_private.staged_passages (
  version_id uuid not null references gather_private.staged_text(version_id) on delete cascade,
  ordinal integer not null check(ordinal between 0 and 255),
  passage_id text not null check(passage_id ~ '^[0-9a-f]{64}$'),
  start_offset integer not null check(start_offset>=0),
  end_offset integer not null check(end_offset>start_offset),
  body text not null check(octet_length(body) between 1 and 8192),
  embedding extensions.vector,
  primary key(version_id,passage_id), unique(version_id,ordinal)
);
create table gather_private.published_sources (
  source_id uuid primary key references public.sources(id) on delete cascade,
  version_id uuid not null unique references gather_private.staged_text(version_id) on delete cascade,
  job_id uuid not null unique references gather_private.ingestion_jobs(id) on delete cascade,
  token_hash bytea not null
);
revoke all on gather_private.staged_text,gather_private.staged_passages,gather_private.published_sources
  from public,anon,authenticated,gather_ingestion_worker;

create function gather_private.guard_ready_publication() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if new.state='ready' and old.state is distinct from 'ready' then
    if old.state<>'processing' or old.lease_token is null or old.lease_expires_at<=clock_timestamp()
      or not exists(select 1 from gather_private.published_sources p
        join gather_private.ingestion_targets t on t.source_id=p.source_id and t.version_id=p.version_id
        join public.sources s on s.id=p.source_id and s.owner_id=old.owner_id and s.deleted_at is null
        where p.job_id=old.id and p.version_id=old.version_id
          and p.token_hash=sha256(convert_to(old.lease_token::text,'UTF8'))) then
      raise exception 'publication_required' using errcode='23514';
    end if;
  end if;
  return new;
end $$;
revoke all on function gather_private.guard_ready_publication() from public,anon,authenticated,gather_ingestion_worker;
create trigger require_publication before update on gather_private.ingestion_jobs
  for each row execute function gather_private.guard_ready_publication();

create function gather_private.stage_text(p_job uuid,p_token uuid,p_original bytea,p_media text,p_manifest jsonb)
returns uuid language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; v public.source_versions%rowtype;
  body text; m jsonb; n integer; a integer; b integer; prev_a integer:=-1; prev_b integer:=0;
  fingerprint bytea; existing bytea; idx integer:=0;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  select * into v from public.source_versions where id=j.version_id;
  if p_original is null or octet_length(p_original)<>j.input_bytes or octet_length(p_original)>65536
     or p_media is distinct from j.media_type or v.parser_version<>'utf8-plain-v1'
     or encode(sha256(p_original),'hex')<>v.content_sha256 then
    raise exception 'source_integrity' using errcode='22023';
  end if;
  begin body:=convert_from(p_original,'UTF8');
  exception when others then raise exception 'invalid_utf8' using errcode='22023'; end;
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
  fingerprint:=sha256(convert_to(p_manifest::text,'UTF8'));
  select manifest_hash into existing from gather_private.staged_text where version_id=j.version_id;
  if found then
    if existing<>fingerprint then raise exception 'manifest_conflict' using errcode='22023'; end if;
    return j.version_id;
  end if;
  insert into gather_private.staged_text values(j.version_id,p_original,body,fingerprint,n);
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

create function gather_private.stage_vectors(p_job uuid,p_token uuid,p_model text,p_revision text,p_dimensions integer,p_rows jsonb)
returns integer language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; r jsonb; vec extensions.vector;
  old extensions.vector; seen text[]:='{}'; n integer;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  if p_model is distinct from j.model_id or p_revision is distinct from j.model_revision or p_dimensions is distinct from j.dimensions then
    raise exception 'embedding_identity' using errcode='22023'; end if;
  if p_rows is null or jsonb_typeof(p_rows)<>'array' or octet_length(p_rows::text)>524288 then
    raise exception 'invalid_vectors' using errcode='22023'; end if;
  n:=jsonb_array_length(p_rows);
  if n not between 1 and 16 then raise exception 'vector_batch_limit' using errcode='22023'; end if;
  for r in select value from jsonb_array_elements(p_rows) loop
    if jsonb_typeof(r)<>'object' or not (r ?& array['id','vector']) or (r-array['id','vector'])<>'{}'::jsonb
      or jsonb_typeof(r->'id')<>'string' or jsonb_typeof(r->'vector')<>'array' then
      raise exception 'invalid_vector' using errcode='22023'; end if;
    if r->>'id'=any(seen) then raise exception 'duplicate_vector' using errcode='22023'; end if;
    seen:=array_append(seen,r->>'id');
    if jsonb_array_length(r->'vector')<>j.dimensions or exists(
      select 1 from jsonb_array_elements(r->'vector') x where jsonb_typeof(x)<>'number') then
      raise exception 'vector_dimensions_or_values' using errcode='22023'; end if;
    -- pgvector rejects NaN, Infinity and float32 overflow, including numeric overflow.
    vec:=(r->'vector')::text::extensions.vector;
    if abs(extensions.vector_norm(vec)-1)>0.001 then
      raise exception 'vector_not_normalized' using errcode='22023'; end if;
    select embedding into old from gather_private.staged_passages where version_id=j.version_id and passage_id=r->>'id';
    if not found then raise exception 'unknown_passage' using errcode='22023'; end if;
    if old is not null and old::text<>vec::text then raise exception 'vector_conflict' using errcode='22023'; end if;
    update gather_private.staged_passages set embedding=vec where version_id=j.version_id and passage_id=r->>'id';
  end loop;
  perform gather_private.lock_live_job(p_job,p_token);
  return n;
end $$;

create function gather_private.publish_text(p_job uuid,p_token uuid) returns uuid
language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; sid uuid; expected integer;
begin
  select source_id into sid from gather_private.ingestion_jobs where id=p_job;
  perform 1 from public.sources where id=sid and deleted_at is null for update;
  if not found then raise exception 'stale_lease' using errcode='55000'; end if;
  -- Lost response retry is read-only and only succeeds for this exact active publication.
  select q.* into j from gather_private.ingestion_jobs q
    join gather_private.ingestion_targets t on t.version_id=q.version_id where q.id=p_job;
  if j.state='ready' and p_token is not null and exists(select 1 from gather_private.published_sources p
    where p.job_id=p_job and p.token_hash=sha256(convert_to(p_token::text,'UTF8'))) then return j.version_id; end if;
  j:=gather_private.lock_live_job(p_job,p_token);
  select expected_count into expected from gather_private.staged_text where version_id=j.version_id;
  if expected is null or (select count(*) from gather_private.staged_passages where version_id=j.version_id
    and embedding is not null and extensions.vector_dims(embedding)=j.dimensions)<>expected then
    raise exception 'incomplete_index' using errcode='22023'; end if;
  perform gather_private.lock_live_job(p_job,p_token);
  insert into gather_private.published_sources values(j.source_id,j.version_id,j.id,sha256(convert_to(p_token::text,'UTF8')))
    on conflict(source_id) do update set version_id=excluded.version_id,job_id=excluded.job_id,token_hash=excluded.token_hash;
  update gather_private.ingestion_jobs set state='ready',error_code=null,
    lease_token=null,lease_started_at=null,lease_expires_at=null where id=p_job;
  return j.version_id;
end $$;

-- Read boundary for search/context adapters: only the published version of an owned live source.
create function public.read_published_text(p_source uuid)
returns table(version_id uuid,source_sha256 text,parser_version text,chunker_version text,
  model_id text,model_revision text,dimensions integer,passage_id text,start_offset integer,end_offset integer,body text)
language sql security definer set search_path='' stable as $$
 select p.version_id,v.content_sha256,v.parser_version,j.chunker_version,j.model_id,j.model_revision,j.dimensions,
   c.passage_id,c.start_offset,c.end_offset,c.body
 from gather_private.published_sources p join public.sources s on s.id=p.source_id
 join public.source_versions v on v.id=p.version_id
 join gather_private.ingestion_jobs j on j.id=p.job_id
 join gather_private.staged_passages c on c.version_id=p.version_id
 where s.id=p_source and s.owner_id=auth.uid() and s.deleted_at is null order by c.ordinal
$$;
revoke all on function gather_private.stage_text(uuid,uuid,bytea,text,jsonb),
 gather_private.stage_vectors(uuid,uuid,text,text,integer,jsonb),gather_private.publish_text(uuid,uuid)
 from public,anon,authenticated;
grant execute on function gather_private.stage_text(uuid,uuid,bytea,text,jsonb),
 gather_private.stage_vectors(uuid,uuid,text,text,integer,jsonb),gather_private.publish_text(uuid,uuid)
 to gather_ingestion_worker;
revoke all on function public.read_published_text(uuid) from public,anon,authenticated;
grant execute on function public.read_published_text(uuid) to authenticated;
commit;
