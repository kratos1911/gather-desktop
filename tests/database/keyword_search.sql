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
select pg_temp.fixture('00000000-0000-0000-0000-000000000701',repeat('Prior background. ',35)||
  'Cedar archive requests are documented. '||repeat('More details. ',40)) as sid \gset second_
select pg_temp.fixture('00000000-0000-0000-0000-000000000702','Cedar belongs to another account.') as sid \gset foreign_
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Cedar unpublished text.',false) as sid \gset draft_
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Cedar deleted text.') as sid \gset deleted_
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000701',true);
select public.request_source_deletion(:'deleted_sid');
select version_id as vid from gather_private.published_sources where source_id=:'own_sid'::uuid \gset own_
select version_id as vid from gather_private.published_sources where source_id=:'foreign_sid'::uuid \gset foreign_
select version_id as vid from gather_private.published_sources where source_id=:'second_sid'::uuid \gset second_
select to_jsonb(array[0,1]||array_fill(0,array[254]))::text as vector \gset
set local role authenticated;
select pg_temp.assert_true((select count(*)=3 and count(preview)=2 and max(length(preview))=240
  and bool_and(source_id not in (:'foreign_sid'::uuid,:'deleted_sid'::uuid))
  from public.list_library_file_previews()),'library excerpts are bounded to owned publications');
select pg_temp.assert_true((select preview is null from public.list_library_file_previews()
  where source_id=:'draft_sid'::uuid),'unpublished source has no excerpt');
select pg_temp.assert_true((public.read_published_original(:'own_sid',:'own_vid')->>'content_base64') =
  encode(convert_to('Archive requests belong in the Cedar queue.','UTF8'),'base64'),
  'explicit open returns exact immutable original bytes');
select pg_temp.assert_true(public.read_published_original(:'foreign_sid',:'foreign_vid') is null
  and public.read_published_original(:'own_sid',:'second_vid') is null,'foreign and mismatched original reads return no data');
select pg_temp.assert_true((select count(*)=2 and bool_and(similarity=0) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'exact word survives zero cosine; drafts, deleted and foreign rows hidden');
select pg_temp.assert_true((select count(*)=2 from public.search_published_keywords('CEDAR',:'vector','synthetic','v1',256)),'case-insensitive matching');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedars',:'vector','synthetic','v1',256)),'whole tokens, not substring matching');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('unknownword',:'vector','synthetic','v1',256)),'absent exact term stays empty');
select pg_temp.assert_true((select count(*)=1 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256,1)),'requested bound retained');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedar',:'vector','synthetic','wrong',256)),'pinned model revision enforced');
select pg_temp.assert_true((select bool_and(r.body=substring(d.body from r.start_offset+1 for r.end_offset-r.start_offset)) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256) r cross join lateral public.open_published_text(r.source_id,r.version_id) d),'exact version offsets and citations retained');
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256,0)','cedar',:'vector','synthetic','v1'),'22023','invalid count denied');
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)',repeat('x',8193),:'vector','synthetic','v1'),'22023','oversized text denied');
select public.search_published_previews('cedar',:'vector','synthetic','v1',256) as batch \gset
select pg_temp.assert_true(
  (select array_agg(r->>'source_id' order by n) from jsonb_array_elements(:'batch'::jsonb->'semantic') with ordinality t(r,n)) =
  (select array_agg(r.source_id::text order by r.ordinality) from public.search_published_text(:'vector','synthetic','v1',256) with ordinality r)
  and
  (select array_agg(r->>'source_id' order by n) from jsonb_array_elements(:'batch'::jsonb->'keywords') with ordinality t(r,n)) =
  (select array_agg(r.source_id::text order by r.ordinality) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256) with ordinality r),
  'combined preview query preserves the order of both ranking branches');
select pg_temp.assert_true(
  (select length(r->>'body')=240 and (r->>'start_offset')::int>0 and (r->>'body') like '%Cedar%'
    and (r->>'body')=substring(d.body from (r->>'start_offset')::int+1 for (r->>'end_offset')::int-(r->>'start_offset')::int)
   from jsonb_array_elements(:'batch'::jsonb->'keywords') r
   cross join lateral public.open_published_text((r->>'source_id')::uuid,(r->>'version_id')::uuid) d
   where r->>'source_id'=:'second_sid'),
  'late keyword preview is bounded and retains exact Unicode offsets');
select pg_temp.expect_error(format('select public.search_published_previews(%L,%L,%L,%L,256,21)','cedar',:'vector','synthetic','v1'),'22023','preview candidate cap enforced');
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000702',true);
select pg_temp.assert_true((select count(*)=1 and bool_and(source_id=:'foreign_sid'::uuid) from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'second owner independently scoped');
select set_config('request.jwt.claim.sub','',true);
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','missing identity denied');
select pg_temp.expect_error(format('select public.search_published_previews(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','preview requires an identity');
set local role anon;
select pg_temp.expect_error('select * from public.list_library_file_previews()','42501','anonymous library excerpts denied');
select pg_temp.expect_error(format('select public.read_published_original(%L,%L)',:'own_sid',:'own_vid'),'42501','anonymous original denied');
select pg_temp.expect_error(format('select * from public.search_published_keywords(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','anonymous execution denied');
select pg_temp.expect_error(format('select public.search_published_previews(%L,%L,%L,%L,256)','cedar',:'vector','synthetic','v1'),'42501','anonymous preview execution denied');
reset role;
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Orchard replaces the old note.',false,:'own_sid');
set local role authenticated;
select pg_temp.assert_true((select count(*)=2 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'replacement staging preserves previous publication');
select pg_temp.assert_true((select preview='Archive requests belong in the Cedar queue.'
  from public.list_library_file_previews() where source_id=:'own_sid'::uuid),'queued replacement preserves the published excerpt');
reset role;
select pg_temp.fixture('00000000-0000-0000-0000-000000000701','Orchard replaces the old note.',true,:'own_sid');
set local role authenticated;
select pg_temp.assert_true((select count(*)=1 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'activated replacement hides old keyword text');
select pg_temp.assert_true(jsonb_array_length(public.search_published_previews('cedar',:'vector','synthetic','v1',256)->'keywords')=1,'replacement hides old keyword preview');
select pg_temp.assert_true(public.read_published_original(:'own_sid',:'own_vid') is null
  and (select preview='Orchard replaces the old note.' from public.list_library_file_previews()
       where source_id=:'own_sid'::uuid),'replacement swaps the excerpt and closes the old original');
select public.request_source_deletion(:'second_sid');
select pg_temp.assert_true((select count(*)=0 from public.search_published_keywords('cedar',:'vector','synthetic','v1',256)),'deletion hides an existing keyword hit immediately');
select pg_temp.assert_true(jsonb_array_length(public.search_published_previews('cedar',:'vector','synthetic','v1',256)->'keywords')=0,'deletion hides an existing keyword preview');
select pg_temp.assert_true(public.read_published_original(:'second_sid',:'second_vid') is null
  and not exists(select 1 from public.list_library_file_previews() where source_id=:'second_sid'::uuid),
  'deletion hides the original and the library excerpt immediately');
rollback;
