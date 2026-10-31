-- Synthetic roles/jobs only; no real Auth, files or vectors.
begin;
create function pg_temp.check_it(ok boolean,label text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',label; end if; raise notice 'PASS: %',label; end $$;
insert into auth.users values('00000000-0000-0000-0000-000000000101'),('00000000-0000-0000-0000-000000000102');
insert into gather_private.source_quotas values('00000000-0000-0000-0000-000000000101',2,0);
set local role gather_ingestion_coordinator;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000101',true);
select gather_private.submit_automatic_text('11111111-1111-1111-1111-111111111111','Fixture',convert_to('Fixture','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256) as item \gset f_
reset role;
set local role authenticated;
select pg_temp.check_it((select can_resume from public.list_library_sources_with_recovery()),'queued owned job is eligible');
set local role gather_ingestion_worker;
select gather_private.claim_automatic_text_job((:'f_item'::jsonb->>'job_id')::uuid) as lease \gset f_
set local role authenticated;
select pg_temp.check_it(not (select can_resume from public.source_processing_status_with_recovery((:'f_item'::jsonb->>'source_id')::uuid))
  and not public.request_automatic_processing((:'f_item'::jsonb->>'source_id')::uuid,(:'f_item'::jsonb->>'job_id')::uuid,1),
  'live lease disables resume and cannot start another attempt');
reset role;
update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',
  lease_expires_at=clock_timestamp()-interval '1 second' where id=(:'f_item'::jsonb->>'job_id')::uuid;
set local role authenticated;
select pg_temp.check_it((select can_resume from public.source_processing_status_with_recovery((:'f_item'::jsonb->>'source_id')::uuid)),
  'expired lease becomes eligible without changing attempts');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000102',true);
select pg_temp.check_it(not exists(select 1 from public.list_library_sources_with_recovery())
  and not exists(select 1 from public.source_processing_status_with_recovery((:'f_item'::jsonb->>'source_id')::uuid)),
  'another owner cannot inspect eligibility or status');
reset role;
update gather_private.ingestion_jobs set state='queued',lease_token=null,lease_started_at=null,lease_expires_at=null,
  next_attempt_at=clock_timestamp()+interval '1 hour' where id=(:'f_item'::jsonb->>'job_id')::uuid;
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000101',true);
select pg_temp.check_it(not (select can_resume from public.list_library_sources_with_recovery()),'retry backoff is not shown as resumable');
reset role;
update gather_private.ingestion_jobs set next_attempt_at=clock_timestamp()-interval '1 second',attempts=3
  where id=(:'f_item'::jsonb->>'job_id')::uuid;
set local role authenticated;
select pg_temp.check_it(not (select can_resume from public.list_library_sources_with_recovery()),'attempt limit stays enforced');
select public.request_source_deletion((:'f_item'::jsonb->>'source_id')::uuid);
select pg_temp.check_it(not exists(select 1 from public.list_library_sources_with_recovery())
  and not exists(select 1 from public.source_processing_status_with_recovery((:'f_item'::jsonb->>'source_id')::uuid)),
  'deleted source has no recovery metadata');
reset role;
select pg_temp.check_it(not has_function_privilege('anon','public.list_library_sources_with_recovery(integer,timestamptz,uuid)','execute')
  and not has_function_privilege('authenticated','gather_private.can_resume_text_job(uuid)','execute'),
  'no anonymous or direct private helper access');
rollback;
