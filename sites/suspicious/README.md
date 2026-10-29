# ShopSafe Lab — Compromised Simulation

ShopSafe Lab is the **simulated, deliberately-suspicious counterpart** of the
legitimate ShopSafe e-commerce website. It is part of the academic
**Watering-Hole Detection Laboratory**. It looks and behaves almost identically
to the legitimate baseline, but exposes a set of clearly-labelled **test
routes** that generate controlled security evidence for a future Python
detection engine to analyze.

> **Authorized, local-only simulation.** This application does not deploy
> malware, exploit vulnerabilities, steal credentials, execute shell commands,
> or contact any real external or malicious infrastructure. Every "suspicious"
> behavior is hard-coded, clearly labelled, and restricted to `127.0.0.1`.

---

## 1. Purpose

- Provide a second storefront that mirrors the legitimate ShopSafe design and
  fictional product data.
- Produce **structured JSON Lines access logs** that can be compared with the
  legitimate website's logs (`logs/legitimate_access.jsonl`).
- Reproduce five observable, configurable indicators so a separate detection
  engine can be tested (redirects, suspicious paths, abnormal methods,
  repeated requests, unexpected resource paths).

## 2. Difference from the legitimate baseline

| Aspect            | Legitimate ShopSafe                  | ShopSafe Lab (this app)               |
|-------------------|--------------------------------------|---------------------------------------|
| Port              | `http://127.0.0.1:5000`              | `http://127.0.0.1:5001`               |
| Log file          | `logs/legitimate_access.jsonl`       | `logs/compromised_access.jsonl`       |
| Lab banner        | none                                 | "Cybersecurity Lab — Simulated Environment" |
| Lab test routes   | none                                 | enabled by `LAB_SIMULATION_ENABLED`   |
| Storefront        | normal                               | same visual design, same fictional data |
| Log field         | —                                    | adds `simulation_mode`                |

The two applications are **fully isolated**. This project does not import from
or modify the legitimate application, and it never writes to the legitimate
log file.

## 3. The five test scenarios

All scenario routes live under `/lab-test/` and are **unavailable (404)** when
`LAB_SIMULATION_ENABLED` is disabled.

### Scenario A — Unexpected Redirect
- Route: `GET /lab-test/redirect`
- Behavior: returns **HTTP 302** to a **fixed, hard-coded local page**
  (`/lab-test/redirect-target`). The destination is never taken from user
  input and is never external.
- Expected evidence: a `302` record with `path = /lab-test/redirect`, plus the
  matching HTTP redirect in Wireshark if captured.
- Note for the detector: treat this as a **configured test indicator**, not a
  reason to flag every 302 as malicious.

### Scenario B — Suspicious URL Path
- Route: `GET /lab-test/admin-test`
- Behavior: returns a static laboratory page with HTTP **200**. It is **not** an
  admin panel. No filesystem access, no credentials, no privilege, no
  environment variables, no command execution.
- Expected evidence: a request path matching a predefined suspicious pattern.

### Scenario C — Abnormal HTTP Requests
- Route: `GET /lab-test/method-check` (accepts `GET` only)
- Behavior: unsupported methods (e.g. `POST`) yield the framework's normal
  **405** response, which is still logged. No action is taken based on method.
- Expected evidence: method + status recorded in the access log.

### Scenario D — Repeated Requests
- Route: `GET /lab-test/repeat`
- Behavior: a lightweight endpoint. Use the safe utility to send a configurable
  number of requests (default **5**, hard maximum **50**) with a short delay.
- Expected evidence: many records for `/lab-test/repeat` within a time window,
  suitable for testing a threshold such as "> 20 requests in 10 seconds".

### Scenario E — Unexpected Resource Origin
- Route: `GET /lab-test/resources/unapproved.js`
- Behavior: serves an **inert, local** JavaScript file. It only writes a
  visible lab marker and a harmless console message. It performs no
  fingerprinting, no storage/credential access, and no network requests.
- Demo page: `/lab-test/resource-demo`.
- **Important distinction:** because this resource is served from the **same
  application origin**, this is a **path-level** indicator only. A different
  path is **not** proof of a cross-origin resource. Do not claim external
  origin from this alone.

## 4. Project structure

```text
SafeShop-Compromised/
├── app.py                     # Flask app factory + storefront + lab routes
├── config.py                  # configuration + validation
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   └── products.json          # same fictional dataset as the baseline
├── logs/
│   ├── .gitkeep
│   └── compromised_access.jsonl   # generated at runtime
├── services/
│   ├── __init__.py
│   ├── access_logger.py       # JSONL access logger (+ simulation_mode)
│   └── product_service.py
├── templates/
│   └── compromised/
│       ├── base.html
│       ├── index.html
│       ├── products.html
│       ├── product_detail.html
│       ├── category.html
│       ├── cart.html
│       ├── about.html
│       ├── contact.html
│       ├── privacy.html
│       ├── 404.html / 405.html / 500.html
│       ├── lab_test.html
│       ├── redirect_target.html
│       ├── admin_test.html
│       ├── method_check.html
│       └── resource_demo.html
├── static/
│   ├── css/style.css
│   ├── js/main.js, cart.js
│   ├── images/*.svg
│   └── lab/unapproved.js      # inert lab resource
└── tests/
    ├── generate_test_traffic.py
    ├── conftest.py
    ├── test_compromised_routes.py
    └── test_compromised_logging.py
```

## 5. Setup (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 6. Running the two applications independently

They are separate processes in separate folders and use different ports and
log files.

Legitimate baseline (in the original `SafeShop` folder):

