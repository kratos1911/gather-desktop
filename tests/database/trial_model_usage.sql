-- Disposable PostgreSQL fixture. Model calls are never made by this check.
begin;
create function pg_temp.assert_true(ok boolean, label text) returns void language plpgsql as $$
begin
  if ok is distinct from true then raise exception 'FAIL: %', label; end if;
  raise notice 'PASS: %', label;
end $$;

insert into auth.users values ('00000000-0000-0000-0000-000000000801'),
  ('00000000-0000-0000-0000-000000000802');
select pg_temp.assert_true(
  not has_function_privilege('authenticated','gather_private.trial_query_usage(boolean)','execute')
  and not has_function_privilege('anon','gather_private.trial_query_usage(boolean)','execute')
  and not has_function_privilege('gather_ingestion_worker','gather_private.trial_query_usage(boolean)','execute')
  and not has_function_privilege('gather_ingestion_coordinator','gather_private.charge_trial_document(uuid,uuid)','execute')
  and not has_function_privilege('gather_ingestion_worker','gather_private.trial_model_usage(uuid,boolean)','execute')
  and not has_table_privilege('gather_ingestion_coordinator','gather_private.trial_model_policy','update'),
  'only restricted roles can use their specific reservation path');

select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000801',true);
set local role gather_ingestion_coordinator;
select pg_temp.assert_true(gather_private.trial_query_usage(true) is null,'unconfigured mode fails closed');
reset role;
insert into gather_private.trial_model_policy (daily_account_limit,monthly_service_limit) values (2,3);
insert into gather_private.source_quotas values ('00000000-0000-0000-0000-000000000801',2,0);
select public.save_source(gen_random_uuid(),'file','Disposable trial note') as source \gset
select gather_private.enqueue_text_job('00000000-0000-0000-0000-000000000801',:'source',gen_random_uuid(),
  encode(sha256(convert_to('fixture','UTF8')),'hex'),'utf8-plain-v1',7,'text/plain','fixture','synthetic','v1',256) as job \gset
select j->>'lease_token' as lease from (select gather_private.claim_target_text_job(:'job') j) q \gset

set local role gather_ingestion_coordinator;
select pg_temp.assert_true(gather_private.trial_query_usage(false)->>'used'='0','read does not charge');
select pg_temp.assert_true(gather_private.trial_query_usage(true)->>'used'='1','first query consumes one unit');
set local role gather_ingestion_worker;
select pg_temp.assert_true(gather_private.charge_trial_document(:'job',:'lease')->>'used'='2',
  'document reservation uses the job owner and shares the account quota');
reset role;

-- Move the fixture lease into the past. A failed reservation must roll back.
update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '62 seconds',
  lease_expires_at=clock_timestamp()-interval '1 second' where id=:'job';
select set_config('gather.test_job',:'job',true),set_config('gather.test_lease',:'lease',true);
set local role gather_ingestion_worker;
do $$ begin
  perform gather_private.charge_trial_document(current_setting('gather.test_job')::uuid,
    current_setting('gather.test_lease')::uuid);
  raise exception 'expired lease was accepted';
exception when sqlstate '55000' then raise notice 'PASS: expired worker lease cannot reserve'; end $$;
set local role gather_ingestion_coordinator;
select pg_temp.assert_true(gather_private.trial_query_usage(true)->>'state'='trial_quota_exhausted',
  'the daily account cap is enforced');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000802',true);
select pg_temp.assert_true(gather_private.trial_query_usage(false)->>'used'='0','second account starts with its own quota');
select pg_temp.assert_true(gather_private.trial_query_usage(true)->>'used'='1','second account can reserve past first account limit');
select pg_temp.assert_true(gather_private.trial_query_usage(true)->>'state'='trial_capacity_exhausted',
  'the service cap applies across accounts');
reset role;
select pg_temp.assert_true((select used=3 from gather_private.trial_model_policy),'denied attempts leave usage unchanged');
update gather_private.trial_model_accounts set usage_date=usage_date-1;
update gather_private.trial_model_policy set usage_month=(usage_month-interval '1 month')::date;
set local role gather_ingestion_coordinator;
select pg_temp.assert_true(gather_private.trial_query_usage(true)->>'used'='1','UTC day and month counters reset independently of the process');
reset role;

-- Leave one monthly slot available for simultaneous reservations from fresh sessions.
update gather_private.trial_model_policy set used=2, monthly_service_limit=3;
commit;
