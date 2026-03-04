from __future__ import annotations

import sys


def patch_six_meta_path_importer_path_attr() -> None:
    """Work around a PySide6 + pandas import crash on Python 3.12.0.

    When PySide6 is imported first, `shibokensupport` may call into `inspect`,
    which can end up calling `repr()` on `six.moves`. On Python 3.12.0 the
    module repr path assumes namespace loaders expose `loader._path`.

    `six._SixMetaPathImporter` doesn't have that attribute, so the repr crashes
    and the pandas import aborts. Adding an empty `_path` attribute is enough
    to keep the import working.
    """
    try:
        import six  # type: ignore
    except Exception:
        return

    importer_type = getattr(six, "_SixMetaPathImporter", None)
    if importer_type is None:
        return

    for finder in sys.meta_path:
        if isinstance(finder, importer_type) and not hasattr(finder, "_path"):
            try:
                finder._path = []
            except Exception:
                # Best-effort patch; avoid breaking app startup.
                pass
