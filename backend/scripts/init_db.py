# To initialize each time without Alembic
import asyncio
import logging
import os

import modules.chat.models  # noqa: F401
import modules.outbox.models  # noqa: F401

# Register every model on Base.metadata. Add one line per module.
import modules.pdf_chatbot.models  # noqa: F401
from settings.database import Base, engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("init_db")

RESET_DB = os.environ["RESET_DB"]


async def init_db():
    async with engine.begin() as connection:
        if RESET_DB:
            log.warning("RESET_DB is on: wiping the public schema.")
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
            await connection.run_sync(Base.metadata.drop_all)
        await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await connection.run_sync(Base.metadata.create_all)
    log.info("Schema ready: %s", ", ".join(sorted(Base.metadata.tables)))
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())
