"""Controlled loopback HTTP -> real fetch subprocess -> offline Docker parser."""
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import threading
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.worker.bookmark_pipeline import BookmarkPipeline
from services.worker.fetch_broker import FetchBroker, BrokerError

BODY = b'<html><title>Fixture page</title><article>Waterproof jacket for rainy walks.</article><script>ignore me</script></html>'


def main():
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            requests.append(self.path)
            if self.path in ('/start', '/blocked'):
                self.send_response(302)
                self.send_header('Location', '/page' if self.path == '/start' else 'http://169.254.169.254/latest')
                self.end_headers()
            else:
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(BODY)))
                self.end_headers()
                self.wfile.write(BODY)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    serving = threading.Thread(target=server.serve_forever, daemon=True)
    serving.start()
    # This mapping is trusted fixture code, never a URL/job option. Destination
    # approval still runs; the test dialer connects only to our loopback peer.
    class LocalBroker(FetchBroker):
        _CHILD_CODE = (
            'import socket; from services.worker import restricted_fetch as r; '
            'original=r.fetch_page; r.fetch_page=lambda url: original(url, '
            'resolver=lambda *a: ["8.8.8.8"], connector=lambda d,t: '
            f'socket.create_connection({server.server_address!r}, t)); '
            'from services.worker.fetch_broker import child_main; child_main()'
        )
    try:
        image = subprocess.check_output(['docker', 'image', 'inspect', 'gather-extraction-extractor',
                                         '--format', '{{.Id}}'], text=True, timeout=15).strip()
        pipeline = BookmarkPipeline(image)
        pipeline.broker = LocalBroker()
        result = pipeline.process('pipeline-fixture', 'http://public.example/start', notes='My rain note')
        assert result['status'] == 'processed'
        document = result['document']
        assert 'Waterproof jacket' in document['fields']['page_text']
        assert 'ignore me' not in document['fields']['page_text']
        assert document['fields']['notes'] == 'My rain note'
        assert document['fetch']['original_url'] == 'http://public.example/start'
        assert document['fetch']['final_url'] == 'http://public.example/page'
        assert document['fetch']['body_sha256'] == hashlib.sha256(BODY).hexdigest()
        assert document['semantic_ready'] is False
        assert any(c['field'] == 'page_text' for c in document['chunks'])
        assert requests == ['/start', '/page']
        print('PASS: controlled HTTP redirect -> supervised fetch -> offline parser -> provenance-labelled passages', flush=True)
        with patch.object(pipeline.parser, 'run') as parse:
            try:
                pipeline.process('denied-fixture', 'http://public.example/blocked')
            except BrokerError as error:
                assert str(error) == 'FETCH_FAILED'
            else:
                raise AssertionError('Metadata redirect accepted')
            parse.assert_not_called()
        assert requests == ['/start', '/page', '/blocked']
        print('PASS: blocked redirect cannot reach parser or metadata endpoint', flush=True)
    finally:
        server.shutdown()
        server.server_close()
        serving.join(timeout=2)


if __name__ == '__main__':
    main()
