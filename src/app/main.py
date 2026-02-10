from __future__ import annotations

from app.bootstrap import build_application


def main() -> int:
    app, window, _ = build_application()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
