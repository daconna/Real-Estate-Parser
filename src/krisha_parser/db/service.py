"""Database service"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from krisha_parser.db.models import Apartment, JKMetrics

logger = logging.getLogger()


def get_connection(db_path: Path | str) -> sqlite3.Connection:
    """Get database connection"""
    db_path = Path(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    logger.info(f"Connected to database: {db_path}")
    return conn


def init_database(conn: sqlite3.Connection):
    """Initialize database schema"""
    cursor = conn.cursor()
    
    # Create apartments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apartments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            krisha_id TEXT UNIQUE NOT NULL,
            jk_name TEXT,
            district TEXT NOT NULL,
            address TEXT NOT NULL,
            price INTEGER NOT NULL,
            area REAL NOT NULL,
            rooms INTEGER NOT NULL,
            price_per_sqm REAL NOT NULL,
            description TEXT,
            photos_count INTEGER DEFAULT 0,
            phone TEXT,
            seller_type TEXT,
            url TEXT NOT NULL,
            parsed_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create jk_metrics table for aggregated statistics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jk_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jk_name TEXT NOT NULL,
            district TEXT NOT NULL,
            avg_price REAL NOT NULL,
            avg_price_per_sqm REAL NOT NULL,
            avg_area REAL NOT NULL,
            median_price REAL NOT NULL,
            count_total INTEGER NOT NULL,
            count_1room INTEGER DEFAULT 0,
            count_2room INTEGER DEFAULT 0,
            count_3plus_room INTEGER DEFAULT 0,
            min_price INTEGER,
            max_price INTEGER,
            snapshot_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_district ON apartments(district)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jk_name ON apartments(jk_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_price_per_sqm ON apartments(price_per_sqm)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_parsed_at ON apartments(parsed_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jk_date ON jk_metrics(jk_name, snapshot_date)")
    
    conn.commit()
    logger.info("Database schema initialized")


def save_apartment(conn: sqlite3.Connection, apartment: Apartment) -> bool:
    """Save or update apartment in database"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO apartments 
            (krisha_id, jk_name, district, address, price, area, rooms, 
             price_per_sqm, description, photos_count, phone, seller_type, url, parsed_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            apartment.krisha_id,
            apartment.jk_name,
            apartment.district,
            apartment.address,
            apartment.price,
            apartment.area,
            apartment.rooms,
            apartment.price_per_sqm,
            apartment.description,
            apartment.photos_count,
            apartment.phone,
            apartment.seller_type,
            apartment.url,
            apartment.parsed_at,
            datetime.now()
        ))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError as e:
        logger.error(f"Error saving apartment {apartment.krisha_id}: {e}")
        return False


def get_apartments_by_district(conn: sqlite3.Connection, district: str) -> list[dict]:
    """Get all apartments in a district"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM apartments 
        WHERE district = ?
        ORDER BY parsed_at DESC
    """, (district,))
    
    return [dict(row) for row in cursor.fetchall()]


def get_latest_apartments(conn: sqlite3.Connection, limit: int = 100) -> list[dict]:
    """Get latest parsed apartments"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM apartments 
        ORDER BY parsed_at DESC
        LIMIT ?
    """, (limit,))
    
    return [dict(row) for row in cursor.fetchall()]
