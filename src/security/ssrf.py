"""SSRF Protection and Safe URL Resolver."""

from __future__ import annotations
import ipaddress
import socket
import urllib.parse
from typing import Tuple
from src.config import settings


class SSRFValidationError(ValueError):
    """Raised when a URL violates SSRF safety rules."""
    pass


BLOCKED_NETWORKS = [ipaddress.ip_network(cidr) for cidr in settings.blocked_ip_ranges]


def is_ip_allowed(ip_str: str) -> bool:
    """Check if an IP address is public and safe to request."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    for net in BLOCKED_NETWORKS:
        if ip in net:
            return False

    return True


def validate_and_resolve_url(url: str) -> Tuple[str, str, int]:
    """
    Validate URL scheme, structure, and safely resolve hostname against SSRF.
    Returns (normalized_url, resolved_ip, port).
    Raises SSRFValidationError if unsafe.
    """
    if not url or not isinstance(url, str):
        raise SSRFValidationError("URL cannot be empty")

    parsed = urllib.parse.urlsplit(url.strip())
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFValidationError(f"Invalid URL scheme '{parsed.scheme}'. Only http and https are permitted.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL missing valid hostname")

    # Reject localhost & internal names directly
    lower_host = hostname.lower()
    if lower_host in ("localhost", "local", "internal", "metadata.google.internal") or lower_host.endswith(".local") or lower_host.endswith(".internal"):
        raise SSRFValidationError(f"Access to internal hostname '{hostname}' is blocked")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)

    # Safe DNS resolution
    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise SSRFValidationError(f"DNS resolution failed for '{hostname}': {e}")

    if not addr_info:
        raise SSRFValidationError(f"No IP addresses resolved for '{hostname}'")

    # Check each resolved address
    first_safe_ip = None
    for item in addr_info:
        ip_addr = item[4][0]
        if not is_ip_allowed(ip_addr):
            raise SSRFValidationError(f"Destination IP '{ip_addr}' for '{hostname}' is private/reserved and blocked.")
        if first_safe_ip is None:
            first_safe_ip = ip_addr

    normalized_url = urllib.parse.urlunsplit((
        parsed.scheme.lower(),
        f"{parsed.netloc}",
        parsed.path or "/",
        parsed.query,
        ""  # strip fragments
    ))

    return normalized_url, first_safe_ip, port