```powershell
python app.py
# -> http://127.0.0.1:5000  -> logs\legitimate_access.jsonl
```

Simulated compromised site (in this folder):

```powershell
python app.py
# -> http://127.0.0.1:5001  -> logs\compromised_access.jsonl
```

## 7. Enable / disable simulation mode

Simulation mode is controlled by the `LAB_SIMULATION_ENABLED` flag
(default: `true`). Accepted values: `1/true/yes/on` and `0/false/no/off`
(case-insensitive). An invalid value raises a configuration error at startup.

Windows PowerShell (enable explicitly — this is the default):

```powershell
$env:LAB_SIMULATION_ENABLED = "true"
python app.py
```

Windows PowerShell (disable — lab-test routes then return 404):

```powershell
$env:LAB_SIMULATION_ENABLED = "false"
python app.py
```

Command Prompt (cmd.exe):

```bat
set LAB_SIMULATION_ENABLED=false
python app.py
```

Environment-variable syntax differs across operating systems; use the form
appropriate to your shell. When disabled:

- `/lab-test/*` routes return **404** and are effectively non-existent.
- The storefront continues to work normally.
- The lab banner is hidden.
- Log records still carry `"simulation_mode": false`.

Optional overrides:

```powershell
$env:LOG_FILE = "C:\temp\lab_access.jsonl"   # custom log path
$env:PORT = "5001"                            # custom port
$env:HOST = "127.0.0.1"                       # keep loopback-only
```

## 8. Generating each scenario

Start the app first, then use the safe generator (it targets **only**
loopback and refuses any non-loopback host).

```powershell
python tests/generate_test_traffic.py redirect
python tests/generate_test_traffic.py admin-test
python tests/generate_test_traffic.py method-check
python tests/generate_test_traffic.py method-check --method POST
python tests/generate_test_traffic.py repeat --count 20 --delay 0.25
python tests/generate_test_traffic.py resource
python tests/generate_test_traffic.py all
```

`--count` is capped at **50**. There is no concurrency and no flooding.

## 9. Inspecting logs

```powershell
Get-Content .\logs\compromised_access.jsonl -Tail 10
```

Example record (illustrative only — real records are produced by real local
requests):

```json
{"timestamp":"2026-01-01T12:00:00Z","source_ip":"127.0.0.1","method":"GET","path":"/lab-test/redirect","status_code":302,"referer":"","user_agent":"python-urllib/3.11","response_bytes":0,"duration_ms":1.42,"simulation_mode":true}
```

Expected detection patterns (paths/values are predictable):

| Scenario            | Path                                  | Key evidence        |
|---------------------|---------------------------------------|---------------------|
| A Redirect          | `/lab-test/redirect`                  | `status_code = 302` |
| B Suspicious path   | `/lab-test/admin-test`                | matching path       |
| C Abnormal method   | `/lab-test/method-check`              | unusual method / `405` |
| D Repeated requests | `/lab-test/repeat`                    | many records in a window |
| E Resource origin   | `/lab-test/resources/unapproved.js`   | unapproved resource path |

### Log record fields

`timestamp` (UTC ISO 8601), `source_ip`, `method`, `path`, `status_code`,
`referer`, `user_agent`, `response_bytes`, `duration_ms`, `simulation_mode`.

The logger **never** records cookies, authorization headers, passwords, session
tokens, request bodies, or query-string values. The client IP comes from the
socket peer; client-supplied forwarding headers are ignored.

## 10. Validating traffic with Wireshark

1. Install Wireshark and select the **Loopback** interface
   (`Adapter for loopback traffic capture`, or `\Device\NPF_Loopback`). On
   Windows this requires the Npcap loopback adapter.
2. Apply a capture filter: `tcp port 5001`.
3. Run a scenario, e.g.
   `python tests/generate_test_traffic.py redirect`.
4. Observe the `HTTP/1.1 302 Found` response and its `Location` header pointing
   at the local `/lab-test/redirect-target`.
5. For Scenario D, observe the burst of requests to `/lab-test/repeat`.

## 11. Running the automated tests

```powershell
pytest
```

Focused runs:

```powershell
pytest tests/test_compromised_routes.py
pytest tests/test_compromised_logging.py
```

Tests use temporary log files and never send traffic outside loopback.

## 12. Security measures implemented

- Localhost-only binding by default (`127.0.0.1`).
- Single explicit simulation switch; lab routes 404 when disabled.
- Fixed, hard-coded internal redirect destination; no user-controlled target.
- No shell commands, code execution, or filesystem access from lab routes.
- No real login, payment, or credential collection; checkout is a demo alert.
- No external destinations in any simulated behavior.
- No CORS configuration is added.
- Sensible security headers (CSP, `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`).
- Request/bodies/secrets excluded from logs; proper HTTP status codes.

## 13. Known limitations

- **Path vs. origin (Scenario E):** the unapproved resource is served by the
  **same origin**. This is a path-level indicator, not proof of cross-origin
  loading.
- Scenario D is sequential by design (no concurrency) to avoid any
  denial-of-service behavior.
- The storefront is demonstrative: client-side cart, no payments, no accounts.
- This app uses the Flask development server; it is not intended for
  production or public exposure.
- Redirects are only visible in Wireshark when captured on loopback with the
  appropriate adapter installed.

## 14. Notes

- Debug mode is off by default and the auto-reloader is disabled to prevent
  duplicate logging.
- Logs are written **only** to `logs/compromised_access.jsonl` (or `LOG_FILE`).
- No external resources, analytics, or tracking.
