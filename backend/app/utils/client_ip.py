from __future__ import annotations

import ipaddress
from functools import lru_cache
from typing import Iterable, Optional

from fastapi import Request

from app.config import settings


@lru_cache(maxsize=32)
def _parse_trusted_proxies(raw: str) -> tuple[ipaddress._BaseNetwork, ...]:
    items: list[ipaddress._BaseNetwork] = []
    for part in (raw or "").split(","):
        token = part.strip()
        if not token:
            continue
        try:
            if "/" in token:
                items.append(ipaddress.ip_network(token, strict=False))
            else:
                ip = ipaddress.ip_address(token)
                items.append(
                    ipaddress.ip_network(f"{ip}/{128 if ip.version == 6 else 32}")
                )
        except ValueError:
            continue
    return tuple(items)


def _is_trusted_proxy(remote_ip: str, trusted: Iterable[ipaddress._BaseNetwork]) -> bool:
    try:
        ip = ipaddress.ip_address(remote_ip)
    except ValueError:
        return False
    return any(ip in net for net in trusted)


def _extract_first_forwarded_ip(x_forwarded_for: str) -> Optional[str]:
    if not x_forwarded_for:
        return None
    first = x_forwarded_for.split(",", 1)[0].strip()
    if not first or first.lower() == "unknown":
        return None
    try:
        ipaddress.ip_address(first)
        return first
    except ValueError:
        return None


def get_client_ip(request: Request) -> str:
    remote_ip = request.client.host if request.client else ""
    if not remote_ip:
        remote_ip = "0.0.0.0"

    if not settings.app.trust_proxy_headers:
        return remote_ip

    trusted = _parse_trusted_proxies(settings.app.trusted_proxy_ips)
    if not trusted or not _is_trusted_proxy(remote_ip, trusted):
        return remote_ip

    forwarded = request.headers.get("X-Forwarded-For", "")
    parsed = _extract_first_forwarded_ip(forwarded)
    if parsed:
        return parsed

    real_ip = request.headers.get("X-Real-IP", "").strip()
    if real_ip and real_ip.lower() != "unknown":
        try:
            ipaddress.ip_address(real_ip)
            return real_ip
        except ValueError:
            pass

    return remote_ip

