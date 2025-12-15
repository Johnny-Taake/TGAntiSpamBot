from sqlalchemy import MetaData, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr

from utils import camel_case_to_snake_case


NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Base(DeclarativeBase):
    __abstract__ = True
    metadata = metadata

    __table_args__ = {"sqlite_autoincrement": True}

    @declared_attr
    def __tablename__(cls) -> str:
        name = camel_case_to_snake_case(cls.__name__)
        return name if name.endswith("s") else f"{name}s"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id}>"

    def __str__(self) -> str:
        return self.__repr__()
