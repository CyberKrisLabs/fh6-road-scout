"""Smoke test: verify all scaffold modules import without error."""


def test_app_package_imports() -> None:
    import app
    import app.core
    import app.models
    import app.ui

    assert app.core and app.models and app.ui


def test_utils_imports() -> None:
    from app.utils import logging_setup, paths

    assert callable(paths.asset)
    assert callable(logging_setup.setup_logging)
