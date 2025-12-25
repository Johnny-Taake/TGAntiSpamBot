"""Shared utilities for message detection functions."""

from typing import Any


def check_entity_type(entity: Any, target_types: set) -> bool:
    """
    Check if an entity is of any of the target types.

    Args:
        entity: The entity to check
        target_types: Set of target types to check against

    Returns:
        True if entity is of any of the target types, False otherwise
    """
    if isinstance(entity, dict):
        return entity.get("type") in target_types
    elif hasattr(entity, "type"):
        return getattr(entity, "type") in target_types
    return False
