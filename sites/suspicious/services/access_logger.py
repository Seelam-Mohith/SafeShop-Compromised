"""Structured JSON Lines access logging for the simulated compromised site.

Design goals:
  * Exactly one record per HTTP request (including static assets and errors).
  * Append-only; never overwrite existing records.
  * Never log cookies, authorization headers, passwords, session tokens or
    request bodies. Only the URL *path* is recorded (never the query string).
  * The client IP is taken from the socket peer, not from client-supplied
    forwarding headers, which are not trustworthy.
"""

import json
import os
from datetime import datetime, timezone
from threading import Lock

# Process-wide lock so concurrent workers do not interleave partial lines.
_log_lock = Lock()


class AccessLogger:
    def __init__(self, log_file=None, simulation_mode=False):
        self.log_file = log_file or os.path.join(
            "logs", "compromised_access.jsonl"
        )
        self.simulation_mode = bool(simulation_mode)
        self._ensure_log_dir()

    def _ensure_log_dir(self):
        log_dir = os.path.dirname(os.path.abspath(self.log_file))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log_request(self, source_ip, method, path, status_code, referer=None,
                    user_agent=None, response_bytes=None, duration_ms=None):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        record = {
            "timestamp": timestamp,
            "source_ip": source_ip,
            "method": method,
            "path": path,
            "status_code": status_code,
            "referer": referer or "",
            "user_agent": user_agent or "",
            "response_bytes": response_bytes if response_bytes is not None else 0,
            "duration_ms": duration_ms if duration_ms is not None else 0.0,
            "simulation_mode": self.simulation_mode,
        }
        payload = json.dumps(record, ensure_ascii=True, sort_keys=False)
        with _log_lock:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(payload + "\n")


def get_source_ip(request):
    """Return the peer socket address. Forwarding headers are ignored."""
    return request.remote_addr or "127.0.0.1"
