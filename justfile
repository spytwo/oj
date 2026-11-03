up:
    docker compose up --build -d

down:
    docker compose down

fix:
    ruff format && ruff check --fix