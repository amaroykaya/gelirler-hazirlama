"""Uygulama adı ve sürüm bilgisi."""

__version__ = "1.4.0"

APP_NAME = "Antsis Gelir Hazırlama"


def app_window_title(page: str = "") -> str:
    """Pencere başlığı: sayfa + uygulama adı + sürüm."""
    base = f"{APP_NAME} v{__version__}"
    if page:
        return f"{page} — {base}"
    return base
