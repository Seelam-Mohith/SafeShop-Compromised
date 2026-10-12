#!/usr/bin/env python3
"""Safe, local-only traffic generator for the ShopSafe Lab simulation.

Targets ONLY http://127.0.0.1:5001 (loopback). It refuses to run against any
non-loopback hostname. It never follows redirects to external destinations and
never performs concurrent floods or denial-of-service behavior.

Usage examples (Windows PowerShell):
    python tests/generate_test_traffic.py redirect
    python tests/generate_test_traffic.py admin-test
    python tests/generate_test_traffic.py method-check
    python tests/generate_test_traffic.py method-check --method POST
    python tests/generate_test_traffic.py repeat --count 20 --delay 0.25
    python tests/generate_test_traffic.py resource
    python tests/generate_test_traffic.py all

The server must already be running, e.g.:
    python app.py
"""

import argparse
import ipaddress
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "http://127.0.0.1:5001"
MAX_REPEAT_REQUESTS = 50
DEFAULT_REPEAT_REQUESTS = 5
DEFAULT_REPEAT_DELAY = 0.25

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent urllib from automatically following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def build_opener():
    return urllib.request.build_opener(NoRedirectHandler)


def is_loopback_base_url(base_url):
    try:
        parsed = urllib.parse.urlparse(base_url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    if host in LOOPBACK_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def send_request(opener, url, method="GET"):
    """Send one request without following redirects. Returns a summary dict."""
    request = urllib.request.Request(url, method=method)
    try:
        with opener.open(request, timeout=5) as response:
            body = response.read()
            return {
                "method": method,
                "url": url,
                "status": response.status,
                "location": response.headers.get("Location", ""),
                "bytes": len(body),
                "error": None,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        return {
            "method": method,
            "url": url,
            "status": exc.code,
            "location": exc.headers.get("Location", "") if exc.headers else "",
            "bytes": len(body),
            "error": None,
        }
    except Exception as exc:  # network-level failure
        return {
            "method": method,
            "url": url,
            "status": None,
            "location": "",
            "bytes": 0,
            "error": str(exc),
        }


def print_summary(results):
    print("\n--- Summary ---")
    for r in results:
        if r["error"]:
            print("  {method} {url} -> ERROR: {error}".format(**r))
        else:
            extra = ""
            if r["location"]:
                extra = " (Location: %s)" % r["location"]
            print("  {method} {url} -> {status} [{bytes} bytes]{extra}".format(
                extra=extra, **r))
    ok = sum(1 for r in results if r["status"] is not None)
    print("  Requests sent: {}  |  Responses received: {}".format(len(results), ok))


def run_redirect(opener, base_url):
    url = base_url + "/lab-test/redirect"
    result = send_request(opener, url)
    # Verify the redirect stays local (defensive; the server hard-codes it).
    if result["location"]:
        location = result["location"]
        if location.startswith("/"):
            passes = True
        else:
            passes = is_loopback_base_url(location)
        if not passes:
            print("  WARNING: server returned a non-local redirect target; not followed.")
    print_summary([result])
    return [result]


def run_simple(opener, base_url, path, method="GET"):
    results = [send_request(opener, base_url + path, method=method)]
    print_summary(results)
    return results


def run_repeat(opener, base_url, count, delay):
    if count < 1:
        count = 1
    if count > MAX_REPEAT_REQUESTS:
        print("  Count {} exceeds max {}; clamping.".format(count, MAX_REPEAT_REQUESTS))
        count = MAX_REPEAT_REQUESTS
    url = base_url + "/lab-test/repeat"
    results = []
    for i in range(count):
        results.append(send_request(opener, url))
        if i < count - 1 and delay > 0:
            time.sleep(delay)
    print_summary(results)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate safe, local-only lab traffic for ShopSafe Lab."
    )
    parser.add_argument(
        "--base-url", default=DEFAULT_BASE_URL,
        help="Loopback base URL (default: %s)" % DEFAULT_BASE_URL,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("redirect", help="Scenario A: request the redirect route.")
    sub.add_parser("admin-test", help="Scenario B: request the suspicious path.")
    mc = sub.add_parser("method-check", help="Scenario C: method recording.")
    mc.add_argument("--method", default="GET", help="HTTP method (default: GET).")
    rp = sub.add_parser("repeat", help="Scenario D: repeated requests.")
    rp.add_argument("--count", type=int, default=DEFAULT_REPEAT_REQUESTS,
                    help="Number of requests (default: %d, max: %d)." % (
                        DEFAULT_REPEAT_REQUESTS, MAX_REPEAT_REQUESTS))
    rp.add_argument("--delay", type=float, default=DEFAULT_REPEAT_DELAY,
                    help="Delay in seconds between requests (default: %.2f)." % DEFAULT_REPEAT_DELAY)
    sub.add_parser("resource", help="Scenario E: request the unapproved resource.")
    sub.add_parser("all", help="Run every scenario once (repeat uses default count).")

    args = parser.parse_args(argv)

    if not is_loopback_base_url(args.base_url):
        print("Refusing to run: '%s' is not a loopback address." % args.base_url)
        print("This utility targets only 127.0.0.1 / localhost / ::1.")
        return 2

    opener = build_opener()

    if args.command == "redirect":
        run_redirect(opener, args.base_url)
    elif args.command == "admin-test":
        run_simple(opener, args.base_url, "/lab-test/admin-test")
    elif args.command == "method-check":
        run_simple(opener, args.base_url, "/lab-test/method-check", method=args.method.upper())
    elif args.command == "repeat":
        run_repeat(opener, args.base_url, args.count, args.delay)
    elif args.command == "resource":
        run_simple(opener, args.base_url, "/lab-test/resources/unapproved.js")
    elif args.command == "all":
        print("== Scenario A: redirect ==")
        run_redirect(opener, args.base_url)
        print("\n== Scenario B: admin-test ==")
        run_simple(opener, args.base_url, "/lab-test/admin-test")
        print("\n== Scenario C: method-check (GET then POST) ==")
        run_simple(opener, args.base_url, "/lab-test/method-check", method="GET")
        run_simple(opener, args.base_url, "/lab-test/method-check", method="POST")
        print("\n== Scenario D: repeat ==")
        run_repeat(opener, args.base_url, DEFAULT_REPEAT_REQUESTS, DEFAULT_REPEAT_DELAY)
        print("\n== Scenario E: resource ==")
        run_simple(opener, args.base_url, "/lab-test/resources/unapproved.js")

    return 0


if __name__ == "__main__":
    sys.exit(main())
