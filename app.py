"""ShopSafe Lab - Compromised Simulation.

A second, deliberately *suspicious-looking* Flask storefront that mirrors the
legitimate ShopSafe baseline. It exists ONLY for an authorized, local
Watering-Hole Detection Laboratory.

What this application does NOT do:
  * No malware, exploits, shell commands, or code execution.
  * No credential, cookie, or session collection.
  * No requests to external or real malicious infrastructure.
  * No user-controlled redirect destinations.

The suspicious behavior is explicitly simulated, hard-coded, local-only, and
fully disabled when LAB_SIMULATION_ENABLED is false.
"""

import os
import time

from flask import (
    Flask,
    abort,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)

from config import Config, validate_config
from services.access_logger import AccessLogger, get_source_ip
from services.product_service import (
    get_product_by_id,
    get_products_by_category,
    load_products,
)
from shared.dashboard import register_dashboard_routes

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LAB_JS_DIR = os.path.join(BASE_DIR, "static", "lab")


def require_simulation():
    """Abort with 404 when the simulation flag is disabled.

    Returning 404 (rather than 403) keeps lab-test routes from even being
    discoverable when simulation mode is off.
    """
    from flask import current_app
    if not current_app.config.get("LAB_SIMULATION_ENABLED"):
        abort(404)


def create_app(config_object=Config, **overrides):
    app = Flask(
        __name__,
        template_folder=config_object.TEMPLATES_DIR,
        static_folder=os.path.join(BASE_DIR, "static"),
    )
    app.config.from_object(config_object)
    if overrides:
        app.config.update(overrides)

    # Validate configuration. Fail loudly on misconfiguration.
    errors = validate_config(app.config)
    if errors:
        raise ValueError("Invalid configuration: " + "; ".join(errors))

    logger = AccessLogger(
        log_file=app.config["LOG_FILE"],
        simulation_mode=bool(app.config["LAB_SIMULATION_ENABLED"]),
    )
    app.extensions["access_logger"] = logger

    # Load the fictional product dataset once.
    app.config["ALL_PRODUCTS"] = load_products()

    register_request_hooks(app, logger)
    register_storefront_routes(app)
    register_lab_routes(app)
    register_error_handlers(app)
    register_context(app)
    register_dashboard_routes(app)

    # Also feed the centralized CSV log used by the dashboard. Skipped under
    # tests so the real log file is never touched by the test suite.
    if not app.config.get("TESTING"):
        try:
            from shared.web_logger import get_web_logger

            central_logger = get_web_logger("suspicious", base_dir=BASE_DIR)

            @app.after_request
            def _central_log(response):
                try:
                    central_logger.log_request(request, response)
                except Exception:
                    pass
                return response
        except Exception:
            pass

    return app


def register_request_hooks(app, logger):
    @app.before_request
    def _start_timer():
        g.start_time = time.time()

    @app.after_request
    def _log_and_secure(response):
        # Exactly one access-log record per request. Wrapped so that logging
        # problems never break a response.
        try:
            duration_ms = (time.time() - getattr(g, "start_time", time.time())) * 1000.0
            response_bytes = response.calculate_content_length()
            if response_bytes is None:
                response_bytes = 0
            logger.log_request(
                source_ip=get_source_ip(request),
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                referer=request.headers.get("Referer"),
                user_agent=request.headers.get("User-Agent"),
                response_bytes=response_bytes,
                duration_ms=round(duration_ms, 2),
            )
        except Exception:
            pass

        # Sensible baseline security headers.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
        )
        return response


