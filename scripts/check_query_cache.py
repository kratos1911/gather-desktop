"""Two-command live Redis check with an explicitly synthetic encrypted vector."""
import argparse
import base64
import json
from pathlib import Path
import time
from uuid import uuid4

from services.worker.local_query_cache import load
from services.worker.query_cache import QueryCache
from services.worker.service_transport import request_json, TransportError

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run:
        print('Preview: SET/GET one synthetic encrypted vector with a 600-second expiry; no model or user documents.')
        return
    values=load();events=[];errors=[]
    def transport(*args,**kwargs):
        try:
            return request_json(*args,**kwargs)
        except TransportError as error:
            errors.append(str(error) if str(error) in ('timeout','authentication_failed','rate_limited',
                'invalid_response','service_unavailable','busy','cleanup_failed') else 'unavailable')
            raise
    cache=QueryCache(values['endpoint'],values['token'],base64.b64decode(values['key']),
        _transport=transport,record=events.append)
    query='Synthetic encrypted cache check '+uuid4().hex
    owner='00000000-0000-0000-0000-000000000001';vector=[1.]+[0.]*511
    started=time.monotonic();cache.put(owner,query,vector);written=time.monotonic()
    read=cache.get(owner,query);finished=time.monotonic()
    report=dict(passed=read==vector and events==['stored','hit'],scope='Synthetic Redis transport/crypto, not semantic search',
        endpoint=values['endpoint'],events=events,transport_errors=errors,
        write_ms=round((written-started)*1000,2),read_ms=round((finished-written)*1000,2),
        model_requests=0,fixture_expiry_seconds=600,automatic_retries=0)
    out=ROOT/'output/upstash-cache';out.mkdir(parents=True,exist_ok=True)
    (out/'connection-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if not report['passed']:
        raise SystemExit('Cache check stopped; no automatic retry. See the safe receipt.')


if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError):
        raise SystemExit('Protected cache setup could not be read; no secret values printed.') from None
