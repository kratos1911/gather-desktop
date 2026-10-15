"""Real database transactions with synthetic documents/vectors; no model calls."""
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.worker.text_processing import process_request


def publication_checks(name, run):
    def sql(statement):
        return run('exec', '-i', name, 'psql', '-X', '-qAt', '-U', 'postgres',
                   '-v', 'ON_ERROR_STOP=1', input=statement).stdout.strip()

    def lit(value):
        return "'" + str(value).replace("'", "''") + "'"

    def js(value):
        return lit(json.dumps(value)) + '::jsonb'

    def worker(statement):
        return sql('set role gather_ingestion_worker; ' + statement)

    count = 0

    def check(condition, label):
        nonlocal count
        assert condition, label
        count += 1
        print('PASS: publication ' + label)

    def denied(action, reason):
        try:
            action()
        except subprocess.CalledProcessError as error:
            assert reason in error.stderr, error.stderr
            check(True, 'rejects ' + reason)
        else:
            raise AssertionError('Expected rejection: ' + reason)

    owner, other = [str(uuid.uuid4()) for _ in range(2)]
    sql(f"insert into auth.users values('{owner}'),('{other}'); "
        f"insert into gather_private.source_quotas values('{owner}',4,0),('{other}',4,0)")

    def client(statement, who=owner):
        return sql(f"set role authenticated; set request.jwt.claim.sub='{who}'; " + statement)

    source = client("select public.save_source(gen_random_uuid(),'file','Publication fixture')")
    raw = ('\ufeff# Notebook\r\n' + 'Cafe\u0301, stars \U0001f31f and **notes**.\r\n' * 55).encode()
    parsed = process_request(json.dumps(dict(version=1, request_id='publication-fixture',
        format='md', content_base64=base64.b64encode(raw).decode())).encode())
    assert parsed['status'] == 'processed'
    document = parsed['document']
    manifest = [{k: c[k] for k in ('id', 'start', 'end')} for c in document['chunks']]
    assert 1 < len(manifest) <= 16
    vectors = [dict(id=c['id'], vector=[1] + [0]*255) for c in manifest]

    def enqueue(data=raw):
        return sql(f"select gather_private.enqueue_text_job('{owner}','{source}',gen_random_uuid(),"
                   f"'{hashlib.sha256(data).hexdigest()}','utf8-plain-v1',{len(data)},'text/markdown',"
                   f"'{document['chunker_version']}','synthetic-unit-vectors','fixture-v1',256)")

    def claim():
        return json.loads(worker('select gather_private.claim_text_job()'))

    def text(job, data=raw, parts=manifest, media='text/markdown'):
        return worker(f"select gather_private.stage_text('{job['id']}','{job['lease_token']}',"
                      f"decode('{data.hex()}','hex'),{lit(media)},{js(parts)})")

    def embed(job, rows=vectors, model='synthetic-unit-vectors', revision='fixture-v1', dimensions=256):
        return worker(f"select gather_private.stage_vectors('{job['id']}','{job['lease_token']}',"
                      f"{lit(model)},{lit(revision)},{dimensions},{js(rows)})")

    def publish(job):
        return worker(f"select gather_private.publish_text('{job['id']}','{job['lease_token']}')")

    def read(who=owner):
        return json.loads(client(f"select coalesce(jsonb_agg(to_jsonb(t)),'[]') "
                                 f"from public.read_published_text('{source}') t", who))

    enqueue()
    job = claim()
    for data in (raw[:-1], b'x'+raw[1:]):
        denied(lambda: text(job, data), 'source_integrity')
    denied(lambda: text(job, media='text/plain'), 'source_integrity')
    for parts in (manifest[:-1], [dict(manifest[0], start=1), *manifest[1:]],
                  [dict(manifest[0], end=len(raw)), *manifest[1:]]):
        denied(lambda: text(job, parts=parts), 'passage_coverage')
    denied(lambda: text(job, parts=[dict(manifest[0], start='0'), *manifest[1:]]), 'invalid_passage')
    denied(lambda: text(job, parts=manifest*257), 'passage_limit')
    check(sql('select count(*) from gather_private.staged_text') == '0', 'invalid staging rolls back')
    check(text(job) == job['version_id'] and text(job) == job['version_id'], 'text replay is idempotent')
    denied(lambda: text(job, parts=[dict(manifest[0], id='a'*64), *manifest[1:]]), 'manifest_conflict')
    check(read() == [] and read(other) == [], 'staging hidden from clients')
    for role in ('authenticated', 'anon', 'gather_ingestion_worker'):
        denied(lambda: sql(f'set role {role}; select * from gather_private.staged_passages'), 'permission denied')
    denied(lambda: client(f"select gather_private.publish_text('{job['id']}','{job['lease_token']}')", other), 'permission denied')
    for kwargs in (dict(model='other'), dict(revision='other'), dict(dimensions=512)):
        denied(lambda: embed(job, **kwargs), 'embedding_identity')
    denied(lambda: embed(job, vectors[:1]*17), 'vector_batch_limit')
    for vector, error in (([1], 'vector_dimensions_or_values'),
                          (['NaN']+[0]*255, 'vector_dimensions_or_values'),
                          ([1e100]+[0]*255, 'out of range'),
                          ([0]*256, 'vector_not_normalized')):
        denied(lambda: embed(job, [dict(vectors[0], vector=vector)]), error)
    denied(lambda: embed(job, [vectors[0], vectors[0]]), 'duplicate_vector')
    denied(lambda: embed(job, [vectors[0], dict(vectors[1], id='f'*64)]), 'unknown_passage')
    check(sql('select count(*) from gather_private.staged_passages where embedding is not null') == '0', 'invalid vector batch rolls back earlier rows')
    embed(job, vectors[:1])
    denied(lambda: publish(job), 'incomplete_index')
    check(read() == [], 'partial vectors stay hidden')
    check(embed(job) == str(len(vectors)) and embed(job) == str(len(vectors)), 'vector replay is idempotent')
    denied(lambda: embed(job, [dict(vectors[0], vector=[0,1]+[0]*254)]), 'vector_conflict')
    worker(f"begin; select gather_private.publish_text('{job['id']}','{job['lease_token']}'); rollback;")
    check(read() == [] and sql(f"select state from gather_private.ingestion_jobs where id='{job['id']}'") == 'processing',
          'aborted publication rolls back pointer and ready status together')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish, [job, job]))
    check(results == [job['version_id']]*2, 'concurrent publications activate one version')
    check(sql(f"select state from gather_private.ingestion_jobs where id='{job['id']}'") == 'ready', 'ready committed with publication')
    rows = read()
    check(len(rows) == len(manifest) and all(
        r['body'] == raw.decode()[r['start_offset']:r['end_offset']]
        and r['source_sha256'] == document['source_sha256'] and r['dimensions'] == 256
        and r['model_revision'] == 'fixture-v1' and r['model_id'] == 'synthetic-unit-vectors'
        and r['passage_id'] == manifest[i]['id'] for i, r in enumerate(rows)),
        'citations preserve Unicode, BOM, CRLF, offsets and identity')
    check(read(other) == [], 'other owner cannot read publication')
    denied(lambda: sql(f"set role anon; select * from public.read_published_text('{source}')"), 'permission denied')
    denied(lambda: publish(dict(job, lease_token=str(uuid.uuid4()))), 'stale_lease')
    enqueue()
    replacement = claim()
    text(replacement)
    check(read() == rows, 'replacement keeps previous publication readable')
    denied(lambda: publish(job), 'stale_lease')
    denied(lambda: publish(replacement), 'incomplete_index')
    embed(replacement)
    sql(f"update gather_private.ingestion_jobs set lease_started_at=clock_timestamp()-interval '2 minutes',"
        f"lease_expires_at=clock_timestamp()-interval '1 second' where id='{replacement['id']}'")
    denied(lambda: publish(replacement), 'stale_lease')
    recovered = claim()
    check(recovered['attempts'] == 2 and recovered['lease_token'] != replacement['lease_token'], 'lease recovery rotates token')
    check(text(recovered) == recovered['version_id'] and embed(recovered) == str(len(vectors)), 'recovery reuses staging')
    publish(recovered)
    check(all(r['version_id'] == recovered['version_id'] for r in read()), 'replacement switches complete version')
    for data, reason in ((b'\xff','invalid_utf8'), (b'\x00','invalid_utf8'),
                         (b'a\x01b','invalid_text'), (b' \r\n\t','invalid_text'),
                         ('\ufeff\u00a0\u2000'.encode(), 'invalid_text')):
        enqueue(data)
        invalid = claim()
        denied(lambda: text(invalid, data), reason)
        check(all(r['version_id'] == recovered['version_id'] for r in read()), 'invalid replacement preserves publication')
    enqueue()
    prior = claim()
    text(prior)
    embed(prior)

    def publish_or_stale(item):
        try:
            return publish(item)
        except subprocess.CalledProcessError as error:
            if 'stale_lease' in error.stderr:
                return 'stale'
            raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        activation = pool.submit(publish_or_stale, prior)
        newer = pool.submit(enqueue)
        check(activation.result() in ('stale', prior['version_id']) and newer.result() != prior['id'], 'replacement/publication race serialized')
    denied(lambda: publish(prior), 'stale_lease')
    latest = claim()
    text(latest)
    embed(latest)
    with ThreadPoolExecutor(max_workers=2) as pool:
        activation = pool.submit(publish_or_stale, latest)
        deletion = pool.submit(client, f"select public.request_source_deletion('{source}')")
        check(activation.result() in ('stale', latest['version_id']) and deletion.result() == 't', 'deletion/publication race serialized')
    check(read() == [], 'deleted publication immediately hidden')
    for action in (publish, text, embed):
        denied(lambda: action(latest), 'stale_lease')
    check(sql(f"select gather_private.finish_source_cleanup('{source}')") == 't', 'cleanup succeeds')
    check(sql('select (select count(*) from gather_private.staged_text) + '
              '(select count(*) from gather_private.staged_passages) + '
              '(select count(*) from gather_private.published_sources)') == '0', 'cleanup removes bytes, vectors and receipts')
    print(f'Publication checks passed: {count}. Synthetic vectors only; no semantic retrieval evidence.')
