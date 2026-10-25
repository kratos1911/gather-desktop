-- Operator jobs must not consume another queued job's retry budget.
-- Shared implementation preserves the existing global lease/locking semantics.
begin;
create function gather_private.claim_text_job_internal(p_job uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare v_source uuid; v_job gather_private.ingestion_jobs%rowtype; v_now timestamptz;
begin
  if not pg_try_advisory_xact_lock(714011,1) then return null; end if;
  v_now:=clock_timestamp();
  if exists(select 1 from gather_private.ingestion_jobs where state='processing' and lease_expires_at>v_now) then return null; end if;
  select s.id into v_source from public.sources s
    join gather_private.ingestion_targets t on t.source_id=s.id
    join gather_private.ingestion_jobs j on j.version_id=t.version_id
    where s.deleted_at is null and (p_job is null or j.id=p_job)
      and ((j.state='queued' and j.next_attempt_at<=v_now)
        or (j.state='processing' and j.lease_expires_at<=v_now))
    order by j.next_attempt_at,j.created_at,j.id limit 1 for update of s skip locked;
  if not found then return null; end if;
  select j.* into v_job from gather_private.ingestion_jobs j
    join gather_private.ingestion_targets t on t.version_id=j.version_id
    where t.source_id=v_source and (p_job is null or j.id=p_job) for update of j;
  v_now:=clock_timestamp();
  if v_job.id is null or not ((v_job.state='queued' and v_job.next_attempt_at<=v_now)
    or (v_job.state='processing' and v_job.lease_expires_at<=v_now)) then return null; end if;
  if v_job.attempts>=3 then
    update gather_private.ingestion_jobs set state='failed',error_code='lease_expired',
      lease_token=null,lease_started_at=null,lease_expires_at=null where id=v_job.id;
    return null;
  end if;
  update gather_private.ingestion_jobs set state='processing',attempts=attempts+1,
    lease_token=gen_random_uuid(),lease_started_at=v_now,lease_expires_at=v_now+interval '60 seconds',
    error_code=case when state='processing' then 'lease_expired' else error_code end
    where id=v_job.id returning * into v_job;
  return (to_jsonb(v_job)-'fingerprint') || (select jsonb_build_object(
    'content_sha256',content_sha256,'parser_version',parser_version)
    from public.source_versions where id=v_job.version_id);
end $$;

create or replace function gather_private.claim_text_job() returns jsonb
language sql security definer set search_path='' as $$
  select gather_private.claim_text_job_internal(null::uuid);
$$;

create function gather_private.claim_target_text_job(p_job uuid) returns jsonb
language sql security definer set search_path='' as $$
  select case when p_job is null then null::jsonb
    else gather_private.claim_text_job_internal(p_job) end;
$$;

revoke all on function gather_private.claim_text_job_internal(uuid),
  gather_private.claim_target_text_job(uuid)
  from public, anon, authenticated, gather_ingestion_coordinator, gather_ingestion_worker;
grant execute on function gather_private.claim_target_text_job(uuid) to gather_ingestion_worker;
commit;
