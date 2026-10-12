import json
import os

REQUIRED_FIELDS = [
    "timestamp",
    "source_ip",
    "method",
    "path",
    "status_code",
    "referer",
    "user_agent",
    "response_bytes",
    "duration_ms",
    "simulation_mode",
]


def test_every_request_produces_exactly_one_record(app_and_log):
    app, log_file = app_and_log
    client = app.test_client()

    client.get("/")  # first request may also create the file
    with open(log_file, "r", encoding="utf-8") as f:
        before = len([l for l in f if l.strip()])

    client.get("/products")
    with open(log_file, "r", encoding="utf-8") as f:
        after = len([l for l in f if l.strip()])

    assert after == before + 1


def test_static_asset_requests_are_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/static/css/style.css")
    paths = [r["path"] for r in read_records(log_file)]
    assert "/static/css/style.css" in paths


def test_records_have_required_fields(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/")
    records = read_records(log_file)
    assert records
    record = records[-1]
    for field in REQUIRED_FIELDS:
        assert field in record, "missing field: %s" % field
    assert record["path"] == "/"
    assert record["method"] == "GET"
    assert record["status_code"] == 200
    assert record["source_ip"] in ("127.0.0.1", "::1")


def test_records_are_valid_jsonl(app_and_log):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/")
    client.get("/products")
    client.get("/static/js/cart.js")
    with open(log_file, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) >= 3
    for line in lines:
        obj = json.loads(line)
        assert isinstance(obj, dict)


def test_query_string_values_are_not_logged(app_and_log):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/products?q=supersecretvalue123&token=abc123")
    with open(log_file, "r", encoding="utf-8") as f:
        raw = f.read()
    assert "supersecretvalue123" not in raw
    assert "abc123" not in raw
    records = [json.loads(l) for l in raw.splitlines() if l.strip()]
    assert records[-1]["path"] == "/products"


def test_secrets_and_bodies_are_not_logged(app_and_log):
    app, log_file = app_and_log
    client = app.test_client()
    client.post(
        "/lab-test/method-check",
        data="password=hunter2&token=topsecretvalue",
        headers={
            "Cookie": "session=verysecretcookie",
            "Authorization": "Bearer verysecrettoken",
        },
        content_type="application/x-www-form-urlencoded",
    )
    with open(log_file, "r", encoding="utf-8") as f:
        raw = f.read().lower()
    for forbidden in (
        "hunter2",
        "topsecretvalue",
        "verysecretcookie",
        "verysecrettoken",
        "password",
        "authorization",
        "cookie",
    ):
        assert forbidden not in raw, "log leaked: %s" % forbidden


def test_redirect_scenario_is_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/lab-test/redirect")
    record = read_records(log_file)[-1]
    assert record["path"] == "/lab-test/redirect"
    assert record["status_code"] == 302


def test_suspicious_path_scenario_is_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/lab-test/admin-test")
    record = read_records(log_file)[-1]
    assert record["path"] == "/lab-test/admin-test"
    assert record["status_code"] == 200


def test_abnormal_method_scenario_is_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.post("/lab-test/method-check")
    record = read_records(log_file)[-1]
    assert record["method"] == "POST"
    assert record["path"] == "/lab-test/method-check"
    assert record["status_code"] == 405


def test_repeated_requests_are_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    for _ in range(25):
        client.get("/lab-test/repeat")
    records = [r for r in read_records(log_file) if r["path"] == "/lab-test/repeat"]
    assert len(records) == 25
    assert all(r["status_code"] == 200 for r in records)


def test_resource_scenario_is_logged(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/lab-test/resources/unapproved.js")
    record = read_records(log_file)[-1]
    assert record["path"] == "/lab-test/resources/unapproved.js"
    assert record["status_code"] == 200


def test_simulation_mode_field_reflects_configuration(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/")
    assert read_records(log_file)[-1]["simulation_mode"] is True


def test_disabled_simulation_logs_404_with_false_flag(make_app, read_records):
    app = make_app(simulation=False)
    log_file = app._test_log_file
    client = app.test_client()
    client.get("/lab-test/redirect")
    record = read_records(log_file)[-1]
    assert record["path"] == "/lab-test/redirect"
    assert record["status_code"] == 404
    assert record["simulation_mode"] is False


def test_log_file_is_appended_not_overwritten(app_and_log, read_records):
    app, log_file = app_and_log
    client = app.test_client()
    client.get("/")
    first = len(read_records(log_file))
    client.get("/about")
    second = len(read_records(log_file))
    assert second == first + 1
