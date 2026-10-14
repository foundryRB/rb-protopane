from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    uvicorn.run(
        "protopane.adapters.inbound.http.app:create_app",
        factory=True,
        host=os.environ.get("PROTOPANE_HOST", "0.0.0.0"),
        port=int(os.environ.get("PROTOPANE_PORT", "8800")),
        reload=False,
    )


if __name__ == "__main__":
    main()
