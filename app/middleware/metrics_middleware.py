import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from starlette.middleware.base import BaseHTTPMiddleware

_requests = deque(maxlen=5000)
_start_time = datetime.utcnow()

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        _requests.append({
            "timestamp": datetime.utcnow(),
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        })
        return response

def get_api_stats() -> dict:
    now = datetime.utcnow()
    w1h  = now - timedelta(hours=1)
    w24h = now - timedelta(hours=24)

    r1h  = [r for r in _requests if r["timestamp"] >= w1h]
    r24h = [r for r in _requests if r["timestamp"] >= w24h]

    def avg_ms(reqs):
        return round(sum(r["duration_ms"] for r in reqs) / len(reqs), 1) if reqs else 0

    def error_rate(reqs):
        if not reqs: return 0.0
        return round(sum(1 for r in reqs if r["status_code"] >= 500) / len(reqs) * 100, 1)

    ep = defaultdict(list)
    for r in r24h:
        ep[r["path"]].append(r["duration_ms"])
    slow = sorted([
        {"path": p, "avg_ms": round(sum(t)/len(t), 1), "calls": len(t)}
        for p, t in ep.items()
    ], key=lambda x: x["avg_ms"], reverse=True)[:10]

    err = defaultdict(int)
    for r in r24h:
        if r["status_code"] >= 400:
            err[f"{r['status_code']} {r['path']}"] += 1
    top_errors = sorted(
        [{"label": k, "count": v} for k, v in err.items()],
        key=lambda x: x["count"], reverse=True
    )[:10]

    hourly = defaultdict(lambda: {"requests": 0, "errors": 0})
    for r in r24h:
        h = r["timestamp"].strftime("%H:00")
        hourly[h]["requests"] += 1
        if r["status_code"] >= 500:
            hourly[h]["errors"] += 1

    uptime_sec = int((now - _start_time).total_seconds())

    return {
        "uptime_seconds": uptime_sec,
        "avg_response_ms_1h": avg_ms(r1h),
        "avg_response_ms_24h": avg_ms(r24h),
        "error_rate_1h": error_rate(r1h),
        "error_rate_24h": error_rate(r24h),
        "rps": round(len(r1h) / 3600, 4),
        "total_requests_24h": len(r24h),
        "slow_endpoints": slow,
        "top_errors": top_errors,
        "hourly_activity": [{"hour": h, **v} for h, v in sorted(hourly.items())],
    }