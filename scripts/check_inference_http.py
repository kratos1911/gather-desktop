"""Bounded loopback HTTP smoke; real weights only when launched by container guard."""
import http.client
import json
from pathlib import Path
import secrets
import threading
import time

from scripts.check_inference_container import profile_requests, review_rows


def run(runtime):
    from services.inference.asgi import LocalBearer, create_app, create_server
    secret = secrets.token_urlsafe(32)
    app = create_app(runtime, LocalBearer(secret))
    server = create_server(app, port=0)
    thread = threading.Thread(target=server.run, daemon=True)
    report = {'passed': False, 'authentication': 'ephemeral local bearer; not Google IAM'}
    started = time.perf_counter()
    thread.start()
    try:
        deadline = time.monotonic() + runtime.startup_timeout + 5
        while not server.started and thread.is_alive() and time.monotonic() < deadline:
            time.sleep(.02)
        if not server.started:
            raise RuntimeError('http_startup_failed')
        report['startup_seconds'] = time.perf_counter() - started
        port = server.servers[0].sockets[0].getsockname()[1]
        pid = runtime.pid

        def request(payload=None, *, authorized=True):
            connection = http.client.HTTPConnection('127.0.0.1', port, timeout=20)
            try:
                headers = {'Content-Type': 'application/json'}
                if authorized:
                    headers['Authorization'] = 'Bearer ' + secret
                connection.request('GET' if payload is None else 'POST',
                                   '/ready' if payload is None else '/embed',
                                   None if payload is None else json.dumps(payload), headers)
                response = connection.getresponse()
                raw = response.read(128 * 1024 + 1)
                if len(raw) > 128 * 1024:
                    raise RuntimeError('oversized_response')
                return response.status, json.loads(raw)
            finally:
                connection.close()

        checks = {'ready': request() == (200, {'ready': True})}
        fixtures, _ = profile_requests('compatibility')
        # Two known short fixtures, one representative 512-token passage, recovery.
        passage = {'role': 'document', 'texts': ['x' + ' x' * 510]}
        requests = fixtures[:2] + [passage, fixtures[1]]
        checks['unauthorized'] = request(fixtures[0], authorized=False) == (
            401, {'error': 'authentication_failed'})
        rows, statuses = [], []
        for index, payload in enumerate(requests):
            if index == 3:
                oversized = {'role': 'document', 'texts': ['x' + ' x' * 2047]}
                checks['token_limit'] = request(oversized) == (400, {'error': 'token_limit'})
            began = time.perf_counter()
            status, value = request(payload)
            statuses.append(status)
            rows.append({'result': value, 'seconds': time.perf_counter() - began})
        outcomes, valid = review_rows(rows, requests, [None] * len(requests))
        checks.update(vectors=valid, http_statuses=statuses == [200] * 4,
                      process_reused=runtime.pid == pid,
                      repeat_stable=rows[1]['result'] == rows[3]['result'],
                      ready_after=request() == (200, {'ready': True}),
                      passage_tokens=rows[2]['result'].get('prompt_tokens') == 512)
        report.update(checks=checks, outcomes=outcomes, passed=all(checks.values()))
    except Exception as error:
        report['error'] = type(error).__name__  # Never include payloads or credentials.
    finally:
        app.state.stopping.set()
        server.should_exit = True
        thread.join(10)
        report['process_reaped'] = runtime.pid is None
        report['server_stopped'] = not thread.is_alive()
        report['passed'] &= report['process_reaped'] and report['server_stopped']
    return report


def main():
    from services.inference.qwen import QwenEngine
    from services.inference.runtime import Runtime
    report = run(Runtime(QwenEngine, '/model'))
    report['container_peak_bytes'] = int(Path('/sys/fs/cgroup/memory.peak').read_text())
    print(json.dumps(report, allow_nan=False), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
