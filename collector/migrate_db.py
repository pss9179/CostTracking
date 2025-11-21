import logging
from sqlmodel import create_engine, text
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/cost_tracker")

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.begin()
        try:
            # Add project_id to api_keys
            logger.info("Checking api_keys table...")
            try:
                conn.execute(text("ALTER TABLE api_keys ADD COLUMN project_id UUID"))
                logger.info("Added project_id to api_keys")
            except Exception as e:
                if "duplicate column" in str(e):
                    logger.info("project_id already exists in api_keys")
                else:
                    logger.error(f"Error altering api_keys: {e}")

            # Add project_id to trace_events (traceevent table name might be different, check model)
            # Model says TraceEvent, table name usually traceevent or trace_events
            # Let's check models.py or assume traceevent (default) or trace_events (if __tablename__ set)
            # models.py usually sets table=True, default name is class name lowercase?
            # Let's try both or check models.py content from earlier view
            
            # From earlier view of models.py:
            # class TraceEvent(SQLModel, table=True):
            # It doesn't specify __tablename__, so it defaults to "traceevent"
            
            logger.info("Checking traceevent table...")
            try:
                conn.execute(text("ALTER TABLE traceevent ADD COLUMN project_id UUID"))
                logger.info("Added project_id to traceevent")
            except Exception as e:
                if "duplicate column" in str(e):
                    logger.info("project_id already exists in traceevent")
                elif "does not exist" in str(e):
                     # Try plural
                    try:
                        conn.execute(text("ALTER TABLE trace_events ADD COLUMN project_id UUID"))
                        logger.info("Added project_id to trace_events")
                    except Exception as e2:
                        if "duplicate column" in str(e2):
                            logger.info("project_id already exists in trace_events")
                        else:
                            logger.error(f"Error altering trace_events: {e2}")
                else:
                    logger.error(f"Error altering traceevent: {e}")
            
            conn.commit()
            logger.info("Migration completed successfully.")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
