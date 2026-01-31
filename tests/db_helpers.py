"""
Database helper functions for E2E tests.
Provides utilities to manipulate database state directly for testing time-based restrictions.
"""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Media

def get_db_session():
    """
    Create a SQLAlchemy session using the DATABASE_URL from environment.
    Used for E2E tests that need direct database access.
    """
    import urllib.parse
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise EnvironmentError("DATABASE_URL not set in environment variables.")
    
    # Parse URL to check if password is missing
    parsed = urllib.parse.urlparse(database_url)
    if parsed.password is None or parsed.password == '':
        # Need to add password
        password = os.environ.get('POSTGRES_PASSWORD')
        if not password:
            # Try to load from .env file in project root
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            if line.startswith('POSTGRES_PASSWORD='):
                                password = line.split('=', 1)[1].strip()
                                break
                except Exception:
                    pass
        if password:
            # Reconstruct URL with password
            netloc = f'{parsed.username}:{password}@{parsed.hostname}'
            if parsed.port:
                netloc += f':{parsed.port}'
            database_url = urllib.parse.urlunparse(
                (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
            )
        else:
            raise EnvironmentError("Password required for database connection but POSTGRES_PASSWORD not set.")
    
    # Use existing engine without creating tables
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def update_media_upload_date(media_id, new_upload_date):
    """
    Update the upload_date of a media record.
    
    Args:
        media_id: ID of the media record
        new_upload_date: datetime object (UTC)
    
    Returns:
        bool: True if update successful, False otherwise
    """
    session = get_db_session()
    try:
        media = session.query(Media).filter(Media.id == media_id).first()
        if not media:
            return False
        media.upload_date = new_upload_date
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def make_media_old(media_id, hours_older=49):
    """
    Convenience function to make a media record older than the deletion limit.
    
    Args:
        media_id: ID of the media record
        hours_older: number of hours to subtract from current time (default 49 > 48 limit)
    
    Returns:
        bool: True if successful
    """
    from utils.timezone import utc_now
    new_date = utc_now() - timedelta(hours=hours_older)
    return update_media_upload_date(media_id, new_date)

def get_media_upload_date(media_id):
    """
    Retrieve the upload_date of a media record.
    
    Args:
        media_id: ID of the media record
    
    Returns:
        datetime or None
    """
    session = get_db_session()
    try:
        media = session.query(Media).filter(Media.id == media_id).first()
        return media.upload_date if media else None
    finally:
        session.close()