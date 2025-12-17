"""
Database utility functions to reduce boilerplate code in database operations.
"""

from typing import TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exc as sqlalchemy_exc
from sqlalchemy.orm import DeclarativeBase
from logger import get_logger

T = TypeVar("T", bound=DeclarativeBase)
log = get_logger(__name__)


async def get_or_create(
    session: AsyncSession, model: Type[T], **kwargs
) -> tuple[T, bool]:
    """
    Get an object or create it if it doesn't exist.

    Args:
        session: SQLAlchemy async session
        model: The model class to query
        **kwargs: Fields to match for existing object

    Returns:
        Tuple of (object, created) where created is a boolean indicating if the object was created
    """
    stmt = select(model).filter_by(**kwargs)
    result = await session.execute(stmt)
    instance = result.scalar_one_or_none()

    if instance:
        return instance, False

    try:
        instance = model(**kwargs)
        session.add(instance)
        await session.flush()
        return instance, True
    except sqlalchemy_exc.IntegrityError:
        # Handle race condition where another worker created the same record
        await session.rollback()
        # Try to get the record again after rollback
        stmt = select(model).filter_by(**kwargs)
        result = await session.execute(stmt)
        instance = result.scalar_one_or_none()
        if instance:
            return instance, False
        else:
            raise
