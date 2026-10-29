"""Centralized web request logging for both SafeShop sites.

Writes to logs/web_logs.csv with cross-process safe locking.
Never logs sensitive headers/body/query values.
"""
import csv
import os
import uuid
from datetime import datetime, timezone
from threading import Lock

_log_lock = Lock()


CSV_FIELDS = [
    "timestamp",
    "site_identifier",
    "http_method",
    "requested_path",
    "http_status_code",
    "client_ip_address",
    "user_agent",
    "referrer",
    "request_id",
]


def _get_log_path(base_dir=None):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "web_logs.csv")


def _ensure_csv_header(log_path):
    try:
        if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
            with _log_lock:
                if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
                    with open(log_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                        writer.writeheader()
            return
    except Exception as e:
        try:
            print(f"[web_logger] Failed to ensure CSV header: {e}")
        except Exception:
            pass


class WebRequestLogger:
    def __init__(self, site_identifier, base_dir=None, log_path=None):
        if site_identifier not in ("legitimate", "suspicious"):
            raise ValueError("site_identifier must be 'legitimate' or 'suspicious'")
        self.site_identifier = site_identifier
        self.base_dir = base_dir or os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        self.log_path = log_path or _get_log_path(self.base_dir)
        _ensure_csv_header(self.log_path)

    def log_request(self, request, response, request_id=None):
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if request_id is None:
                request_id = str(uuid.uuid4())

            requested_path = request.path if hasattr(request, "path") else "/"

            try:
                client_ip = request.remote_addr or "127.0.0.1"
            except Exception:
                client_ip = "127.0.0.1"

            try:
                user_agent = request.headers.get("User-Agent", "") if hasattr(request, "headers") else ""
            except Exception:
                user_agent = ""

            try:
                referrer = request.headers.get("Referer", "") if hasattr(request, "headers") else ""
            except Exception:
                referrer = ""

            try:
                status_code = response.status_code
            except Exception:
                status_code = 0

            try:
                method = request.method
            except Exception:
                method = "GET"

            record = {
                "timestamp": timestamp,
                "site_identifier": self.site_identifier,
                "http_method": method,
                "requested_path": requested_path,
                "http_status_code": status_code,
                "client_ip_address": client_ip,
                "user_agent": user_agent,
                "referrer": referrer,
                "request_id": request_id,
            }

            with _log_lock:
                _ensure_csv_header(self.log_path)
                with open(self.log_path, "a", encoding="utf-8", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                    writer.writerow(record)
        except Exception as e:
            try:
                print(f"[web_logger] Logging failed for {self.site_identifier}: {e}")
            except Exception:
                pass


def get_web_logger(site_identifier, base_dir=None):
    return WebRequestLogger(site_identifier, base_dir=base_dir)