def register_storefront_routes(app):
    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "message": "ShopSafe Lab (compromised simulation) is running",
            "simulation_mode": bool(app.config["LAB_SIMULATION_ENABLED"]),
        }), 200

    @app.route("/")
    def index():
        products = app.config["ALL_PRODUCTS"]
        featured = [p for p in products if p.get("featured")]
        best_selling = sorted(
            products, key=lambda x: x.get("rating", 0), reverse=True
        )[:6]
        return render_template(
            "index.html", featured_products=featured, best_selling=best_selling
        )

    @app.route("/products")
    def products():
        all_products = app.config["ALL_PRODUCTS"]
        query = request.args.get("q", "").strip().lower()
        category = request.args.get("category", "").strip()
        sort = request.args.get("sort", "default").strip()

        filtered = list(all_products)
        if query:
            filtered = [
                p for p in filtered
                if query in p.get("name", "").lower()
                or query in p.get("description", "").lower()
            ]
        if category:
            filtered = [p for p in filtered if p.get("category", "") == category]

        if sort == "price_asc":
            filtered.sort(key=lambda x: x.get("price", 0))
        elif sort == "price_desc":
            filtered.sort(key=lambda x: x.get("price", 0), reverse=True)
        elif sort == "rating_desc":
            filtered.sort(key=lambda x: x.get("rating", 0), reverse=True)

        return render_template(
            "products.html",
            products=filtered,
            query=request.args.get("q", ""),
            category=category,
            sort=sort,
        )

    @app.route("/product/<product_id>")
    def product_detail(product_id):
        product = get_product_by_id(app.config["ALL_PRODUCTS"], product_id)
        if not product:
            return render_template("404.html"), 404
        return render_template("product_detail.html", product=product)

    @app.route("/category/<category_name>")
    def category(category_name):
        found = get_products_by_category(app.config["ALL_PRODUCTS"], category_name)
        return render_template(
            "category.html", category_name=category_name, products=found
        )

    @app.route("/cart")
    def cart():
        return render_template("cart.html", products=app.config["ALL_PRODUCTS"])

    @app.route("/about")
    def about():
        return render_template("about.html")

    @app.route("/contact")
    def contact():
        return render_template("contact.html")

    @app.route("/privacy")
    def privacy():
        return render_template("privacy.html")


def register_lab_routes(app):
    """All routes in this section are gated behind LAB_SIMULATION_ENABLED.

    They are fixed, hard-coded, and local-only. None of them accept a
    user-controlled destination, read the filesystem, execute commands,
    touch credentials, or contact an external host.
    """

    @app.route("/lab-test/")
    def lab_test_index():
        require_simulation()
        return render_template("lab_test.html")

    # --- Scenario A: Unexpected Redirect ---------------------------------
    @app.route("/lab-test/redirect")
    def lab_redirect():
        require_simulation()
        # Hard-coded local destination only. User input is never consulted.
        return redirect(app.config["LAB_REDIRECT_TARGET"], code=302)

    @app.route("/lab-test/redirect-target")
    def lab_redirect_target():
        require_simulation()
        return render_template("redirect_target.html")

    # --- Scenario B: Suspicious URL Path ---------------------------------
    @app.route("/lab-test/admin-test")
    def lab_admin_test():
        require_simulation()
        # Static laboratory response. NOT an admin panel.
        return render_template("admin_test.html"), 200

    # --- Scenario C: Abnormal HTTP Requests ------------------------------
    @app.route("/lab-test/method-check", methods=["GET"])
    def lab_method_check():
        require_simulation()
        # POST/PUT/DELETE to this route yield Flask's normal 405, which is
        # logged. No action is taken based on the HTTP method.
        return render_template("method_check.html", method=request.method), 200

    # --- Scenario D: Repeated Requests -----------------------------------
    @app.route("/lab-test/repeat")
    def lab_repeat():
        require_simulation()
        # Lightweight endpoint used by tests/generate_test_traffic.py.
        return jsonify({"status": "ok", "endpoint": "/lab-test/repeat"}), 200

    # --- Scenario E: Unexpected Resource Origin --------------------------
    @app.route("/lab-test/resource-demo")
    def lab_resource_demo():
        require_simulation()
        return render_template("resource_demo.html")

    @app.route("/lab-test/resources/unapproved.js")
    def lab_unapproved_resource():
        require_simulation()
        # Inert, same-origin laboratory script. See static/lab/unapproved.js.
        return send_from_directory(
            LAB_JS_DIR,
            "unapproved.js",
            mimetype="application/javascript",
        )


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return render_template("405.html"), 405

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("500.html"), 500


def register_context(app):
    @app.context_processor
    def inject_lab_state():
        return {
            "lab_simulation_enabled": bool(app.config["LAB_SIMULATION_ENABLED"]),
            "app_name": "ShopSafe Lab",
        }


# Module-level app for `python app.py` and for test imports that expect `app`.
app = create_app()


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    # use_reloader=False: prevents the reloader from importing the app twice,
    # which avoids duplicate/shadow logger instances.
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=debug_mode,
        use_reloader=False,
    )
