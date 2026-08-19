from utils.logger import get_logger

from . import database_migration

logger = get_logger(__name__)


def run_migrations():
    try:
        logger.info("Starting database migration...")
        database_migration.migrate_database()
        logger.info("Database migration finished.")
    except Exception as e:
        logger.error("Migration failed: %s", e, exc_info=True)
        raise
