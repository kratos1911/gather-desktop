"""Backend-only bounded HTTP transport. Not wired to live jobs or a browser.

Run behind an external deadline supervisor: the OS DNS resolver can block.
Resolver/connector injection is trusted test configuration, never request data.
"""
from dataclasses import dataclass
import http.client
import ipaddress
import socket
import ssl
import threading
import time
from urllib.parse import quote, urljoin, urlsplit

from services.worker.network_policy import approve_destination

MAX_BODY = 64 * 1024
MAX_REDIRECTS = 3
TIMEOUT = 10
CONTENT_TYPES = {'text/html', 'text/plain', 'application/xhtml+xml'}


class FetchError(ValueError):
    """Safe error code only; never include URL, headers or response content."""


@dataclass(frozen=True)
class FetchedPage:
    final_url: str
    content_type: str
    body: bytes
    redirects: int


def resolve(host, port):
    return sorted({row[4][0] for row in socket.getaddrinfo(
        host, port, type=socket.SOCK_STREAM)})


def connect(destination, timeout):
    """Dial one previously approved numeric address without a second DNS lookup."""
    address = destination.addresses[0]
    family = socket.AF_INET6 if ipaddress.ip_address(address).version == 6 else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect((address, destination.port))
        if ipaddress.ip_address(sock.getpeername()[0]) != ipaddress.ip_address(address):
            raise FetchError('FETCH_PEER_DENIED')
        if urlsplit(destination.url).scheme == 'https':
            # Preserve hostname verification/SNI even though TCP uses a pinned IP.
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=destination.host)
        return sock
    except BaseException:
        sock.close()
        raise


class _PinnedConnection(http.client.HTTPConnection):
    def connect(self):
        # Never fall back to HTTPConnection's hostname resolution/reconnection.
        raise FetchError('FETCH_RECONNECT_DENIED')


def _abort(sock):
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def fetch_page(url, *, resolver=resolve, connector=connect):
    """Fetch only a page body. No cookies, proxy environment, scripts or assets.

    Each redirect repeats destination approval. HTTPS downgrade is forbidden.
    Compressed responses are rejected rather than decompressed without a budget.
    """
    deadline = time.monotonic() + TIMEOUT
    current = url
    try:
        for hop in range(MAX_REDIRECTS + 1):
            destination = approve_destination(current, resolver)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise FetchError('FETCH_TIMEOUT')
            sock = connector(destination, remaining)
            sock.settimeout(max(.001, deadline - time.monotonic()))
            connection = _PinnedConnection(destination.host, destination.port)
            connection.sock = sock
            timer = threading.Timer(max(0, deadline - time.monotonic()), _abort, (sock,))
            timer.daemon = True
            timer.start()
            try:
                parts = urlsplit(destination.url)
                target = quote(parts.path or '/', safe="/%:@!$&'()*+,;=-._~")
                if parts.query:
                    target += '?' + quote(parts.query, safe="/%?:@!$&'()*+,;=-._~")
                # Explicit Host prevents accidentally sending the selected IP.
                connection.request('GET', target, headers={
                    'Host': parts.netloc, 'User-Agent': 'Gather-fetch/1',
                    'Accept': ', '.join(sorted(CONTENT_TYPES)),
                    'Accept-Encoding': 'identity', 'Connection': 'close',
                })
                with connection.getresponse() as response:
                    # http.client itself caps header count/line length while parsing.
                    if sum(len(k) + len(v) for k, v in response.getheaders()) > 16384:
                        raise FetchError('FETCH_HEADERS_TOO_LARGE')
                    if response.status in (301, 302, 303, 307, 308):
                        locations = response.headers.get_all('Location', [])
                        if len(locations) != 1 or hop == MAX_REDIRECTS:
                            raise FetchError('FETCH_REDIRECT_DENIED')
                        next_url = urljoin(destination.url, locations[0])
                        if parts.scheme == 'https' and urlsplit(next_url).scheme != 'https':
                            raise FetchError('FETCH_REDIRECT_DENIED')
                        current = next_url
                        continue
                    if response.status != 200:
                        raise FetchError('FETCH_STATUS_DENIED')
                    encodings = response.headers.get_all('Content-Encoding', [])
                    if encodings and encodings != ['identity']:
                        raise FetchError('FETCH_ENCODING_DENIED')
                    types = response.headers.get_all('Content-Type', [])
                    content_type = types[0].split(';')[0].strip().lower() if len(types) == 1 else ''
                    if content_type not in CONTENT_TYPES:
                        raise FetchError('FETCH_CONTENT_TYPE_DENIED')
                    lengths = response.headers.get_all('Content-Length', [])
                    transfers = response.headers.get_all('Transfer-Encoding', [])
                    if (len(lengths) > 1 or (lengths and transfers)
                            or (transfers and transfers != ['chunked'])):
                        raise FetchError('FETCH_FRAMING_DENIED')
                    if lengths and (not lengths[0].isdigit() or int(lengths[0]) > MAX_BODY):
                        raise FetchError('FETCH_BODY_TOO_LARGE')
                    body = bytearray()
                    while True:
                        if time.monotonic() >= deadline:
                            raise FetchError('FETCH_TIMEOUT')
                        chunk = response.read1(min(8192, MAX_BODY + 1 - len(body)))
                        if not chunk:
                            break
                        body.extend(chunk)
                        if len(body) > MAX_BODY:
                            raise FetchError('FETCH_BODY_TOO_LARGE')
                    if time.monotonic() >= deadline:
                        raise FetchError('FETCH_TIMEOUT')
                    if lengths and len(body) != int(lengths[0]):
                        raise FetchError('FETCH_TRUNCATED')
                    return FetchedPage(destination.url, content_type, bytes(body), hop)
            finally:
                timer.cancel()
                connection.close()
                sock.close()
        raise FetchError('FETCH_REDIRECT_DENIED')
    except FetchError:
        raise
    except (TimeoutError, socket.timeout):
        raise FetchError('FETCH_TIMEOUT') from None
    except (ValueError, OSError, http.client.HTTPException, UnicodeError):
        if time.monotonic() >= deadline:
            raise FetchError('FETCH_TIMEOUT') from None
        raise FetchError('FETCH_DENIED') from None
