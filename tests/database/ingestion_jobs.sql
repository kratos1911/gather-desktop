-- Synthetic scheduler evidence. Admin clock edits simulate expiry, not production APIs.
insert into auth.users values ('00000000-0000-0000-0000-000000000005'),('00000000-0000-0000-0000-000000000006');
insert into gather_private.source_quotas values ('00000000-0000-0000-0000-000000000005',4,0),('00000000-0000-0000-0000-000000000006',4,0);
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000005',false);
select public.save_source(gen_random_uuid(),'file','Scheduler fixture') as src \gset
reset role;
create function pg_temp.enqueue_fixture(src uuid,req uuid,hash text default repeat('a',64)) returns uuid
language sql as $$ select gather_private.enqueue_text_job('00000000-0000-0000-0000-000000000005',src,req,hash,'text-v1',32,'text/plain','token512-v1','synthetic-model','fixture-revision',512) $$;
select gen_random_uuid() as req \gset
select pg_temp.enqueue_fixture(:'src',:'req') as job \gset
select pg_temp.assert_true(pg_temp.enqueue_fixture(:'src',:'req')=:'job','job retry returns identical identity');
select pg_temp.assert_true((select count(*)=1 from public.source_versions where source_id=:'src'),'job retry creates one version');
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,%L,repeat(''b'',64))',:'src',:'req'),'22023','job key conflict rejected');
select pg_temp.expect_error(format('select gather_private.enqueue_text_job(%L,%L,gen_random_uuid(),repeat(''a'',64),''v'',65537,''text/plain'',''c'',''m'',''r'',512)','00000000-0000-0000-0000-000000000005',:'src'),'22023','job preserves 64 KiB input limit');
select pg_temp.expect_error(format('select gather_private.enqueue_text_job(%L,%L,gen_random_uuid(),repeat(''a'',64),''v'',32,''text/plain'',''c'',''m'',''r'',512)','00000000-0000-0000-0000-000000000006',:'src'),'23503','coordinator rejects mismatched source ownership');
select pg_temp.expect_error(format('update public.source_versions set parser_version=''changed'' where source_id=%L',:'src'),'23514','job-bound version provenance immutable');
select pg_temp.expect_error(format('update gather_private.ingestion_jobs set state=''ready'' where id=%L',:'job'),'23514','no premature ready state exists');
set role authenticated;
select pg_temp.assert_true((select state='queued' and attempts=0 from public.source_processing_status(:'src')),'owner sees queued status');
select pg_temp.expect_error('select * from gather_private.ingestion_jobs','42501','client cannot read lease secrets');
select pg_temp.expect_error('select gather_private.claim_text_job()','42501','client cannot claim jobs');
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,%L)',:'src',:'req'),'42501','client cannot enqueue or forge processing provenance');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000006',false);
select pg_temp.assert_true((select count(*)=0 from public.source_processing_status(:'src')),'other owner cannot read status');
select pg_temp.assert_true(not public.request_source_deletion(:'src'),'other owner cannot cancel source');
select set_config('request.jwt.claim.sub','',false);
select pg_temp.assert_true((select count(*)=0 from public.source_processing_status(:'src')),'missing identity cannot read status');
set role anon;
select pg_temp.expect_error(format('select * from public.source_processing_status(%L)',:'src'),'42501','anonymous status denied');
set role gather_ingestion_worker;
select pg_temp.expect_error('select * from gather_private.ingestion_jobs','42501','worker has no direct table read');
select pg_temp.expect_error('update gather_private.ingestion_jobs set attempts=0','42501','worker cannot reset attempts');
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,%L)',:'src',:'req'),'42501','worker cannot create jobs');
select gather_private.claim_text_job() as claimed \gset
select pg_temp.assert_true((:'claimed'::jsonb->>'id')::uuid=:'job','worker claims the queued job');
select pg_temp.assert_true(:'claimed'::jsonb->>'content_sha256'=repeat('a',64) and :'claimed'::jsonb->>'dimensions'='512','claim preserves hash and embedding configuration');
select pg_temp.assert_true(gather_private.claim_text_job() is null,'global single-flight lease enforced');
select pg_temp.expect_error(format('select gather_private.renew_text_job(%L,gen_random_uuid())',:'job'),'55000','wrong lease token rejected');
select pg_temp.assert_true(gather_private.renew_text_job(:'job',(:'claimed'::jsonb->>'lease_token')::uuid)>clock_timestamp(),'live lease heartbeat succeeds');
select pg_temp.expect_error(format('select gather_private.fail_text_job(%L,%L,''raw private content'')',:'job',:'claimed'::jsonb->>'lease_token'),'22023','arbitrary error text rejected');
reset role;
update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',lease_expires_at=clock_timestamp()-interval '1 second' where id=:'job';
set role gather_ingestion_worker;
select pg_temp.expect_error(format('select gather_private.renew_text_job(%L,%L)',:'job',:'claimed'::jsonb->>'lease_token'),'55000','expired token cannot revive itself');
select gather_private.claim_text_job() as recovered \gset
select pg_temp.assert_true(:'recovered'::jsonb->>'attempts'='2' and :'recovered'::jsonb->>'lease_token'<>:'claimed'::jsonb->>'lease_token','expired work recovered with new fenced token');
select pg_temp.expect_error(format('select gather_private.fail_text_job(%L,%L,''timeout'')',:'job',:'claimed'::jsonb->>'lease_token'),'55000','stale worker cannot overwrite recovered state');
select pg_temp.assert_true(gather_private.fail_text_job(:'job',(:'recovered'::jsonb->>'lease_token')::uuid,'timeout')='queued','transient failure queues bounded retry');
select pg_temp.assert_true(gather_private.claim_text_job() is null,'retry backoff is respected');
reset role;
select pg_temp.assert_true((select next_attempt_at>clock_timestamp() and error_code='timeout' from gather_private.ingestion_jobs where id=:'job'),'failure remains visible with delayed retry');
update gather_private.ingestion_jobs set next_attempt_at=clock_timestamp()-interval '1 second' where id=:'job';
set role gather_ingestion_worker;
select gather_private.claim_text_job() as third \gset
select pg_temp.assert_true(gather_private.fail_text_job(:'job',(:'third'::jsonb->>'lease_token')::uuid,'timeout')='failed','third transient attempt is terminal');
select pg_temp.assert_true(gather_private.claim_text_job() is null,'failed jobs never retry automatically');
reset role;
select pg_temp.assert_true(pg_temp.enqueue_fixture(:'src',:'req')=:'job','same request cannot reset failed attempt budget');
select pg_temp.enqueue_fixture(:'src',gen_random_uuid(),repeat('b',64)) as replacement \gset
set role gather_ingestion_worker;
select gather_private.claim_text_job() as replace_claim \gset
reset role;
select pg_temp.enqueue_fixture(:'src',gen_random_uuid(),repeat('c',64)) as newest \gset
select pg_temp.assert_true((select state='cancelled' and lease_token is null and error_code='superseded' from gather_private.ingestion_jobs where id=:'replacement'),'replacement cancels old lease atomically');
set role gather_ingestion_worker;
select pg_temp.expect_error(format('select gather_private.renew_text_job(%L,%L)',:'replacement',:'replace_claim'::jsonb->>'lease_token'),'55000','superseded worker cannot heartbeat');
select gather_private.claim_text_job() as newest_claim \gset
select pg_temp.assert_true(gather_private.fail_text_job(:'newest',(:'newest_claim'::jsonb->>'lease_token')::uuid,'invalid_input')='failed','validation failure does not retry');
reset role;
select pg_temp.enqueue_fixture(:'src',gen_random_uuid(),repeat('d',64)) as deleted_job \gset
set role gather_ingestion_worker;
select gather_private.claim_text_job() as delete_claim \gset
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000005',false);
select public.request_source_deletion(:'src');
select pg_temp.assert_true((select count(*)=0 from public.source_processing_status(:'src')),'deletion immediately hides processing status');
set role gather_ingestion_worker;
select pg_temp.expect_error(format('select gather_private.fail_text_job(%L,%L,''timeout'')',:'deleted_job',:'delete_claim'::jsonb->>'lease_token'),'55000','deleted source rejects late worker failure');
select pg_temp.assert_true(gather_private.claim_text_job() is null,'deleted source cannot be claimed');
reset role;
select pg_temp.assert_true((select bool_and(state='cancelled' and lease_token is null) from gather_private.ingestion_jobs where source_id=:'src'),'deletion cancels every job');
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,%L)',:'src',:'req'),'23503','late enqueue does not resurrect tombstoned source');
select pg_temp.assert_true(gather_private.finish_source_cleanup(:'src'),'existing cleanup accepts scheduling derivatives');
select pg_temp.assert_true(not exists(select 1 from gather_private.ingestion_jobs where source_id=:'src') and not exists(select 1 from gather_private.ingestion_targets where source_id=:'src'),'cleanup cascades jobs and targets');
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,%L)',:'src',:'req'),'23503','late enqueue after physical cleanup fails closed');

