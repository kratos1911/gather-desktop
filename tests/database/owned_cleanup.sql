begin;
create function pg_temp.check_it(ok boolean,label text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',label; end if; raise notice 'PASS: %',label; end $$;
insert into auth.users values('00000000-0000-0000-0000-000000000001'),('00000000-0000-0000-0000-000000000002');
insert into gather_private.source_quotas values('00000000-0000-0000-0000-000000000001',2,0),('00000000-0000-0000-0000-000000000002',2,0);
set local role gather_ingestion_coordinator;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select gather_private.submit_automatic_text('11111111-1111-1111-1111-111111111111','Cleanup fixture',convert_to('Synthetic','UTF8'),
  'text/plain','utf8-plain-v1','fixture','synthetic','v1',256) as item \gset saved_
set local role authenticated;
select pg_temp.check_it(not public.complete_source_cleanup((:'saved_item'::jsonb->>'source_id')::uuid),'active source cannot be physically removed');
select public.request_source_deletion((:'saved_item'::jsonb->>'source_id')::uuid);
select pg_temp.check_it((select count(*)=1 from public.list_source_cleanup()),'pending cleanup survives reconnect');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
select pg_temp.check_it((select count(*)=0 from public.list_source_cleanup()),'another owner cannot list cleanup');
select pg_temp.check_it(not public.complete_source_cleanup((:'saved_item'::jsonb->>'source_id')::uuid),'another owner cannot complete cleanup');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select pg_temp.check_it(public.complete_source_cleanup((:'saved_item'::jsonb->>'source_id')::uuid),'owned cleanup completes');
select pg_temp.check_it(public.complete_source_cleanup((:'saved_item'::jsonb->>'source_id')::uuid),'lost acknowledgement can be retried safely');
select pg_temp.check_it((select count(*)=0 from public.list_source_cleanup()),'confirmed cleanup disappears from pending list');
reset role;
select pg_temp.check_it(not exists(select 1 from public.sources where id=(:'saved_item'::jsonb->>'source_id')::uuid)
  and not exists(select 1 from public.source_versions where id=(:'saved_item'::jsonb->>'version_id')::uuid)
  and not exists(select 1 from gather_private.job_originals where version_id=(:'saved_item'::jsonb->>'version_id')::uuid)
  and not exists(select 1 from gather_private.ingestion_jobs where id=(:'saved_item'::jsonb->>'job_id')::uuid)
  and not exists(select 1 from gather_private.automatic_text_jobs where job_id=(:'saved_item'::jsonb->>'job_id')::uuid),'original, version, job and intent are removed');
select pg_temp.check_it((select used=0 from gather_private.source_quotas where owner_id='00000000-0000-0000-0000-000000000001')
  and exists(select 1 from gather_private.save_receipts where source_id=(:'saved_item'::jsonb->>'source_id')::uuid),'quota released once and replay guard retained');
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
select pg_temp.check_it(not public.complete_source_cleanup((:'saved_item'::jsonb->>'source_id')::uuid),'completed foreign source indistinguishable from unknown');
reset role;
select pg_temp.check_it(not has_function_privilege('anon','public.complete_source_cleanup(uuid)','execute')
  and not has_function_privilege('gather_ingestion_worker','public.complete_source_cleanup(uuid)','execute')
  and not has_function_privilege('authenticated','gather_private.finish_source_cleanup(uuid)','execute'),'no private finalizer or anonymous access granted');
rollback;
