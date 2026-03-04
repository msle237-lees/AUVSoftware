# base.py
# All SQLAlchemy models must inherit from a single "DeclarativeBase".
# We create it once here and import it everywhere else.
# Think of Base as the "registry" that keeps track of all your tables.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass