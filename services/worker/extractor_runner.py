"""One bounded JSON job on stdin, one JSON response. Offline outputs only."""
import json
import sys
from services.worker.extraction_adapters import crawl4ai_passages, ytdlp_passages
from services.worker.http_page import http_page_passages

MAX_INPUT = 256 * 1024
MAX_OUTPUT = 2 * 1024 * 1024


def run_job(payload):
    try:
        if not isinstance(payload, bytes) or len(payload) > MAX_INPUT:
            raise ValueError()
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result
        job = json.loads(payload.decode('utf-8'), object_pairs_hook=unique)
        required = {'backend', 'source_id', 'url', 'result', 'backend_version', 'fetched_at'}
        if not isinstance(job, dict) or not required <= job.keys() or job.keys() - required - {'notes'}:
            raise ValueError()
        arguments = {key: job[key] for key in ('backend_version', 'fetched_at')}
        arguments['notes'] = job.get('notes', '')
        adapter = {'crawl4ai': crawl4ai_passages, 'yt-dlp': ytdlp_passages,
                   'http-page': http_page_passages}.get(job['backend'])
        if adapter is None:
            raise ValueError()
        document = adapter(job['source_id'], job['url'], job['result'], **arguments)
        response = json.dumps({'status': 'processed', 'document': document}, ensure_ascii=False).encode('utf-8')
        if len(response) > MAX_OUTPUT:
            raise ValueError()
        return response
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return b'{"status":"error","code":"INVALID_EXTRACTION_JOB"}'


def main():
    payload = sys.stdin.buffer.read(MAX_INPUT + 1)
    sys.stdout.buffer.write(run_job(payload) + b'\n')


if __name__ == '__main__':
    main()
