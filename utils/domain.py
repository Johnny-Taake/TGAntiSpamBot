import re
from typing import Set
from urllib.parse import urlsplit


def _normalize_domain(value: str) -> str:
    v = (value or "").strip().lower()
    if not v:
        raise ValueError("Empty domain")

    # If URL - get hostname
    if "://" in v:
        host = urlsplit(v).hostname or ""
    else:
        # Split path from URL e.g. "github.com/path"
        host = v.split("/")[0].split("?")[0].split("#")[0]

    host = host.strip().rstrip(".")
    if host.startswith("www."):
        host = host[4:]

    # strip port for bare host: example.com:443
    if ":" in host and host.count(":") == 1:
        host = host.split(":", 1)[0]

    if not host:
        raise ValueError(f"Invalid domain: {value}")

    return host


def parse_domains(raw: str) -> list[str]:
    parts = [p for p in (raw or "").replace(",", " ").split() if p.strip()]
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        d = _normalize_domain(p)
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out


# Excludes emails via negative lookbehind for '@'.
_DOMAIN_RE = re.compile(
    r"""
    (?<!@)
    (?:
        (?P<scheme>[a-zA-Z][a-zA-Z0-9+.-]*)://  # any scheme://
        |
        (?P<www>www\.)
        |
        (?P<tme>t\.me/)
        |
        (?P<bare>(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})  # bare domain.tld
    )
    (?P<rest>[^\s<>"'\]]*)  # optional path/query
    """,
    re.IGNORECASE | re.VERBOSE,
)


def normalize_host(host: str) -> str:
    host = (host or "").lower().strip().rstrip(".")
    if host.startswith("www."):
        host = host[4:]

    # Strip brackets for IPv6-like forms: [::1]:443
    if host.startswith("[") and "]" in host:
        host = host[1: host.index("]")]

    # Strip port for normal hosts: example.com:443
    if ":" in host and host.count(":") == 1:
        host = host.split(":", 1)[0]

    return host


_TRIM_CHARS = ".,;:!?)]}>\"'…<“”’"


def extract_domains_from_text(text: str) -> Set[str]:
    """
    Extract domains from URLs in the given text.
    Supports: anyscheme://domain, www.domain, t.me/
      and bare domains like link.link

    Args:
        text: Text that may contain URLs

    Returns:
        Set of domains extracted from URLs in the text
    """
    domains: Set[str] = set()
    if not text:
        return domains

    for m in _DOMAIN_RE.finditer(text):
        full = (m.group(0) or "").strip().rstrip(_TRIM_CHARS)

        bare = (m.group("bare") or "").strip().rstrip(_TRIM_CHARS)
        if bare:
            domains.add(normalize_host(bare))
            continue

        url = full
        if m.group("www"):
            url = "http://" + full
        elif m.group("tme"):
            url = "http://" + full

        try:
            parsed = urlsplit(url)
            host = normalize_host(parsed.hostname or "")
            if host:
                domains.add(host)
        except Exception:
            continue

    return domains
