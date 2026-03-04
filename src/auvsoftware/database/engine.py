# engine.py
# The Engine is SQLAlchemy's way of talking to the database.
# The Session is how you actually read/write rows — think of it
# like a "unit of work" that batches your changes and commits them.

import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Build the PostgreSQL connection URL from your .env values.
# Format: postgresql+psycopg2://user:password@host:port/dbname
#
# We use psycopg2 as the "driver" (the low-level adapter between
# SQLAlchemy and PostgreSQL). Install it with: pip install psycopg2-binary
DATABASE_URL = (
    f"postgresql+psycopg2://"
    f"{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}"
    f"/{os.getenv('POSTGRES_DB')}"
)

# echo=True prints every SQL statement SQLAlchemy generates — great for learning!
# Set echo=False in production.
engine = create_engine(DATABASE_URL, echo=True)

# SessionLocal is a factory. Each time you call SessionLocal() you get
# a new session — an isolated workspace for database operations.
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    """
    Context-manager style helper. Use it like:

        with get_session() as session:
            session.add(some_object)
            session.commit()

    The session is automatically closed when the block exits,
    even if an exception is raised.
    """
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()  # Undo any changes if something went wrong
        raise
    finally:
        session.close()