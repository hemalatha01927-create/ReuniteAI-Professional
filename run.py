import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    production = os.environ.get("APP_ENV", "development").lower() == "production"
    app.run(
        host="0.0.0.0" if production else "127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=not production,
    )
