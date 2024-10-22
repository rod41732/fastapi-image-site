# FastAPI image sharing website

Experimenting with FastAPI to build image sharing website like dA that user can register account and share images together.
Trying to build both server-rendered page and API in the same time.

WIP: This is an experiment!

## Technologies used

- Python / FastAPI: backend
- Alembic: used for generating migration
- Poetry: Dependency management
- HTMX: interactivity in frontend
- HTPy: server side HTML generation
- PostgresQL: database

## Running

NOTE: to run the command you either need to activate poetry's virtual env (Terminal in VSCode should activate it for you), or prefix the commands with `poetry run` like `poetry run alembic upgrade head`

- Start the database (use docker-compose.yml or your own database, non-PostgresQL should work too)
  - `docker compose up -d` to start the DB
- Install dependency: `poetry install --no-root`
- Update DB config in `alembic.ini` and `libs/db.py`
- Migrate the database `alembic upgrade head`
- Run the server: `fastapi dev`

## Using

- visit localhost:8000/ for website (server side rendered)

  - `/`: home page
  - `/user/login.html`: login
  - `/user/register.html`: register. there is currently no email validation
  - `/artworks/gallery.html`: list artworks
  - `/artworks/mine.html`: list my artworks
  - `/artworks/{id}.html`: single artwork view: it's also possible to comment on artwork

- visit `/docs` for Swagger
  - currently it's way to upload new image (/artworks/upload)

## Notes

- image are stored locally, and served using python server, would be ideal to use servers such as NGINX
- credentials are hardcoded, for now...