-- Exhausted crash attempts, heartbeat ceiling, transactional rollback and metadata cap.
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000005',false);
select public.save_source(gen_random_uuid(),'file','Bounds fixture') as bounds_src \gset
reset role;
select gen_random_uuid() as bounds_req \gset
begin;
select pg_temp.enqueue_fixture(:'bounds_src',:'bounds_req');
rollback;
select pg_temp.assert_true(not exists(select 1 from public.source_versions where source_id=:'bounds_src'),'interrupted enqueue rolls back version and job');
select pg_temp.enqueue_fixture(:'bounds_src',:'bounds_req') as bounds_job \gset
select gather_private.claim_text_job() as bounds_claim \gset
update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '4 minutes 50 seconds',lease_expires_at=clock_timestamp()+interval '9 seconds' where id=:'bounds_job';
select gather_private.renew_text_job(:'bounds_job',(:'bounds_claim'::jsonb->>'lease_token')::uuid);
select pg_temp.assert_true((select lease_expires_at<=lease_started_at+interval '5 minutes' from gather_private.ingestion_jobs where id=:'bounds_job'),'heartbeat cannot extend attempt beyond five minutes');
update gather_private.ingestion_jobs set attempts=3,lease_started_at=clock_timestamp()-interval '2 minutes',lease_expires_at=clock_timestamp()-interval '1 second' where id=:'bounds_job';
select pg_temp.assert_true(gather_private.claim_text_job() is null,'exhausted crashed job is retired without fourth claim');
select pg_temp.assert_true((select state='failed' and error_code='lease_expired' and attempts=3 from gather_private.ingestion_jobs where id=:'bounds_job'),'exhausted lease failure remains visible');
select pg_temp.enqueue_fixture(:'bounds_src',gen_random_uuid()) from generate_series(1,15);
select pg_temp.expect_error(format('select pg_temp.enqueue_fixture(%L,gen_random_uuid())',:'bounds_src'),'P0001','retained job/version metadata is bounded');
select pg_temp.assert_true(pg_temp.enqueue_fixture(:'bounds_src',:'bounds_req')=:'bounds_job','idempotent replay remains valid at version cap');
select pg_temp.assert_true((select count(*)=16 from public.source_versions where source_id=:'bounds_src'),'over-limit enqueue creates no extra version');
set role authenticated;
select public.request_source_deletion(:'bounds_src');
reset role;
select gather_private.finish_source_cleanup(:'bounds_src');
