"""
Database migration to add error logging tables
Run this to create the critical error logging tables
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text

from config.settings import get_settings


def run_migration():
    """Create error logging tables"""
    settings = get_settings()
    engine = create_engine(settings.database.url)

    # Create critical error logs table
    critical_error_logs_sql = """
    CREATE TABLE IF NOT EXISTS critical_error_logs (
        id VARCHAR PRIMARY KEY,
        error_type VARCHAR NOT NULL,
        message TEXT NOT NULL,
        details JSON,
        service VARCHAR,
        user_id VARCHAR,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        resolved_at DATETIME,
        resolution_notes TEXT,
        severity VARCHAR DEFAULT 'HIGH' NOT NULL
    );
    
    CREATE INDEX IF NOT EXISTS idx_critical_error_logs_error_type ON critical_error_logs(error_type);
    CREATE INDEX IF NOT EXISTS idx_critical_error_logs_created_at ON critical_error_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_critical_error_logs_resolved_at ON critical_error_logs(resolved_at);
    """

    # Create system health status table
    system_health_sql = """
    CREATE TABLE IF NOT EXISTS system_health_status (
        id VARCHAR PRIMARY KEY,
        check_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        service_name VARCHAR NOT NULL,
        status VARCHAR NOT NULL,
        response_time_ms VARCHAR,
        error_count_24h VARCHAR,
        details JSON
    );
    
    CREATE INDEX IF NOT EXISTS idx_system_health_service_name ON system_health_status(service_name);
    CREATE INDEX IF NOT EXISTS idx_system_health_check_timestamp ON system_health_status(check_timestamp);
    """

    try:
        with engine.connect() as conn:
            # Execute statements one at a time for SQLite
            statements = [
                """CREATE TABLE IF NOT EXISTS critical_error_logs (
                    id VARCHAR PRIMARY KEY,
                    error_type VARCHAR NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    service VARCHAR,
                    user_id VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    resolved_at DATETIME,
                    resolution_notes TEXT,
                    severity VARCHAR DEFAULT 'HIGH' NOT NULL
                )""",
                "CREATE INDEX IF NOT EXISTS idx_critical_error_logs_error_type ON critical_error_logs(error_type)",
                "CREATE INDEX IF NOT EXISTS idx_critical_error_logs_created_at ON critical_error_logs(created_at)",
                "CREATE INDEX IF NOT EXISTS idx_critical_error_logs_resolved_at ON critical_error_logs(resolved_at)",
                """CREATE TABLE IF NOT EXISTS system_health_status (
                    id VARCHAR PRIMARY KEY,
                    check_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    service_name VARCHAR NOT NULL,
                    status VARCHAR NOT NULL,
                    response_time_ms VARCHAR,
                    error_count_24h VARCHAR,
                    details TEXT
                )""",
                "CREATE INDEX IF NOT EXISTS idx_system_health_service_name ON system_health_status(service_name)",
                "CREATE INDEX IF NOT EXISTS idx_system_health_check_timestamp ON system_health_status(check_timestamp)",
            ]

            for statement in statements:
                conn.execute(text(statement))

            conn.commit()

        print("✅ Error logging tables created successfully")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")


if __name__ == "__main__":
    run_migration()
