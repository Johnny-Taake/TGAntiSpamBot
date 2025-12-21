"""
Request Parts Data Model
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class RequestParts:
    """Container for HTTP request components."""

    url: str
    headers: Dict[str, str]
    payload: Dict[str, Any]
