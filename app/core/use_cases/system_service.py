import psutil
from firebase_admin import auth
from sqlalchemy.orm import Session
from collections import deque
from datetime import datetime
from app.infrastructure.database.repositories.system_repository import get_db_stats as _get_db_stats

_history: deque = deque(maxlen=50)


def record_snapshot():
    snapshot = get_server_stats()
    snapshot["captured_at"] = datetime.utcnow().isoformat()
    _history.append(snapshot)


def get_server_history() -> list:
    return list(_history)


def get_server_stats() -> dict:
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "cpu_percent": cpu,
        "ram_used_gb": round(ram.used / 1024**3, 2),
        "ram_total_gb": round(ram.total / 1024**3, 2),
        "ram_percent": ram.percent,
        "disk_used_gb": round(disk.used / 1024**3, 2),
        "disk_total_gb": round(disk.total / 1024**3, 2),
        "disk_percent": disk.percent,
    }


def get_db_stats(db: Session) -> dict:
    return _get_db_stats(db)


def get_firebase_user_stats() -> dict:
    all_users = []
    page = auth.list_users()
    while page:
        for u in page.users:
            claims = u.custom_claims or {}
            all_users.append({
                "role": claims.get("role"),
                "status": claims.get("status"),
                "disabled": u.disabled,
                "last_sign_in": u.user_metadata.last_sign_in_timestamp,
            })
        page = page.get_next_page()

    by_role, by_status, never_logged_in = {}, {}, 0
    for u in all_users:
        role = u["role"] or "unknown"
        status = u["status"] or "unknown"
        by_role[role] = by_role.get(role, 0) + 1
        by_status[status] = by_status.get(status, 0) + 1
        if not u["last_sign_in"]:
            never_logged_in += 1

    return {
        "total_users": len(all_users),
        "disabled_users": sum(1 for u in all_users if u["disabled"]),
        "never_logged_in": never_logged_in,
        "by_role": [{"role": k, "count": v} for k, v in by_role.items()],
        "by_status": [{"status": k, "count": v} for k, v in by_status.items()],
    }