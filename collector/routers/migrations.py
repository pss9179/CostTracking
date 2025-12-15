"""
Migration router for database schema updates.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, inspect
from db import get_session, engine, IS_POSTGRESQL
from sqlmodel import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/migrations", tags=["migrations"])


@router.post("/semantic-label")
def migrate_semantic_label(session: Session = Depends(get_session)):
    """
    Add semantic_label column to trace_events table.
    Safe to run multiple times (checks if column exists first).
    """
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('trace_events')]
        
        if 'semantic_label' in columns:
            logger.info("⚠️  semantic_label column already exists")
            return {"status": "success", "message": "Column already exists"}
        
        if IS_POSTGRESQL:
            migrations = [
                "ALTER TABLE trace_events ADD COLUMN IF NOT EXISTS semantic_label VARCHAR(255);",
                "CREATE INDEX IF NOT EXISTS idx_trace_events_semantic_label ON trace_events(semantic_label);",
            ]
        else:
            migrations = [
                "ALTER TABLE trace_events ADD COLUMN semantic_label VARCHAR(255);",
                "CREATE INDEX IF NOT EXISTS idx_trace_events_semantic_label ON trace_events(semantic_label);",
            ]
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for i, sql in enumerate(migrations, 1):
                    logger.info(f"Running semantic_label migration {i}/{len(migrations)}")
                    conn.execute(text(sql))
                trans.commit()
                logger.info("✅ semantic_label migration completed")
                return {"status": "success", "message": "semantic_label column added"}
            except Exception as e:
                trans.rollback()
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    return {"status": "success", "message": "Column already exists"}
                raise
    except Exception as e:
        logger.error(f"semantic_label migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/voice-columns")
def migrate_voice_columns(session: Session = Depends(get_session)):
    """
    Add voice-related columns to trace_events table.
    Columns: voice_call_id, audio_duration_seconds, voice_segment_type
    Safe to run multiple times.
    """
    try:
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('trace_events')]
        
        # Define all voice columns to add
        voice_columns = [
            ("voice_call_id", "VARCHAR(255)", True),  # name, type, create_index
            ("audio_duration_seconds", "FLOAT", False),
            ("voice_segment_type", "VARCHAR(50)", False),
        ]
        
        added = []
        skipped = []
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for col_name, col_type, create_index in voice_columns:
                    if col_name in columns:
                        skipped.append(col_name)
                        continue
                    
                    if IS_POSTGRESQL:
                        conn.execute(text(f"ALTER TABLE trace_events ADD COLUMN IF NOT EXISTS {col_name} {col_type};"))
                    else:
                        conn.execute(text(f"ALTER TABLE trace_events ADD COLUMN {col_name} {col_type};"))
                    
                    if create_index:
                        conn.execute(text(f"CREATE INDEX IF NOT EXISTS idx_trace_events_{col_name} ON trace_events({col_name});"))
                    
                    added.append(col_name)
                
                trans.commit()
                logger.info(f"✅ voice columns migration: added={added}, skipped={skipped}")
                return {"status": "success", "added": added, "skipped": skipped}
            except Exception as e:
                trans.rollback()
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    return {"status": "success", "message": "Columns already exist", "added": added, "skipped": skipped}
                raise
    except Exception as e:
        logger.error(f"voice columns migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.post("/all")
def migrate_all(session: Session = Depends(get_session)):
    """
    Run all migrations to ensure schema is up to date.
    Safe to run multiple times.
    """
    results = {}
    
    # Run semantic_label migration
    try:
        result = migrate_semantic_label(session)
        results["semantic_label"] = result
    except Exception as e:
        results["semantic_label"] = {"status": "error", "message": str(e)}
    
    # Run voice columns migration
    try:
        result = migrate_voice_columns(session)
        results["voice_columns"] = result
    except Exception as e:
        results["voice_columns"] = {"status": "error", "message": str(e)}
    
    # Run voice_platform migration
    try:
        result = migrate_voice_platform(session)
        results["voice_platform"] = result
    except Exception as e:
        results["voice_platform"] = {"status": "error", "message": str(e)}
    
    return {"status": "success", "migrations": results}


@router.post("/voice-platform")
def migrate_voice_platform(session: Session = Depends(get_session)):
    """
    Add voice_platform column to trace_events table.
    Safe to run multiple times (checks if column exists first).
    """
    try:
        # Check if column already exists
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('trace_events')]
        
        if 'voice_platform' in columns:
            logger.info("⚠️  voice_platform column already exists")
            return {"status": "success", "message": "Column already exists"}
        
        # Build migration SQL based on database type
        if IS_POSTGRESQL:
            migrations = [
                "ALTER TABLE trace_events ADD COLUMN IF NOT EXISTS voice_platform VARCHAR(50);",
                "CREATE INDEX IF NOT EXISTS idx_trace_events_voice_platform ON trace_events(voice_platform);",
            ]
        else:
            # SQLite doesn't support IF NOT EXISTS in ALTER TABLE
            migrations = [
                "ALTER TABLE trace_events ADD COLUMN voice_platform VARCHAR(50);",
                "CREATE INDEX IF NOT EXISTS idx_trace_events_voice_platform ON trace_events(voice_platform);",
            ]
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                for i, sql in enumerate(migrations, 1):
                    logger.info(f"Running migration {i}/{len(migrations)}")
                    conn.execute(text(sql))
                trans.commit()
                logger.info("✅ voice_platform migration completed")
                return {"status": "success", "message": "voice_platform column added"}
            except Exception as e:
                trans.rollback()
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg or "duplicate column" in error_msg:
                    logger.info("⚠️  Column/index already exists")
                    return {"status": "success", "message": "Column already exists"}
                raise
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

