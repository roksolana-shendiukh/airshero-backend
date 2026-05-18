from sqlalchemy.orm import Session
from sqlalchemy import text


def get_db_stats(db: Session) -> dict:
    db_size_mb = db.execute(text("""
        SELECT SUM(size * 8.0 / 1024) AS size_mb
        FROM sys.database_files
    """)).scalar() or 0

    active_connections = db.execute(text("""
        SELECT COUNT(*) FROM sys.dm_exec_sessions
        WHERE is_user_process = 1
    """)).scalar()

    rows = db.execute(text("""
        SELECT
            t.name AS table_name,
            p.rows AS row_count,
            ROUND((SUM(a.total_pages) * 8.0) / 1024, 2) AS size_mb
        FROM sys.tables t
        JOIN sys.indexes i ON t.object_id = i.object_id
        JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
        JOIN sys.allocation_units a ON p.partition_id = a.container_id
        WHERE i.index_id <= 1
        GROUP BY t.name, p.rows
        ORDER BY size_mb DESC
    """)).fetchall()

    return {
        "db_size_mb": round(db_size_mb, 2),
        "active_connections": active_connections,
        "tables": [
            {"table": r[0], "rows": r[1], "size_mb": r[2]}
            for r in rows
        ],
    }