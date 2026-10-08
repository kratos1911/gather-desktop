\set ON_ERROR_STOP on
create function pg_temp.assert_true(ok boolean, label text) returns void
language plpgsql as $$ begin
  if ok is distinct from true then raise exception 'FAIL: %', label; end if;
  raise notice 'PASS: %', label;
end $$;
create function pg_temp.expect_error(statement text, expected text, label text)
returns void language plpgsql security invoker as $$ begin
  begin
    execute statement;
  exception when others then
    if sqlstate = expected then raise notice 'PASS: %', label; return; end if;
    raise;
  end;
  raise exception 'FAIL: expected denial: %', label;
end $$;

insert into auth.users values
 ('00000000-0000-0000-0000-000000000001'),
 ('00000000-0000-0000-0000-000000000002');
insert into public.sources(id, owner_id, kind, title, original_url) values
 ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000001','bookmark','A','https://example.com/a'),
 ('10000000-0000-0000-0000-000000000002','00000000-0000-0000-0000-000000000002','file','B',null);
insert into public.source_versions(source_id,owner_id,content_sha256,parser_version)
 select id,owner_id,repeat('a',64),'fixture-v1' from public.sources;
select pg_temp.expect_error($q$insert into public.source_versions(source_id,owner_id,content_sha256,parser_version)
 values ('10000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002',repeat('b',64),'test')$q$,
 '23503','composite FK rejects cross-owner version even for privileged writer');

set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
select pg_temp.assert_true((select count(*) = 1 from public.sources),'A reads only own source');
select pg_temp.assert_true((select count(*) = 1 from public.source_versions),'A reads only own version');
update public.sources set title='Edited A',notes='Synthetic note';
select pg_temp.assert_true((select title='Edited A' from public.sources),'own metadata edit persists');
with changed as (update public.sources set title='Stolen' where id='10000000-0000-0000-0000-000000000002' returning id)
 select pg_temp.assert_true((select count(*)=0 from changed),'cross-owner update affects zero rows');
select pg_temp.expect_error('update public.sources set owner_id=gen_random_uuid()', '42501','ownership cannot be forged');
select pg_temp.expect_error('update public.sources set deleted_at=now()', '42501','client cannot forge lifecycle');
select pg_temp.expect_error('delete from public.sources', '42501','hard deletion denied');
select pg_temp.expect_error($q$insert into public.sources(owner_id,kind,title) values(auth.uid(),'file','Injected')$q$,'42501','client cannot bypass ingestion quotas');
select pg_temp.expect_error('delete from public.source_versions', '42501','versions are immutable to client');
select pg_temp.expect_error($q$update public.sources set title=''$q$,'23514','empty title rejected');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',false);
select pg_temp.assert_true((select count(*)=1 and min(title)='B' from public.sources),'B isolated from A edits');
select pg_temp.assert_true((select count(*)=1 from public.source_versions),'B sees own version');
select set_config('request.jwt.claim.sub','',false);
select pg_temp.assert_true((select count(*)=0 from public.sources),'missing identity fails closed');
set role anon;
select pg_temp.expect_error('select * from public.sources','42501','anonymous source read denied');
select pg_temp.expect_error('select * from public.source_versions','42501','anonymous version read denied');
reset role;
update public.sources set deleted_at=now() where title='Edited A';
set role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',false);
select pg_temp.assert_true((select count(*)=0 from public.sources),'tombstone hides source');
select pg_temp.assert_true((select count(*)=0 from public.source_versions),'tombstone hides dependent versions');
with changed as (update public.sources set title='Resurrected' returning id)
 select pg_temp.assert_true((select count(*)=0 from changed),'client cannot edit tombstoned source');
reset role;
