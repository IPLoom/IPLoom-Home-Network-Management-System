import duckdb
from pathlib import Path
from app.core.config import get_settings
import logging
import threading

logger = logging.getLogger(__name__)

_shared_conn: duckdb.DuckDBPyConnection = None
_db_lock = threading.RLock()

def get_dns_db_lock():
    """Returns the global database lock for DNS DB operations."""
    return _db_lock

def get_dns_connection() -> duckdb.DuckDBPyConnection:
    """
    Returns a cursor from a shared DuckDB connection for the DNS logs database.
    Target DB: backend/data/dns_logs.duckdb
    """
    global _shared_conn
    with _db_lock:
        if _shared_conn is None:
            settings = get_settings()
            # Construct path relative to the main DB path or explicit setting
            # We assume it lives next to the main DB
            main_db_path = Path(settings.db_path)
            dns_db_path = main_db_path.parent / "dns_logs.duckdb"
            dns_db_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Opening DNS database at {dns_db_path}")
            _shared_conn = duckdb.connect(str(dns_db_path))
            
            # Optimization for high volume inserts
            _shared_conn.execute("SET threads TO 4")
            # Maybe lower memory limit if main DB is heavy
            _shared_conn.execute("SET memory_limit = '256MB'") 
            _shared_conn.execute("SET TimeZone='UTC'")
            
            _init_schema(_shared_conn)
        
        return _shared_conn.cursor()

def _init_schema(conn: duckdb.DuckDBPyConnection):
    """Initializes the DNS database schema."""
    try:
        # Table: dns_domains (Lookup)
        conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS seq_domain_id START 1;
            
            CREATE TABLE IF NOT EXISTS dns_domains (
                id          INTEGER PRIMARY KEY DEFAULT nextval('seq_domain_id'),
                domain      TEXT UNIQUE NOT NULL,
                category    TEXT,
                is_blocked  BOOLEAN DEFAULT FALSE,
                last_seen   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_domain_name ON dns_domains(domain);
        """)
        
        # Table: dns_logs (Time-series)
        # Table: dns_logs (Time-series)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dns_logs (
                timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_id   TEXT,
                domain_id   INTEGER,
                status      TEXT,    -- 'Blocked', 'OK', 'Rewritten'
                query_type  TEXT,    -- 'A', 'AAAA', 'PTR', etc.
                client_ip   TEXT,    -- Original IP for reference
                response_time INTEGER, -- ms
                is_blocked  BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (domain_id) REFERENCES dns_domains(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON dns_logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_logs_device_id ON dns_logs(device_id);
            CREATE INDEX IF NOT EXISTS idx_logs_domain_id ON dns_logs(domain_id);
        """)
        
        # Migration: Check if is_blocked exists in dns_logs (for existing DBs)
        try:
            # Describe returns: column_name, column_type, null, key, default, extra
            cols = conn.execute("DESCRIBE dns_logs").fetchall()
            col_names = [c[0] for c in cols]
            if 'is_blocked' not in col_names:
                logger.info("Migrating dns_logs: adding is_blocked column")
                conn.execute("ALTER TABLE dns_logs ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE")
                
                # Try to backfill based on status (best effort)
                try:
                    conn.execute("""
                        UPDATE dns_logs 
                        SET is_blocked = TRUE 
                        WHERE status IN ('FilteredBlackList', 'SafeBrowsing', 'ParentalControl', 'Blocked') 
                           OR status LIKE 'Filtered%'
                    """)
                except Exception as e:
                    logger.warning(f"Failed to backfill is_blocked: {e}")
                    
        except Exception as e:
            logger.warning(f"Migration check failed (table might be empty/new): {e}")

        # Migration: Add query_type if missing
        try:
            cols = conn.execute("DESCRIBE dns_logs").fetchall()
            col_names = [c[0] for c in cols]
            if 'query_type' not in col_names:
                logger.info("Migrating dns_logs: adding query_type column")
                conn.execute("ALTER TABLE dns_logs ADD COLUMN query_type TEXT")
        except Exception as e:
            logger.warning(f"Query type migration check failed: {e}")

    except Exception as e:
        logger.error(f"Failed to initialize DNS DB schema: {e}")
        raise e

def close_dns_connection():
    global _shared_conn
    with _db_lock:
        if _shared_conn:
            try:
                _shared_conn.close()
                logger.info("DNS database connection closed.")
            except Exception as e:
                logger.error(f"Error closing DNS connection: {e}")
            _shared_conn = None

def commit_dns():
    global _shared_conn
    with _db_lock:
        if _shared_conn:
            _shared_conn.commit()
