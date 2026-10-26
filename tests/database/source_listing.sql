-- Synthetic sources, vectors and Auth claim shim. No real JWTs or hosted data.
begin;
create or replace function pg_temp.assert_true(ok boolean,label text) returns void
language plpgsql as $$ begin
  if ok is distinct from true then raise exception 'FAIL: %',label; end if;
  raise notice 'PASS: %',label;
end $$;
create or replace function pg_temp.expect_error(statement text,expected text,label text) returns void
language plpgsql security invoker as $$ begin
  begin execute statement;
  exception when others then
    if sqlstate=expected then raise notice 'PASS: %',label; return; end if;
    raise;
  end;
  raise exception 'FAIL: expected denial: %',label;
end $$;
insert into auth.users values('00000000-0000-0000-0000-000000000001'),('00000000-0000-0000-0000-000000000002');
insert into gather_private.source_quotas values('00000000-0000-0000-0000-000000000001',20,4),('00000000-0000-0000-0000-000000000002',20,2);
insert into public.sources(id,owner_id,kind,title,created_at)
select ('10000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,
  '00000000-0000-0000-0000-000000000001','file','A '||n,'2026-10-26T01:00:00.000001Z' from generate_series(1,4) n;
insert into public.sources(id,owner_id,kind,title,created_at)
select ('20000000-0000-0000-0000-'||lpad(n::text,12,'0'))::uuid,
  '00000000-0000-0000-0000-000000000002','file','B '||n,'2026-10-26T01:00:00.000001Z' from generate_series(1,2) n;
update public.sources set deleted_at=now() where title='A 4';
select gather_private.enqueue_text_job('00000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000003',
  gen_random_uuid(),encode(sha256(convert_to('Synthetic note','UTF8')),'hex'),'utf8-plain-v1',14,'text/plain','fixture','synthetic','v1',256) as id \gset pub_
select j->>'lease_token' as token,j->>'version_id' as version from (select gather_private.claim_target_text_job(:'pub_id') j) q \gset pub_
select gather_private.stage_text(:'pub_id',:'pub_token',convert_to('Synthetic note','UTF8'),'text/plain',
  jsonb_build_array(jsonb_build_object('id',repeat('a',64),'start',0,'end',14)));
select gather_private.stage_vectors(:'pub_id',:'pub_token','synthetic','v1',256,
  jsonb_build_array(jsonb_build_object('id',repeat('a',64),'vector',to_jsonb(array[1]||array_fill(0,array[255])))));
select gather_private.publish_text(:'pub_id',:'pub_token');
select gather_private.enqueue_text_job('00000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000002',
  gen_random_uuid(),repeat('b',64),'utf8-plain-v1',14,'text/plain','fixture','synthetic','v1',256) as id \gset queued_
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select pg_temp.assert_true((select count(*)=3 and bool_and(title like 'A %') from public.list_library_sources()),'list is owner-scoped and tombstones hidden');
select pg_temp.assert_true((select array_agg(title)=array['A 3','A 2'] from public.list_library_sources(1)),'unique ID breaks timestamp ties; bounded lookahead');
select pg_temp.assert_true((select array_agg(title)=array['A 1'] from public.list_library_sources(1,'2026-10-26T01:00:00.000001Z','10000000-0000-0000-0000-000000000002')),'next page strictly excludes cursor and earlier items');
select pg_temp.assert_true((select count(*)=0 from public.list_library_sources(1,'2026-10-26T01:00:00.000001Z','10000000-0000-0000-0000-000000000001')),'last page is empty');
select pg_temp.assert_true((select count(*)=3 and bool_and(title like 'A %') from public.list_library_sources(20,'2026-10-26T01:00:00.000001Z','20000000-0000-0000-0000-000000000002')),'foreign valid cursor cannot grant foreign rows');
select pg_temp.assert_true((select state='ready' and published_version_id=processing_version_id and created_at='2026-10-26T01:00:00.000001Z' from public.list_library_sources() where title='A 3'),'ready and microsecond cursor identity preserved');
select pg_temp.assert_true((select state='queued' and published_version_id is null from public.list_library_sources() where title='A 2'),'unpublished queued version is metadata only');
select pg_temp.assert_true((select state is null and job_id is null from public.list_library_sources() where title='A 1'),'missing processing is not invented as ready');
select pg_temp.assert_true((select count(*)=0 from public.open_published_text('10000000-0000-0000-0000-000000000002',:'pub_version')),'unpublished text cannot open');
select pg_temp.assert_true(not public.request_source_deletion('20000000-0000-0000-0000-000000000001'),'foreign deletion denied');
select pg_temp.expect_error('select * from public.list_library_sources(21)','22023','oversized page denied');
select pg_temp.expect_error('select * from public.list_library_sources(0)','22023','zero page denied');
select pg_temp.expect_error('select * from public.list_library_sources(null)','22023','null page denied');
select pg_temp.expect_error($q$select * from public.list_library_sources(1,null,'10000000-0000-0000-0000-000000000001')$q$,'22023','half cursor denied');
select pg_temp.expect_error($q$select * from public.list_library_sources(1,'infinity','10000000-0000-0000-0000-000000000001')$q$,'22023','nonfinite timestamp denied');
select pg_temp.assert_true((select bool_and(not (to_jsonb(r) ?| array['owner_id','original','body','embedding','lease_token','notes'])) from public.list_library_sources() r),'listing has no originals, private staging or capabilities');
select pg_temp.expect_error('select * from gather_private.staged_passages','42501','client staging access remains denied');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
select pg_temp.assert_true((select count(*)=2 and bool_and(title like 'B %') from public.list_library_sources()),'B independently sees only B');
select pg_temp.assert_true((select count(*)=0 from public.open_published_text('10000000-0000-0000-0000-000000000003',:'pub_version')),'B cannot open listed A version');
select set_config('request.jwt.claim.sub','',true);
select pg_temp.expect_error('select * from public.list_library_sources()','42501','missing identity fails closed');
set role anon;
select pg_temp.expect_error('select * from public.list_library_sources()','42501','anonymous execution denied');
reset role;
select pg_temp.assert_true(not has_function_privilege('gather_ingestion_worker','public.list_library_sources(integer,timestamptz,uuid)','execute'),'worker is not a client reader');
select j->>'lease_token' as token from (select gather_private.claim_target_text_job(:'queued_id') j) q \gset queued_
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select pg_temp.assert_true((select state='processing' from public.list_library_sources() where title='A 2'),'processing state is truthful');
reset role;
select gather_private.fail_text_job(:'queued_id',:'queued_token','invalid_input');
select gather_private.enqueue_text_job('00000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000003',
  gen_random_uuid(),repeat('c',64),'utf8-plain-v1',14,'text/plain','fixture','synthetic','v1',256) as id \gset replace_
set role authenticated;
select pg_temp.assert_true((select state='failed' and error_code='invalid_input' from public.list_library_sources() where title='A 2'),'failed processing stays visible');
select pg_temp.assert_true((select state='queued' and published_version_id=:'pub_version'::uuid and published_version_id<>processing_version_id from public.list_library_sources() where title='A 3'),'replacement target is separate from prior publication');
select pg_temp.assert_true((select count(*)=1 from public.open_published_text('10000000-0000-0000-0000-000000000003',:'pub_version')),'old published text opens during replacement');
select public.request_source_deletion('10000000-0000-0000-0000-000000000003');
select pg_temp.assert_true((select count(*)=0 from public.list_library_sources() where title='A 3'),'deleted source disappears immediately on reload');
select pg_temp.assert_true((select count(*)=0 from public.open_published_text('10000000-0000-0000-0000-000000000003',:'pub_version')),'deleted publication no longer opens');
reset role;
rollback;
