-- Opted-in new imports only. Existing jobs are deliberately not enrolled.
begin;
create table gather_private.automatic_text_jobs (
  job_id uuid primary key references gather_private.ingestion_jobs(id) on delete cascade,
  requested_attempt integer not null default 1 check(requested_attempt between 1 and 3)
);
alter table gather_private.automatic_text_jobs enable row level security;
-- No client policies: default deny in addition to revoked direct table grants.
revoke all on gather_private.automatic_text_jobs from public,anon,authenticated,
  gather_ingestion_worker,gather_ingestion_coordinator;

create function gather_private.submit_automatic_text(p_request uuid,p_title text,p_original bytea,
  p_media text,p_parser text,p_chunker text,p_model text,p_revision text,p_dimensions integer,
  p_source uuid default null) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_owner uuid:=auth.uid(); result jsonb; existed boolean;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  -- Same quota -> source -> job ordering as admission; serialize identical retries.
  perform 1 from gather_private.source_quotas where owner_id=v_owner for update;
  select exists(select 1 from gather_private.ingestion_jobs j where j.owner_id=v_owner
    and j.request_key=p_request) into existed;
  result:=gather_private.submit_text(p_request,p_title,p_original,p_media,p_parser,p_chunker,p_model,p_revision,p_dimensions,p_source);
  if not existed then
    insert into gather_private.automatic_text_jobs(job_id) values((result->>'job_id')::uuid);
  end if;
  return result || jsonb_build_object('automatic_processing',exists(
    select 1 from gather_private.automatic_text_jobs where job_id=(result->>'job_id')::uuid));
end $$;

create function gather_private.next_automatic_text_job() returns uuid
language sql security definer set search_path='' as $$
  select j.id from gather_private.automatic_text_jobs a
  join gather_private.ingestion_jobs j on j.id=a.job_id
  join gather_private.ingestion_targets t on t.version_id=j.version_id
  join public.sources s on s.id=j.source_id
  where s.deleted_at is null and j.attempts<a.requested_attempt
    and ((j.state='queued' and j.next_attempt_at<=clock_timestamp())
      or (j.state='processing' and j.lease_expires_at<=clock_timestamp()))
    and not exists(select 1 from gather_private.ingestion_jobs live
      where live.state='processing' and live.lease_expires_at>clock_timestamp())
  order by j.next_attempt_at,j.created_at,j.id limit 1;
$$;

create function gather_private.claim_automatic_text_job(p_job uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare sid uuid;
begin
  if p_job is null or not pg_try_advisory_xact_lock(714011,1) then return null; end if;
  select j.source_id into sid from gather_private.ingestion_jobs j where j.id=p_job;
  perform 1 from public.sources where id=sid for update;
  perform 1 from gather_private.ingestion_jobs j join gather_private.automatic_text_jobs a on a.job_id=j.id
    where j.id=p_job and j.attempts<a.requested_attempt for update of j;
  if not found then return null; end if;
  return gather_private.claim_text_job_internal(p_job);
end $$;

-- Explicit user recovery only; no automatic second inference attempt. A failed
-- request cannot raise the requested attempt repeatedly while the job is idle.
create function public.request_automatic_processing(p_source uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare v_owner uuid:=auth.uid(); j gather_private.ingestion_jobs%rowtype;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  perform 1 from public.sources s where s.id=p_source and s.owner_id=v_owner
    and s.deleted_at is null for update;
  if not found then return false; end if;
  select jobs.* into j from gather_private.ingestion_jobs jobs
    join gather_private.ingestion_targets t on t.version_id=jobs.version_id
    join gather_private.automatic_text_jobs a on a.job_id=jobs.id
    where t.source_id=p_source for update of jobs;
  if not found or j.attempts>=3 or not ((j.state='queued' and j.next_attempt_at<=clock_timestamp())
    or (j.state='processing' and j.lease_expires_at<=clock_timestamp())) then return false; end if;
  update gather_private.automatic_text_jobs set requested_attempt=j.attempts+1 where job_id=j.id;
  return true;
end $$;

revoke all on function gather_private.submit_automatic_text(uuid,text,bytea,text,text,text,text,text,integer,uuid),
  gather_private.next_automatic_text_job(),gather_private.claim_automatic_text_job(uuid),
  public.request_automatic_processing(uuid)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function gather_private.submit_automatic_text(uuid,text,bytea,text,text,text,text,text,integer,uuid)
  to gather_ingestion_coordinator;
grant execute on function gather_private.next_automatic_text_job(),gather_private.claim_automatic_text_job(uuid)
  to gather_ingestion_worker;
grant execute on function public.request_automatic_processing(uuid) to authenticated;
commit;
