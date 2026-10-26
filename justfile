up:
    docker compose up --build

down:
    docker compose down

fix:
    ruff format && ruff check --fix