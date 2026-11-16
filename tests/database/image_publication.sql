-- Storage-only fixtures. Header-only image bytes and synthetic identities/vectors; not OCR evidence.
do $$
declare
  owner_id uuid:='00000000-0000-0000-0000-000000000555';
  other_id uuid:='00000000-0000-0000-0000-000000000666';
  request_id uuid:=gen_random_uuid(); receipt jsonb; replay jsonb; claim jsonb;
  sid uuid; vid uuid; jid uuid; token uuid;
  original bytea:=decode('89504e470d0a1a0a00ff','hex');
  body text:=E'Page one.\n\nPage two.';
  paragraphs jsonb:='{"media_type":"image/png","width":100,"height":50,"engine":"tesseract-5.5.0-lstm","ocr_model_sha256":"7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2","language":"eng","regions":[{"number":1,"start":0,"end":11,"x":5,"y":5,"width":30,"height":15,"confidence":95},{"number":2,"start":11,"end":20,"x":5,"y":25,"width":30,"height":15,"confidence":95}]}';
  manifest jsonb:=jsonb_build_array(jsonb_build_object('id',repeat('a',64),'start',0,'end',11),jsonb_build_object('id',repeat('b',64),'start',11,'end',20));
  vector jsonb:=to_jsonb(array[1]||array_fill(0,array[511]));
  failed boolean;
