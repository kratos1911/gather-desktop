"""Actual Linux SIGTERM with synthetic inference and mocked Google keys only."""
import asyncio
import http.client
import json
import os
import select
import signal
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch


class Engine:
    def __init__(self, _):
        pass

    def count_tokens(self, text):
        return 10

    def embed(self, text):
        print('BUSY', flush=True)
        time.sleep(30)
        return [1.]*512


def serve_fixture():
    from services.inference.asgi import create_app, create_server
    from services.inference.runtime import Runtime
    from services.inference.managed_auth import ManagedGoogleServiceAuth
    from tests.inference.test_service_auth import ServiceAuthTests, SUB
    ServiceAuthTests.setUpClass()
    fixture = ServiceAuthTests()
    fixture.setUp()
    auth = ManagedGoogleServiceAuth(fixture.identity,SUB)
    runtime = Runtime(Engine,request_timeout=15)
    original_close = auth.close
    async def checked_close():
        await original_close()
        clean = runtime.pid is None and not auth.ready and not auth._thread.is_alive()
        print('CLEAN' if clean else 'LEAK',flush=True)
        if not clean:
            raise RuntimeError('fixture_cleanup_failed')
    auth.close = checked_close
    app = create_app(runtime,auth)
    server = create_server(app,port=0)
    async def run():
        task = asyncio.create_task(server.serve())
        while not server.started:
            if task.done():
                await task
                raise RuntimeError('fixture_startup_failed')
            await asyncio.sleep(.01)
        port = server.servers[0].sockets[0].getsockname()[1]
        print(json.dumps({'port':port,'token':fixture.token().decode()}),flush=True)
        await task
    with patch('services.inference.managed_auth.request_google_certificates',
               return_value={'certificates':{'fixture':fixture.pem},'ttl':240}):
        asyncio.run(run())


@unittest.skipUnless(sys.platform == 'linux','requires actual Linux signals')
class LinuxShutdownTests(unittest.TestCase):
    def test_sigterm_cancels_inference_and_joins_key_refresh(self):
        process = subprocess.Popen([sys.executable,'-B','-u','-c',
            'from tests.inference.test_linux_auth_shutdown import serve_fixture; serve_fixture()'],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        request_thread = None
        results = []
        try:
            self.assertTrue(select.select([process.stdout],[],[],8)[0], 'startup deadline')
            info = json.loads(process.stdout.readline())
            def request():
                connection = http.client.HTTPConnection('127.0.0.1',info['port'],timeout=8)
                try:
                    connection.request('POST','/embed',body=json.dumps({'role':'query','texts':['hang']}),
                        headers={'Authorization':'Bearer '+info['token'],'Content-Type':'application/json'})
                    response = connection.getresponse()
                    results.append(response.status)
                    response.read()
                except Exception as error:
                    results.append(type(error).__name__)
                finally:
                    connection.close()
            request_thread = threading.Thread(target=request,daemon=True)
            request_thread.start()
            self.assertTrue(select.select([process.stdout],[],[],5)[0], 'inference admission deadline')
            self.assertEqual(process.stdout.readline().strip(),b'BUSY')
            process.send_signal(signal.SIGTERM)
            output, error = process.communicate(timeout=8)
            request_thread.join(2)
            # Uvicorn re-raises SIGTERM after lifespan cleanup, by design.
            self.assertEqual(process.returncode,-signal.SIGTERM,error.decode(errors='replace'))
            self.assertIn(b'CLEAN',output)
            self.assertEqual(results,[503])
            self.assertFalse(request_thread.is_alive())
        finally:
            if process.poll() is None:
                os.killpg(process.pid,signal.SIGKILL)
            process.communicate(timeout=3)
            if request_thread:
                request_thread.join(9)


if __name__ == '__main__':
    unittest.main()
