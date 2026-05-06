# next-drones-api

FastAPI service for the Next Drones Shop workshop (Sprint 2: RDS Postgres + REST API).

## Stack

- Python 3.12+, [uv](https://github.com/astral-sh/uv) for dependencies (`pyproject.toml` + `uv.lock`)
- FastAPI + Uvicorn
- SQLAlchemy 2 + PostgreSQL (psycopg2)

## Local setup

```bash
cp .env.example .env
# Set DATABASE_URL to your Postgres instance (local or RDS).

uv sync
uv run python -m app.seed
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- Products: `GET/POST /products`, `GET/DELETE /products/{id}`
- Customers: `GET/POST /customers`, `DELETE /customers/{id}`
- Orders: `GET/POST /orders`, `GET/DELETE /orders/{id}` — each order references **`customers`**; JSON includes nested `customer`. On startup, legacy DBs that still store customer fields on `orders` are migrated automatically.
- Comprobaciones con `curl`: [docs/sprint2-verificacion-api.md](docs/sprint2-verificacion-api.md)

## Docker

Build and run (after setting `DATABASE_URL` for the container runtime, e.g. `-e DATABASE_URL=...`):

```bash
docker build -t next-drones-api:local .
docker run --rm -p 8000:8000 -e DATABASE_URL="postgresql://..." next-drones-api:local
```

The workshop deploys the image to ECR and runs it on EC2 with Docker; see `plan.md` in **aws2-workshop**.
