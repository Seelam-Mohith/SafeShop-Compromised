#!/usr/bin/env python3
# Simple rule-based detection engine for Watering-Hole lab

import csv
import os
from collections import defaultdict, deque
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.dirname(__file__))
LOG_FILE = os.path.join(ROOT, "logs", "web_logs.csv")
REPORT_FILE = os.path.join(ROOT, "reports", "detection_report.csv")

REPORT_FIELDS = [
    "timestamp",
    "site_identifier",
    "http_method",
    "requested_path",
    "http_status_code",
    "client_ip_address",
    "request_id",
    "indicator_type",
    "severity",
    "details",
]

SUSPICIOUS_PATHS = [
    "/lab-test/admin-test",
    "/lab-test/method-check",
]

UNEXPECTED_RESOURCES = [
    "/lab-test/resources/unapproved.js",
]


def read_logs():
    if not os.path.exists(LOG_FILE):
        print(f"[detect] Log file not found: {LOG_FILE}")
        return []
    logs = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            logs.append(row)
    return logs


def detect(logs):
    alerts = []
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)

    # Track for repeated requests
    path_ip_window = defaultdict(deque)  # (path, ip) -> list of timestamps

    for log in logs:
        ts_str = log.get("timestamp", "")
        path = log.get("requested_path", "")
        method = log.get("http_method", "")
        status = log.get("http_status_code", "")
        site = log.get("site_identifier", "")
        ip = log.get("client_ip_address", "")
        req_id = log.get("request_id", "")

        try:
            status_int = int(status)
        except Exception:
            status_int = 0

        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            ts = datetime.utcnow()

        # 1) Unexpected Redirects
        if status_int == 302 and path.startswith("/lab-test/redirect"):
            alerts.append({
                "timestamp": ts_str,
                "site_identifier": site,
                "http_method": method,
                "requested_path": path,
                "http_status_code": status,
                "client_ip_address": ip,
                "request_id": req_id,
                "indicator_type": "unexpected_redirect",
                "severity": "medium",
                "details": "HTTP 302 redirect observed to local test target",
            })

        # 2) Suspicious URL Paths
        if path in SUSPICIOUS_PATHS:
            alerts.append({
                "timestamp": ts_str,
                "site_identifier": site,
                "http_method": method,
                "requested_path": path,
                "http_status_code": status,
                "client_ip_address": ip,
                "request_id": req_id,
                "indicator_type": "suspicious_path",
                "severity": "medium",
                "details": f"Access to lab test path {path}",
            })

        # 3) Abnormal HTTP Methods
        if path == "/lab-test/method-check" and method != "GET":
            alerts.append({
                "timestamp": ts_str,
                "site_identifier": site,
                "http_method": method,
                "requested_path": path,
                "http_status_code": status,
                "client_ip_address": ip,
                "request_id": req_id,
                "indicator_type": "abnormal_http_method",
                "severity": "medium",
                "details": f"Non-GET method {method} to GET-only test route (responded {status_int})",
            })
        elif method not in ("GET", "POST", "HEAD", "OPTIONS") and method:
            alerts.append({
                "timestamp": ts_str,
                "site_identifier": site,
                "http_method": method,
                "requested_path": path,
                "http_status_code": status,
                "client_ip_address": ip,
                "request_id": req_id,
                "indicator_type": "abnormal_http_method",
                "severity": "low",
                "details": f"Uncommon HTTP method {method}",
            })

        # 5) Unexpected Resource Origin/Path
        if path in UNEXPECTED_RESOURCES:
            alerts.append({
                "timestamp": ts_str,
                "site_identifier": site,
                "http_method": method,
                "requested_path": path,
                "http_status_code": status,
                "client_ip_address": ip,
                "request_id": req_id,
                "indicator_type": "unexpected_resource",
                "severity": "medium",
                "details": "Request to local unapproved resource (path-level indicator)",
            })

        # Track for repeated requests
        key = (path, ip)
        dq = path_ip_window[key]
        dq.append(ts)
        # Keep last 60 seconds
        cutoff = ts - timedelta(seconds=60)
        while dq and dq[0] < cutoff:
            dq.popleft()

    # 4) Repeated Requests - flag if > 10 requests in 60s to same path from same IP
    for (path, ip), dq in path_ip_window.items():
        if len(dq) >= 10:
            # Create one alert for the pattern
            alerts.append({
                "timestamp": dq[-1].strftime("%Y-%m-%dT%H:%M:%SZ"),
                "site_identifier": "",
                "http_method": "",
                "requested_path": path,
                "http_status_code": "",
                "client_ip_address": ip,
                "request_id": "",
                "indicator_type": "repeated_requests",
                "severity": "high",
                "details": f"{len(dq)} requests to {path} from {ip} within 60 seconds",
            })

    # Write report
    with open(REPORT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        for alert in alerts:
            writer.writerow(alert)

    print(f"[detect] Analyzed {len(logs)} log entries")
    print(f"[detect] Generated {len(alerts)} alerts")
    print(f"[detect] Report written to {REPORT_FILE}")
    return alerts


if __name__ == "__main__":
    logs = read_logs()
    detect(logs)
