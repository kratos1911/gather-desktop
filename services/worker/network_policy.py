"""Public-destination preflight. Not a replacement for enforced network isolation.

The resolver is injected; this module never connects. The future transport must
connect to an approved address without resolving again, enforce TLS host identity,
and run this policy on redirects, subtitle URLs and browser subresources.
"""

from dataclasses import dataclass
import ipaddress
from urllib.parse import urlsplit

from services.worker.bookmarks import normalize_url


@dataclass(frozen=True)
class Destination:
    url: str
    host: str
    port: int
    addresses: tuple[str, ...]


def approve_destination(url, resolver) -> Destination:
    normalized = normalize_url(url)
    parsed = urlsplit(normalized)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if parsed.port == 0 or port not in (80, 443):
        raise ValueError("DESTINATION_PORT_DENIED")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        # Prevent alternate numeric notation being interpreted differently downstream.
        if all(part.isdigit() or part.lower().startswith("0x") for part in host.split(".")):
            raise ValueError("DESTINATION_HOST_DENIED")
        try:
            addresses = resolver(host, port)
        except Exception:
            raise ValueError("DESTINATION_DNS_FAILED") from None
    else:
        addresses = [str(literal)]
    if not isinstance(addresses, (list, tuple)) or not 1 <= len(addresses) <= 32:
        raise ValueError("DESTINATION_DNS_INVALID")
    approved = set()
    for value in addresses:
        try:
            if not isinstance(value, str) or "%" in value:
                raise ValueError()
            address = ipaddress.ip_address(value)
        except ValueError:
            raise ValueError("DESTINATION_DNS_INVALID") from None
        if (not address.is_global or address.is_multicast or address.is_reserved
                or address.is_unspecified or address.is_loopback or address.is_link_local
                or (address.version == 6 and (address.ipv4_mapped or address.sixtofour or address.teredo))):
            raise ValueError("DESTINATION_ADDRESS_DENIED")
        approved.add(str(address))
    return Destination(normalized, host, port, tuple(sorted(approved)))
