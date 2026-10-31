-- Storage-only fixtures. Deliberately not presented as a valid parsed PDF.
do $$
declare
  owner_id uuid:='00000000-0000-0000-0000-000000000111';
  other_id uuid:='00000000-0000-0000-0000-000000000222';
  request_id uuid:=gen_random_uuid(); receipt jsonb; replay jsonb; claim jsonb;
  sid uuid; vid uuid; jid uuid; token uuid;
  original bytea:=decode('255044462d312e370a00ff2525454f460a','hex');
  body text:=E'Page one.\n\nPage two.';
  pages jsonb:='[{"number":1,"start":0,"end":11},{"number":2,"start":11,"end":20}]';
  manifest jsonb:=jsonb_build_array(jsonb_build_object('id',repeat('a',64),'start',0,'end',11),jsonb_build_object('id',repeat('b',64),'start',11,'end',20));
  vector jsonb:=to_jsonb(array[1]||array_fill(0,array[511]));
  failed boolean;
begin
  if has_table_privilege('authenticated','gather_private.pdf_text','select') or has_table_privilege('gather_ingestion_worker','gather_private.pdf_text','select') then raise exception 'private table grant';end if;
  insert into auth.users values(owner_id),(other_id);
  insert into gather_private.source_quotas values(owner_id,2,0),(other_id,2,0);
  perform set_config('request.jwt.claim.sub',owner_id::text,true);
  set local role gather_ingestion_coordinator;
  receipt:=gather_private.submit_automatic_text(request_id,'fixture.pdf',original,'application/pdf',
    'pdf-pypdf6.21.4-text-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,null);
  replay:=gather_private.submit_automatic_text(request_id,'fixture.pdf',original,'application/pdf',
    'pdf-pypdf6.21.4-text-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,null);
  if receipt<>replay then raise exception 'duplicate import'; end if;
  sid:=(receipt->>'source_id')::uuid;vid:=(receipt->>'version_id')::uuid;jid:=(receipt->>'job_id')::uuid;
  raise notice 'PASS: PDF duplicate request reuses original/source/version/job';
  set local role gather_ingestion_worker;
  claim:=gather_private.claim_target_text_job(jid);token:=(claim->>'lease_token')::uuid;
  failed:=false;
  begin perform gather_private.stage_pdf(jid,token,original,body,'[{"number":1,"start":1,"end":20}]',manifest);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'invalid pages accepted';end if;
  perform gather_private.stage_pdf(jid,token,original,body,pages,manifest);
  perform gather_private.stage_pdf(jid,token,original,body,pages,manifest);
  failed:=false;
  begin perform gather_private.stage_pdf(jid,token,original,body||'changed',pages,manifest);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'changed extraction accepted';end if;
  raise notice 'PASS: exact pages/offsets and immutable staging retries';
  set local role authenticated;
  if public.read_published_pdf(sid,vid) is not null then raise exception 'private staging visible';end if;
  raise notice 'PASS: staging/page metadata private before publication';
  set local role gather_ingestion_worker;
  perform gather_private.stage_vectors(jid,token,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,
    jsonb_build_array(jsonb_build_object('id',repeat('a',64),'vector',vector)));
  failed:=false;
  begin perform gather_private.publish_text(jid,token);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'partial PDF published';end if;
  perform gather_private.stage_vectors(jid,token,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,
    jsonb_build_array(jsonb_build_object('id',repeat('b',64),'vector',vector)));
  perform gather_private.publish_text(jid,token);
  raise notice 'PASS: partial vectors hidden; complete PDF publishes atomically';
  set local role authenticated;
  if public.read_published_pdf(sid,vid)->'pages'<>pages then raise exception 'wrong PDF pages';end if;
  if (select t.body from public.open_published_text(sid,vid) t)<>body then raise exception 'wrong extracted text';end if;
  perform set_config('request.jwt.claim.sub',other_id::text,true);
  if public.read_published_pdf(sid,vid) is not null or public.request_source_deletion(sid) then raise exception 'foreign access';end if;
  perform set_config('request.jwt.claim.sub',owner_id::text,true);
  raise notice 'PASS: page metadata and deletion enforce ownership';
  set local role gather_ingestion_coordinator;
  receipt:=gather_private.submit_automatic_text(gen_random_uuid(),'fixture.pdf',original,'application/pdf',
    'pdf-pypdf6.21.4-text-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,sid);
  set local role authenticated;
  if public.read_published_pdf(sid,vid) is null then raise exception 'replacement hid old publication';end if;
  set local role gather_ingestion_worker;
  jid:=(receipt->>'job_id')::uuid;claim:=gather_private.claim_target_text_job(jid);token:=(claim->>'lease_token')::uuid;
  set local role authenticated;
  perform public.request_source_deletion(sid);
  if public.read_published_pdf(sid,vid) is not null then raise exception 'deleted PDF visible';end if;
  set local role gather_ingestion_worker;
  failed:=false;
  begin perform gather_private.stage_pdf(jid,token,original,body,pages,manifest);
  exception when sqlstate '55000' then failed:=true;end;
  if not failed then raise exception 'late PDF worker accepted';end if;
  set local role authenticated;
  if not public.complete_source_cleanup(sid) then raise exception 'PDF cleanup incomplete';end if;
  reset role;
  if exists(select 1 from gather_private.pdf_text where version_id=vid) then raise exception 'PDF metadata retained';end if;
  raise notice 'PASS: replacement, deletion fence and cascading PDF cleanup';
end $$;
