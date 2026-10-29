"""Read-only lab dashboard data and routes.

The dashboard surfaces the centralized web log (``logs/web_logs.csv``) and the
detection engine output (``reports/detection_report.csv``). It never modifies
those files except when the operator explicitly asks to re-run detection from
the dashboard.
"""

import csv
import os
import sys
from collections import Counter

from flask import abort, current_app, redirect, render_template, url_for

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
WEB_LOG_FILE = os.path.join(REPO_ROOT, "logs", "web_logs.csv")
REPORT_FILE = os.path.join(REPO_ROOT, "reports", "detection_report.csv")


def _read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _require_simulation():
    if not current_app.config.get("LAB_SIMULATION_ENABLED"):
        abort(404)


def run_detection():
    """Run the rule-based detector over the centralized web log."""
    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)
    import detect as detect_module

    return detect_module.detect(detect_module.read_logs())


def load_dashboard_data():
    """Load logs and report rows, newest first, plus summary statistics."""
    web_logs = _read_csv(WEB_LOG_FILE)
    report = _read_csv(REPORT_FILE)

    web_logs.reverse()
    report.reverse()

    site_counts = Counter(
        (row.get("site_identifier") or "unknown") for row in web_logs
    )
    method_counts = Counter(
        (row.get("http_method") or "unknown") for row in web_logs
    )
    severity_counts = Counter(
        ((row.get("severity") or "unknown").lower()) for row in report
    )
    attack_counts = Counter(
        (row.get("indicator_type") or "unknown") for row in report
    )

    summary = {
        "total_requests": len(web_logs),
        "legitimate_requests": site_counts.get("legitimate", 0),
        "suspicious_requests": site_counts.get("suspicious", 0),
        "unique_ips": len({
            row.get("client_ip_address")
            for row in web_logs
            if row.get("client_ip_address")
        }),
        "unique_paths": len({
            row.get("requested_path")
            for row in web_logs
            if row.get("requested_path")
        }),
        "total_alerts": len(report),
        "high_alerts": severity_counts.get("high", 0),
        "medium_alerts": severity_counts.get("medium", 0),
        "low_alerts": severity_counts.get("low", 0),
    }

    log_sites = sorted({row.get("site_identifier") for row in web_logs if row.get("site_identifier")})
    log_methods = sorted({row.get("http_method") for row in web_logs if row.get("http_method")})

    return {
        "web_logs": web_logs,
        "report": report,
        "summary": summary,
        "site_counts": site_counts.most_common(),
        "method_counts": method_counts.most_common(),
        "severity_counts": severity_counts.most_common(),
        "attack_counts": attack_counts.most_common(),
        "log_sites": log_sites,
        "log_methods": log_methods,
        "web_log_file": os.path.relpath(WEB_LOG_FILE, REPO_ROOT),
        "report_file": os.path.relpath(REPORT_FILE, REPO_ROOT),
    }


def register_dashboard_routes(app):
    @app.route("/dashboard")
    def dashboard():
        _require_simulation()
        return render_template("dashboard.html", **load_dashboard_data())

    @app.route("/dashboard/detect", methods=["POST"])
    def dashboard_detect():
        _require_simulation()
        try:
            run_detection()
        except Exception as exc:  # never let a detector problem break the UI
            current_app.logger.warning("Dashboard detection run failed: %s", exc)
            return redirect(url_for("dashboard", error="1"))
        return redirect(url_for("dashboard", updated="1"))
