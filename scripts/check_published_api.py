"""Real JWT/PostgREST retrieval tests with explicitly synthetic unit vectors.

Uses the existing disposable stack and its generated users. No model calls.
"""
import base64
import json
import uuid

from services.worker.text_processing import process_request
from services.worker.search import search as search_text
from services.inference.runtime import MODEL, REVISION, DIMENSIONS


def check_published_api(api, request, sql, check, sources):
    owner, source, token, _ = sources[0]
    other, other_source, other_token, _ = sources[1]
    vector = [1]+[0]*511
    alternate = [0,1]+[0]*510
    body = ('\ufeff# Synthetic search\r\nCafe\u0301 and stars \U0001f31f.\r\n'*40).encode()
    parsed = process_request(json.dumps(dict(version=1,request_id='search-fixture',format='md',
        content_base64=base64.b64encode(body).decode())).encode())['document']
    manifest = [{k:c[k] for k in ('id','start','end')} for c in parsed['chunks']]

    def literal(value):
        return "'"+str(value).replace("'","''")+"'"

    def fixture(who, sid, vec=vector, *, activate=True, revision=REVISION, dimensions=512):
        job = sql(f"select gather_private.enqueue_text_job('{who}','{sid}',gen_random_uuid(),"
            f"'{parsed['source_sha256']}','{parsed['parser_version']}',{len(body)},'text/markdown',"
            f"'{parsed['chunker_version']}',{literal(MODEL)},{literal(revision)},{dimensions})").splitlines()[-1]
        claim = json.loads(sql("set role gather_ingestion_worker; select gather_private.claim_text_job()").splitlines()[-1])
        assert claim['id'] == job
        args = f"'{job}','{claim['lease_token']}'"
        rows = [{'id':c['id'],'vector':vec} for c in manifest]
        sql(f"set role gather_ingestion_worker; select gather_private.stage_text({args},decode('{body.hex()}','hex'),"
            f"'text/markdown',{literal(json.dumps(manifest))}::jsonb); "
            f"select gather_private.stage_vectors({args},{literal(MODEL)},{literal(revision)},{dimensions},{literal(json.dumps(rows))}::jsonb)")
        if activate:
            sql(f"set role gather_ingestion_worker; select gather_private.publish_text({args})")
        return claim

    query = dict(p_query=vector,p_model=MODEL,p_revision=REVISION,p_dimensions=512,p_limit=20)

    class SyntheticProvider:
        # TEST ONLY: identity matches fixture rows, vectors are NOT model outputs.
        def count_tokens(self, text):
            return 32

        def infer(self, request, *, cancel):
            return dict(model=MODEL, revision=REVISION, dimensions=DIMENSIONS,
                        data=[dict(index=0, embedding=vector)])

    def coordinated(who=token):
        return search_text('synthetic stars', provider=SyntheticProvider(),
            api=lambda method, path, payload: api(method, path, who, payload))
    def search(who=token, **overrides):
        return api('POST','/rest/v1/rpc/search_published_text',who,dict(query,**overrides))

    def opened(sid,vid,who=token):
        return api('POST','/rest/v1/rpc/open_published_text',who,{'p_source':sid,'p_version':vid})

    first = fixture(owner,source)
    fixture(other,other_source)
    context = coordinated()
    check(len(context['windows'])==1 and context['windows'][0]['source_id']==source
          and context['windows'][0]['text']==body.decode(),
          'query coordinator joins real JWT search and exact cited context with injected synthetic vectors')
    check(all(w['source_id']==other_source for w in coordinated(other_token)['windows']),
          'query coordinator respects second real bearer session')
    params = {'p_request_key':str(uuid.uuid4()),'p_kind':'file','p_title':'Synthetic secondary'}
    second = str(uuid.UUID(api('POST','/rest/v1/rpc/save_source',token,params)))
    sources.append((owner,second,token,params))  # Existing harness owns exact cleanup.
    draft = fixture(owner,second,alternate,activate=False)
    results = search()
    check(len(results)==len(manifest) and all(r['source_id']==source for r in results),'JWT search excludes other owner and unpublished staging')
    check(all(abs(r['similarity']-1)<1e-6 for r in results),'exact cosine scores match synthetic unit vectors')
    check(len(search(p_limit=1))==1,'search respects requested result limit')
    check(search()==results,'tied passages have deterministic order')
    check(all(r['source_id']==other_source for r in search(other_token)),'second JWT searches only its own publication')
    check(search(p_revision='different')==[] and search(p_model='different')==[],'search keeps model and revision spaces separate')
    check(search(p_query=[1]+[0]*255,p_dimensions=256)==[],'different dimensions never enter cosine comparison')
    doc = opened(source,first['version_id'])[0]
    check(doc['body']==body.decode() and doc['source_sha256']==parsed['source_sha256'],'reader returns exact original text and hash')
    check(doc['passages']==manifest and all(doc['body'][r['start_offset']:r['end_offset']]==r['body'] for r in results),
          'search citations agree with reader Unicode offsets and manifest')
    check(opened(source,first['version_id'],other_token)==[],'reader prevents cross-owner access')
    check(opened(second,draft['version_id'])==[],'reader hides draft version')
    check(opened(str(uuid.uuid4()),first['version_id'])==[],'reader rejects source/version mismatch')
    for bad in (dict(p_limit=0),dict(p_limit=101),dict(p_query=[1]),dict(p_query=[0]*512),
                dict(p_query=['NaN']+[0]*511),dict(p_query=[1e100]+[0]*511),dict(p_dimensions=123),dict(p_query=None)):
        code,_ = request('POST','/rest/v1/rpc/search_published_text',token,dict(query,**bad))
        check(code==400,'malformed vector or search bound rejected')
    for endpoint,payload in (('search_published_text',query),('open_published_text',{'p_source':source,'p_version':first['version_id']})):
        check(request('POST','/rest/v1/rpc/'+endpoint,payload=payload)[0] in (401,403),'anonymous '+endpoint+' denied')
        check(request('POST','/rest/v1/rpc/'+endpoint,'invalid-token',payload)[0]==401,'invalid JWT '+endpoint+' denied')
    # Tamper the signed payload while retaining signature: this must never change identity.
    parts = token.split('.')
    forged = dict(json.loads(base64.urlsafe_b64decode(parts[1]+'='*((-len(parts[1]))%4))),sub=other)
    parts[1] = base64.urlsafe_b64encode(json.dumps(forged).encode()).decode().rstrip('=')
    check(request('POST','/rest/v1/rpc/search_published_text','.'.join(parts),query)[0]==401,'tampered owner claim fails signature verification')
    check(request('GET','/rest/v1/staged_passages',token)[0] in (403,404),'staging table remains unavailable through REST')
    check(request('POST','/rest/v1/rpc/submit_text',token,{})[0] in (403,404),'private ingestion admission is not exposed through REST')

    sql(f"set role gather_ingestion_worker; select gather_private.publish_text('{draft['id']}','{draft['lease_token']}')")
    results = search()
    check([r['source_id'] for r in results[:len(manifest)]]==[source]*len(manifest)
          and all(abs(r['similarity'])<1e-6 for r in results[len(manifest):]),'published secondary source is ranked by cosine distance')
    replacement = fixture(owner,source,alternate,activate=False)
    check(opened(source,first['version_id']) and any(r['version_id']==first['version_id'] for r in search()),'replacement draft preserves prior reader and search version')
    def replacing_api(method, path, payload):
        result = api(method, path, token, payload)
        if path.endswith('/search_published_text'):
            sql(f"set role gather_ingestion_worker; select gather_private.publish_text('{replacement['id']}','{replacement['lease_token']}')")
        return result
    raced = search_text('synthetic stars', provider=SyntheticProvider(), api=replacing_api)
    check(all(w['source_id']!=source for w in raced['windows'])
          and {'source_id':source,'reason':'no_longer_available'} in raced['omitted_sources'],
          'replacement between coordinated ranking and open omits old context')
    check(opened(source,first['version_id'])==[],'stale search citation cannot silently open replacement')
    check(opened(source,replacement['version_id']) and all(r['version_id']!=first['version_id'] for r in search()),'publication switches search and reader to current version')
    # Leave the added fixture tombstoned, so earlier lifecycle assertions retain one source.
    api('POST','/rest/v1/rpc/request_source_deletion',token,{'p_source_id':second})
    check(opened(second,draft['version_id'])==[] and all(r['source_id']!=second for r in search()),'deletion immediately hides reader and search results')
    check(all(r['source_id']==other_source for r in search(other_token)),'other owner remains searchable after deletion')
    sql(f"select gather_private.finish_source_cleanup('{second}')")
    print('Published Auth/REST checks passed. Synthetic vector ordering only; no natural-language model evidence.')
