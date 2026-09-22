from PyQt6.QtCore import QSettings, QSize
from PyQt6.QtGui import QGuiApplication

# Defaults (matching current hardcoded values)
DEFAULTS = {
    "export/format": "JPEG",
    "export/quality": 92,
    "export/ppi": 300,
    "export/output_mode": "same_as_pdf",  # "same_as_pdf", "last_used", "fixed"
    "export/fixed_path": "",
    "export/last_used_path": "",
    "naming/include_doc_name": True,
    "naming/suffix": "page_",
    "naming/zero_padding": 2,
    "thumbnails/default_size": 180,
    "thumbnails/min_columns": 4,
    "general/remember_last_dir": True,
    "general/last_open_dir": "",
}


class Settings:
    """Thin wrapper around QSettings with defaults."""

    def __init__(self):
        self._qs = QSettings("Monokular", "Monokular")

    def get(self, key: str):
        default = DEFAULTS.get(key)
        val = self._qs.value(f"settings/{key}", default)
        # QSettings stores everything as strings, cast back
        if isinstance(default, bool):
            if isinstance(val, str):
                return val.lower() == "true"
            return bool(val)
        if isinstance(default, int):
            return int(val)
        return val

    def set(self, key: str, value):
        self._qs.setValue(f"settings/{key}", value)

    def reset_all(self):
        for key, value in DEFAULTS.items():
            self._qs.setValue(f"settings/{key}", value)


def _is_wayland() -> bool:
    return QGuiApplication.platformName().startswith("wayland")


def save_geometry(key: str, widget):
    """Persist a window's size and position under window/<key>.

    Wayland gets only the size, under window_size/<key>: apps can't place
    windows there anyway, and compositors such as Hyprland flag every window
    as maximized, which makes Qt's geometry blob keep a stale normal size.
    """
    qs = QSettings("Monokular", "Monokular")
    if _is_wayland():
        qs.setValue(f"window_size/{key}", widget.size())
    else:
        qs.setValue(f"window/{key}", widget.saveGeometry())


def restore_geometry(key: str, widget) -> bool:
    """Restore a window's saved geometry. Returns False when nothing was saved."""
    qs = QSettings("Monokular", "Monokular")
    if _is_wayland():
        size = qs.value(f"window_size/{key}")
        if not isinstance(size, QSize) or not size.isValid():
            return False
        widget.resize(size)
        return True
    geometry = qs.value(f"window/{key}")
    if not geometry:
        return False
    return widget.restoreGeometry(geometry)
