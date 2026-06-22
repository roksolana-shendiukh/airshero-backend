from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension
)
from google.oauth2 import service_account
import json

PROPERTY_ID = "525204249"  
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

def _get_client():
    credentials = service_account.Credentials.from_service_account_file(
        "serviceAccountKey.json",  
        scopes=SCOPES
    )
    return BetaAnalyticsDataClient(credentials=credentials)


def get_active_users() -> dict:
    client = _get_client()
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
        ],
        dimensions=[Dimension(name="date")]
    )
    response = client.run_report(request)
    
    rows = []
    for row in response.rows:
        rows.append({
            "date": row.dimension_values[0].value,
            "activeUsers": int(row.metric_values[0].value),
            "newUsers": int(row.metric_values[1].value),
            "sessions": int(row.metric_values[2].value),
        })
    return {"data": sorted(rows, key=lambda x: x["date"])}


def get_top_events() -> dict:
    client = _get_client()
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        metrics=[Metric(name="eventCount")],
        dimensions=[Dimension(name="eventName")]
    )
    response = client.run_report(request)
    
    rows = [
        {
            "event": row.dimension_values[0].value,
            "count": int(row.metric_values[0].value)
        }
        for row in response.rows
    ]
    return {"data": sorted(rows, key=lambda x: x["count"], reverse=True)[:20]}


def get_screen_views() -> dict:
    client = _get_client()
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date="7daysAgo", end_date="today")],
        metrics=[Metric(name="screenPageViews"), Metric(name="activeUsers")],
        dimensions=[Dimension(name="unifiedScreenName")]
    )
    response = client.run_report(request)
    
    rows = [
        {
            "screen": row.dimension_values[0].value,
            "views": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        }
        for row in response.rows
    ]
    return {"data": sorted(rows, key=lambda x: x["views"], reverse=True)}