begin
  if has_table_privilege('authenticated','gather_private.image_text','select') or has_table_privilege('gather_ingestion_worker','gather_private.image_text','select') then raise exception 'private table grant';end if;
  insert into auth.users values(owner_id),(other_id);
  insert into gather_private.source_quotas values(owner_id,2,0),(other_id,2,0);
  perform set_config('request.jwt.claim.sub',owner_id::text,true);
  set local role gather_ingestion_coordinator;
  receipt:=gather_private.submit_automatic_text(request_id,'fixture.png',original,'image/png',
    'image-tesseract-5.5.0-eng-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,null);
  replay:=gather_private.submit_automatic_text(request_id,'fixture.png',original,'image/png',
    'image-tesseract-5.5.0-eng-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,null);
  if receipt<>replay then raise exception 'duplicate import'; end if;
  sid:=(receipt->>'source_id')::uuid;vid:=(receipt->>'version_id')::uuid;jid:=(receipt->>'job_id')::uuid;
  raise notice 'PASS: image OCR duplicate request reuses original/source/version/job';
  set local role gather_ingestion_worker;
  claim:=gather_private.claim_target_text_job(jid);token:=(claim->>'lease_token')::uuid;
  failed:=false;
  begin perform gather_private.stage_pdf(jid,token,original,body,paragraphs,manifest);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'PDF wrapper accepted a image OCR job';end if;
  failed:=false;
  begin perform gather_private.stage_image(jid,token,original,body,'[{"number":1,"start":1,"end":20}]',manifest);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'invalid paragraphs accepted';end if;
  perform gather_private.stage_image(jid,token,original,body,paragraphs,manifest);
  perform gather_private.stage_image(jid,token,original,body,paragraphs,manifest);
  failed:=false;
  begin perform gather_private.stage_image(jid,token,original,body||'changed',paragraphs,manifest);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'changed extraction accepted';end if;
  raise notice 'PASS: exact OCR regions/offsets and immutable staging retries';
  set local role authenticated;
  if public.read_published_image(sid,vid) is not null then raise exception 'private staging visible';end if;
  if public.read_published_image_original(sid,vid) is not null then raise exception 'staged original visible';end if;
  raise notice 'PASS: staging/image metadata and originals private before publication';
  reset role;
  if has_function_privilege('authenticated','gather_private.stage_extracted_document(uuid,uuid,bytea,text,jsonb,jsonb,text)','execute')
    or has_function_privilege('gather_ingestion_worker','gather_private.stage_extracted_document(uuid,uuid,bytea,text,jsonb,jsonb,text)','execute') then
    raise exception 'generic staging helper exposed'; end if;
  set local role authenticated;
  set local role gather_ingestion_worker;
  perform gather_private.stage_vectors(jid,token,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,
    jsonb_build_array(jsonb_build_object('id',repeat('a',64),'vector',vector)));
  failed:=false;
  begin perform gather_private.publish_text(jid,token);
  exception when sqlstate '22023' then failed:=true;end;
  if not failed then raise exception 'partial image OCR published';end if;
  perform gather_private.stage_vectors(jid,token,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,
    jsonb_build_array(jsonb_build_object('id',repeat('b',64),'vector',vector)));
  perform gather_private.publish_text(jid,token);
  raise notice 'PASS: partial vectors hidden; complete image OCR publishes atomically';
  set local role authenticated;
  if public.read_published_image(sid,vid)->'regions'<>paragraphs->'regions' then raise exception 'wrong image OCR paragraphs';end if;
  if (select t.body from public.open_published_text(sid,vid) t)<>body then raise exception 'wrong extracted text';end if;
  perform set_config('request.jwt.claim.sub',other_id::text,true);
  if public.read_published_image(sid,vid) is not null or public.read_published_image_original(sid,vid) is not null or public.request_source_deletion(sid) then raise exception 'foreign access';end if;
  perform set_config('request.jwt.claim.sub',owner_id::text,true);
  if (select count(*) from public.search_published_text(vector,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,20) r where r.source_id=sid)<>2 then raise exception 'owned image OCR not searchable'; end if;
  if not exists(
    select 1 from jsonb_array_elements(public.search_published_previews(
      'two',vector,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512)->'keywords') as hit
    where hit->>'source_id'=sid::text and hit->>'version_id'=vid::text
      and hit->>'media_type'='image/png' and hit->'locations'='[2]'::jsonb
  ) then raise exception 'wrong image preview citation'; end if;
  raise notice 'PASS: image compact keyword preview retains exact location';
  perform set_config('request.jwt.claim.sub',other_id::text,true);
  if exists(select 1 from public.search_published_text(vector,'Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,20) r where r.source_id=sid)
    or exists(select 1 from public.open_published_text(sid,vid)) then raise exception 'foreign image OCR visible';end if;
  perform set_config('request.jwt.claim.sub',owner_id::text,true);
  if decode(public.read_published_image_original(sid,vid)->>'content_base64','base64')<>original then raise exception 'wrong owned original';end if;
  raise notice 'PASS: OCR metadata, original bytes and deletion enforce ownership';
  set local role gather_ingestion_coordinator;
  receipt:=gather_private.submit_automatic_text(gen_random_uuid(),'fixture.png',original,'image/png',
    'image-tesseract-5.5.0-eng-v1','token-512-overlap64-v1','Qwen/Qwen3-Embedding-0.6B','pinned-test-revision',512,sid);
  set local role authenticated;
  if public.read_published_image(sid,vid) is null then raise exception 'replacement hid old publication';end if;
  set local role gather_ingestion_worker;
  jid:=(receipt->>'job_id')::uuid;claim:=gather_private.claim_target_text_job(jid);token:=(claim->>'lease_token')::uuid;
  reset role;
  update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',
    lease_expires_at=clock_timestamp()-interval '1 second' where id=jid;
  set local role gather_ingestion_worker;
  failed:=false;
  begin perform gather_private.stage_image(jid,token,original,body,paragraphs,manifest);
  exception when sqlstate '55000' then failed:=true;end;
  if not failed then raise exception 'expired image OCR lease accepted';end if;
  claim:=gather_private.claim_target_text_job(jid);token:=(claim->>'lease_token')::uuid;
  if token is null then raise exception 'expired claim did not recover';end if;
  raise notice 'PASS: expired image OCR worker fenced and exact job recovered';
  set local role authenticated;
  perform public.request_source_deletion(sid);
  if public.read_published_image(sid,vid) is not null or public.read_published_image_original(sid,vid) is not null then raise exception 'deleted image visible';end if;
  set local role gather_ingestion_worker;
  failed:=false;
  begin perform gather_private.stage_image(jid,token,original,body,paragraphs,manifest);
  exception when sqlstate '55000' then failed:=true;end;
  if not failed then raise exception 'late image OCR worker accepted';end if;
  set local role authenticated;
  if not public.complete_source_cleanup(sid) then raise exception 'image OCR cleanup incomplete';end if;
  reset role;
  if exists(select 1 from gather_private.image_text where version_id=vid) then raise exception 'image OCR metadata retained';end if;
  raise notice 'PASS: replacement, deletion fence and cascading image OCR cleanup';
end $$;
