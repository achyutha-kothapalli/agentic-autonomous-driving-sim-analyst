from pathlib import Path

from app.main import STATIC_DIR, app, index


def test_root_route_is_registered():
    routes = {route.path for route in app.routes}

    assert "/" in routes


def test_dashboard_files_exist():
    assert (STATIC_DIR / "index.html").exists()
    assert (STATIC_DIR / "styles.css").exists()
    assert (STATIC_DIR / "app.js").exists()


def test_index_returns_dashboard_file():
    response = index()

    assert Path(response.path).name == "index.html"
