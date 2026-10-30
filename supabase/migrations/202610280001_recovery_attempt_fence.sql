-- Bind explicit recovery to the displayed job and attempt. A late duplicate
-- request must not authorize a later retry or process a replacement version.
begin;
drop function public.request_automatic_processing(uuid);
create function public.request_automatic_processing(p_source uuid,p_job uuid,p_attempts integer) returns boolean
language plpgsql security definer set search_path='' as $$
declare v_owner uuid:=auth.uid(); j gather_private.ingestion_jobs%rowtype;
begin
  if v_owner is null then raise exception 'authentication_required' using errcode='42501'; end if;
  if p_source is null or p_job is null or p_attempts is null or p_attempts not between 0 and 2 then return false; end if;
  perform 1 from public.sources s where s.id=p_source and s.owner_id=v_owner and s.deleted_at is null for update;
  if not found then return false; end if;
  select jobs.* into j from gather_private.ingestion_jobs jobs
    join gather_private.ingestion_targets t on t.version_id=jobs.version_id
    join gather_private.automatic_text_jobs a on a.job_id=jobs.id
    where t.source_id=p_source and jobs.id=p_job for update of jobs;
  if not found or j.attempts<>p_attempts or not ((j.state='queued' and j.next_attempt_at<=clock_timestamp())
    or (j.state='processing' and j.lease_expires_at<=clock_timestamp())) then return false; end if;
  update gather_private.automatic_text_jobs set requested_attempt=j.attempts+1 where job_id=j.id;
  return true;
end $$;
revoke all on function public.request_automatic_processing(uuid,uuid,integer)
  from public,anon,authenticated,gather_ingestion_worker,gather_ingestion_coordinator;
grant execute on function public.request_automatic_processing(uuid,uuid,integer) to authenticated;
commit;
