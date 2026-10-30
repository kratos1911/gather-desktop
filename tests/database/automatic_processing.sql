-- Synthetic SQL fixtures; no real Auth session, inference or hosted data.
begin;
create function pg_temp.check_it(ok boolean,label text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',label; end if; raise notice 'PASS: %',label; end $$;
insert into auth.users values('00000000-0000-0000-0000-000000000001'),('00000000-0000-0000-0000-000000000002');
insert into gather_private.source_quotas values('00000000-0000-0000-0000-000000000001',4,0),('00000000-0000-0000-0000-000000000002',2,0);
set local role gather_ingestion_coordinator;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select gather_private.submit_text('11111111-1111-1111-1111-111111111111','Old',convert_to('Old note','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256) as item \gset old_
select gather_private.submit_automatic_text('11111111-1111-1111-1111-111111111111','Old',convert_to('Old note','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256) as item \gset replay_
select pg_temp.check_it(not (:'replay_item'::jsonb->>'automatic_processing')::boolean,'retrying an older manual import does not enroll it');
select gather_private.submit_automatic_text('22222222-2222-2222-2222-222222222222','New',convert_to('New note','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256) as item \gset new_
select pg_temp.check_it(gather_private.submit_automatic_text('22222222-2222-2222-2222-222222222222','New',convert_to('New note','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256)=:'new_item'::jsonb,'duplicate import returns the same automatic job');
reset role;
select pg_temp.check_it((select count(*)=1 from gather_private.automatic_text_jobs),'one durable intent and no legacy sweep');
select pg_temp.check_it((select relrowsecurity from pg_class where oid='gather_private.automatic_text_jobs'::regclass)
  and not exists(select 1 from pg_policy where polrelid='gather_private.automatic_text_jobs'::regclass),'RLS enabled with no client policies');
select pg_temp.check_it(not has_table_privilege('authenticated','gather_private.automatic_text_jobs','SELECT')
  and not has_table_privilege('gather_ingestion_worker','gather_private.automatic_text_jobs','UPDATE'),'intent table is private');
select pg_temp.check_it(not has_function_privilege('authenticated','gather_private.claim_automatic_text_job(uuid)','execute')
  and not has_function_privilege('gather_ingestion_coordinator','gather_private.next_automatic_text_job()','execute')
  and not has_function_privilege('gather_ingestion_worker','gather_private.submit_automatic_text(uuid,text,bytea,text,text,text,text,text,integer,uuid)','execute'),'role separation');
set local role gather_ingestion_worker;
select pg_temp.check_it(gather_private.next_automatic_text_job()=(:'new_item'::jsonb->>'job_id')::uuid,'durable new job recoverable after reconnect');
select gather_private.claim_automatic_text_job((:'new_item'::jsonb->>'job_id')::uuid) as value \gset claim_
select pg_temp.check_it(gather_private.claim_automatic_text_job((:'new_item'::jsonb->>'job_id')::uuid) is null,'second claim cannot consume another attempt');
select gather_private.fail_text_job((:'claim_value'::jsonb->>'id')::uuid,(:'claim_value'::jsonb->>'lease_token')::uuid,'timeout');
reset role;
update gather_private.ingestion_jobs set next_attempt_at=clock_timestamp()-interval '1 second' where id=(:'new_item'::jsonb->>'job_id')::uuid;
set local role gather_ingestion_worker;
select pg_temp.check_it(gather_private.next_automatic_text_job() is null,'no automatic retry after failed inference');
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
select pg_temp.check_it(not public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,1),'another user cannot trigger recovery');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select pg_temp.check_it(not public.request_automatic_processing((:'old_item'::jsonb->>'source_id')::uuid,(:'old_item'::jsonb->>'job_id')::uuid,0),'old manual source cannot enter automatic recovery');
select pg_temp.check_it(not public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'old_item'::jsonb->>'job_id')::uuid,1),'wrong displayed job cannot recover a replacement');
select pg_temp.check_it(public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,1),'owner can explicitly authorize one retry');
select pg_temp.check_it(public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,1),'retrying the recovery request is idempotent');
set local role gather_ingestion_worker;
select gather_private.claim_automatic_text_job((:'new_item'::jsonb->>'job_id')::uuid) as value \gset second_
select pg_temp.check_it((:'second_value'::jsonb->>'attempts')::integer=2,'only one additional attempt authorized');
reset role;
update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',lease_expires_at=clock_timestamp()-interval '1 minute'
  where id=(:'new_item'::jsonb->>'job_id')::uuid;
set local role gather_ingestion_worker;
select pg_temp.check_it(gather_private.next_automatic_text_job() is null,'expired interrupted attempt requires explicit recovery');
set local role authenticated;
select pg_temp.check_it(not public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,1),'late duplicate recovery cannot authorize a later attempt');
select pg_temp.check_it(public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,2),'owner authorizes recovery after lease expiry');
set local role gather_ingestion_worker;
select gather_private.claim_automatic_text_job((:'new_item'::jsonb->>'job_id')::uuid) as value \gset third_
select pg_temp.check_it((:'third_value'::jsonb->>'attempts')::integer=3,'three-attempt ceiling retained');
select gather_private.fail_text_job((:'third_value'::jsonb->>'id')::uuid,(:'third_value'::jsonb->>'lease_token')::uuid,'timeout');
set local role authenticated;
select pg_temp.check_it(not public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,3),'exhausted job cannot be reset');
select public.request_source_deletion((:'new_item'::jsonb->>'source_id')::uuid);
select pg_temp.check_it(not public.request_automatic_processing((:'new_item'::jsonb->>'source_id')::uuid,(:'new_item'::jsonb->>'job_id')::uuid,2),'deleted source cannot be restarted');
reset role;
select pg_temp.check_it((select attempts=0 from gather_private.ingestion_jobs where id=(:'old_item'::jsonb->>'job_id')::uuid),'older job attempt count untouched');
select gather_private.finish_source_cleanup((:'new_item'::jsonb->>'source_id')::uuid);
select pg_temp.check_it((select count(*)=0 from gather_private.automatic_text_jobs),'cleanup removes intent through existing cascade');
rollback;
