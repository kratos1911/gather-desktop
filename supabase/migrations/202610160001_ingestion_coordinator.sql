begin;
create role gather_ingestion_coordinator nologin;
grant usage on schema gather_private to gather_ingestion_coordinator;
create table gather_private.job_originals (
  version_id uuid primary key references public.source_versions(id) on delete cascade,
  original bytea not null check(octet_length(original) between 1 and 65536)
);
revoke all on gather_private.job_originals from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;

-- Internal admission only. The server supplies auth.uid() from verified context.
-- Source, version, receipt, original and job either all commit or all roll back.
create function gather_private.submit_text(p_request uuid,p_title text,p_original bytea,
  p_media text,p_parser text,p_chunker text,p_model text,p_revision text,p_dimensions integer,
  p_source uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare owner_id uuid:=auth.uid(); sid uuid; jid uuid; vid uuid; existing bytea;
begin
  if owner_id is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_original is null or octet_length(p_original) not between 1 and 65536 then
    raise exception 'invalid_input' using errcode='22023'; end if;
  sid:=p_source;
  if sid is null then sid:=public.save_source(p_request,'file',p_title); end if;
  jid:=gather_private.enqueue_text_job(owner_id,sid,p_request,encode(sha256(p_original),'hex'),
    p_parser,octet_length(p_original),p_media,p_chunker,p_model,p_revision,p_dimensions);
  select version_id into vid from gather_private.ingestion_jobs where id=jid;
  insert into gather_private.job_originals values(vid,p_original) on conflict do nothing;
  select original into existing from gather_private.job_originals where version_id=vid;
  if existing<>p_original then raise exception 'original_conflict' using errcode='22023'; end if;
  return jsonb_build_object('source_id',sid,'job_id',jid,'version_id',vid);
end $$;

create function gather_private.read_job_original(p_job uuid,p_token uuid) returns text
language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; data bytea;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  select original into data from gather_private.job_originals where version_id=j.version_id;
  if data is null then raise exception 'missing_original' using errcode='22023'; end if;
  return encode(data,'hex');
end $$;
create function gather_private.completed_passages(p_job uuid,p_token uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare j gather_private.ingestion_jobs%rowtype; result jsonb;
begin
  j:=gather_private.lock_live_job(p_job,p_token);
  select coalesce(jsonb_agg(passage_id),'[]'::jsonb) into result
    from gather_private.staged_passages where version_id=j.version_id and embedding is not null;
  return result;
end $$;
revoke all on function gather_private.submit_text(uuid,text,bytea,text,text,text,text,text,integer,uuid),
 gather_private.read_job_original(uuid,uuid),gather_private.completed_passages(uuid,uuid)
 from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function gather_private.submit_text(uuid,text,bytea,text,text,text,text,text,integer,uuid)
 to gather_ingestion_coordinator;
grant execute on function gather_private.read_job_original(uuid,uuid),gather_private.completed_passages(uuid,uuid)
 to gather_ingestion_worker;
commit;
