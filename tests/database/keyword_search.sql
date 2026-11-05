-- Real SQL, synthetic identities/vectors. All data lives in a disposable DB.
begin;
create function pg_temp.assert_true(ok boolean,label text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',label;end if;
raise notice 'PASS: %',label;end $$;
create function pg_temp.expect_error(statement text,expected text,label text) returns void language plpgsql as $$
begin begin execute statement;exception when others then
if sqlstate=expected then raise notice 'PASS: %',label;return;end if;raise;end;
raise exception 'FAIL: missing denial %',label;end $$;
create function pg_temp.fixture(who uuid,body text,publish boolean default true,target uuid default null)
returns uuid language plpgsql as $$
declare sid uuid;job uuid;claim jsonb;token uuid;raw bytea:=convert_to(body,'UTF8');
begin
perform set_config('request.jwt.claim.sub',who::text,true);
sid:=coalesce(target,public.save_source(gen_random_uuid(),'file','Keyword fixture'));
job:=gather_private.enqueue_text_job(who,sid,gen_random_uuid(),encode(sha256(raw),'hex'),
 'utf8-plain-v1',octet_length(raw),'text/plain','fixture','synthetic','v1',256);
if not publish then return sid;end if;
claim:=gather_private.claim_target_text_job(job);token:=(claim->>'lease_token')::uuid;
perform gather_private.stage_text(job,token,raw,'text/plain',
 jsonb_build_array(jsonb_build_object('id',repeat('a',64),'start',0,'end',length(body))));
if publish then
 perform gather_private.stage_vectors(job,token,'synthetic','v1',256,
 jsonb_build_array(jsonb_build_object('id',repeat('a',64),'vector',to_jsonb(array[1]||array_fill(0,array[255])))));
 perform gather_private.publish_text(job,token);
end if;
return sid;end $$;
insert into auth.users values('00000000-0000-0000-0000-000000000701'),('00000000-0000-0000-0000-000000000702');
insert into gather_private.source_quotas values('00000000-0000-0000-0000-000000000701',10,0),('00000000-0000-0000-0000-000000000702',10,0);
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Archive requests belong in the Cedar queue.') as sid \gset own_
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Cedar archive requests are documented.') as sid \gset second_
select pg_temp.fixture('00000000-0000-0000-0000-000000000702','Cedar belongs to another account.') as sid \gset foreign_
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Cedar unpublished text.',false) as sid \gset draft_
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Cedar deleted text.') as sid \gset deleted_
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000701',true);
select public.request_source_deletion(:'deleted_sid');
select to_jsonb(array[0,1]||array_fill(0,array[254]))::text as vector \gset
set local role authenticated;
select pg_temp.assert_true((select count(*)=2 and bool_and(similarity=0) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'exact word survives zero cosine; drafts, deleted and foreign rows hidden');
select pg_temp.assert_true((select count(*)=2 from public.search_published_keywords('CEDAR',:'vector','synthetic','v1',256)),'case-insensitive matching');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedars',:'vector','synthetic','v1',256)),'whole tokens, not substring matching');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('unknownword',:'vector','synthetic','v1',256)),'absent exact term stays empty');
select pg_temp.assert_true((select count(*)=1 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256,1)),'requested bound retained');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedar',:'vector','synthetic','wrong',256)),'pinned model revision enforced');
select pg_temp.assert_true((select bool_and(r.body=substring(d.body from r.start_offset+1 for r.end_offset-r.start_offset)) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256) r cross join lateral public.open_published_text(r.source_id,r.version_id) d),'exact version offsets and citations retained');
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256,0)','cedar',:'vector','synthetic','v1'),'22023','invalid count denied');
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)',repeat('x',8193),:'vector','synthetic','v1'),'22023','oversized text denied');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000702',true);
select pg_temp.assert_true((select count(*)=1 and bool_and(source_id=:'foreign_sid'::uuid) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'second owner independently scoped');
select set_config('request.jwt.claim.sub','',true);
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','missing identity denied');
set local role anon;
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','anonymous execution denied');
reset role;
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Orchard replaces the old note.',false,:'own_sid');
set local role authenticated;
select pg_temp.assert_true((select count(*)=2 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'replacement staging preserves previous publication');
reset role;
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Orchard replaces the old note.',true,:'own_sid');
set local role authenticated;
select pg_temp.assert_true((select count(*)=1 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'activated replacement hides old keyword text');
select public.request_source_deletion(:'second_sid');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'deletion hides an existing keyword hit immediately');
rollback;
