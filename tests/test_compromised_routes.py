import pytest

from tests.generate_test_traffic import is_loopback_base_url


def test_homepage_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200


def test_products_listing_returns_200(client):
    response = client.get("/products")
    assert response.status_code == 200


def test_product_search_and_filter(client):
    assert client.get("/products?q=headphones").status_code == 200
    assert client.get("/products?category=Books&sort=price_asc").status_code == 200


def test_valid_product_detail(client):
    assert client.get("/product/1").status_code == 200


def test_unknown_product_returns_404(client):
    assert client.get("/product/9999").status_code == 404


def test_category_page(client):
    assert client.get("/category/Electronics").status_code == 200


def test_about_privacy_contact_cart(client):
    for path in ("/about", "/privacy", "/contact", "/cart"):
        assert client.get(path).status_code == 200


def test_unknown_route_returns_404(client):
    response = client.get("/definitely-not-a-route")
    assert response.status_code == 404


def test_health_reports_simulation_mode(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["simulation_mode"] is True


def test_lab_index_available_when_simulation_enabled(client):
    assert client.get("/lab-test/").status_code == 200


# --- Scenario A: redirect ----------------------------------------------------

def test_redirect_returns_302_to_fixed_local_target(client):
    response = client.get("/lab-test/redirect")
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert location.endswith("/lab-test/redirect-target")
    assert "http://" not in location and "https://" not in location


def test_redirect_target_is_reachable(client):
    assert client.get("/lab-test/redirect-target").status_code == 200


# --- Scenario B: suspicious path --------------------------------------------

def test_admin_test_path_returns_static_200(client):
    response = client.get("/lab-test/admin-test")
    assert response.status_code == 200


# --- Scenario C: abnormal methods -------------------------------------------

def test_method_check_get_ok(client):
    assert client.get("/lab-test/method-check").status_code == 200


def test_method_check_unsupported_method_returns_405(client):
    assert client.post("/lab-test/method-check").status_code == 405


# --- Scenario D: repeated requests ------------------------------------------

def test_repeat_endpoint_ok(client):
    assert client.get("/lab-test/repeat").status_code == 200


# --- Scenario E: resource ----------------------------------------------------

def test_unapproved_resource_served_as_local_javascript(client):
    response = client.get("/lab-test/resources/unapproved.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("Content-Type", "")
    body = response.get_data(as_text=True).lower()
    assert "lab-resource-marker" in body
    # Inert: no external networking, no storage/credential access.
    assert "xmlhttprequest" not in body
    assert "fetch(" not in body
    assert "localstorage" not in body
    assert "document.cookie" not in body
    assert "http://" not in body and "https://" not in body


def test_resource_demo_page_loads(client):
    assert client.get("/lab-test/resource-demo").status_code == 200


# --- Simulation disabled -----------------------------------------------------

LAB_PATHS = [
    "/lab-test/",
    "/lab-test/redirect",
    "/lab-test/redirect-target",
    "/lab-test/admin-test",
    "/lab-test/method-check",
    "/lab-test/repeat",
    "/lab-test/resource-demo",
    "/lab-test/resources/unapproved.js",
]


@pytest.mark.parametrize("path", LAB_PATHS)
def test_lab_routes_unavailable_when_simulation_disabled(make_app, path):
    app = make_app(simulation=False)
    client = app.test_client()
    assert client.get(path).status_code == 404


def test_storefront_still_works_when_simulation_disabled(make_app):
    app = make_app(simulation=False)
    client = app.test_client()
    assert client.get("/").status_code == 200
    assert client.get("/products").status_code == 200
    health = client.get("/health").get_json()
    assert health["simulation_mode"] is False


# --- Traffic generator safety ------------------------------------------------

def test_traffic_generator_accepts_only_loopback():
    assert is_loopback_base_url("http://127.0.0.1:5001")
    assert is_loopback_base_url("http://localhost:5001")
    assert is_loopback_base_url("http://[::1]:5001")
    assert not is_loopback_base_url("http://example.com:5001")
    assert not is_loopback_base_url("http://192.168.1.10:5001")
    assert not is_loopback_base_url("ftp://127.0.0.1")
