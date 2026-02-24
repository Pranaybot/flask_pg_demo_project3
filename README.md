# Flask + PostgreSQL (Docker) — Simple REST API Setup Guide

This guide shows how to:

✅ Run PostgreSQL in Docker (or reuse an existing container like **pgacid**)  
✅ Connect the Flask API (`app.py`) to PostgreSQL  
✅ Load records from `data.json`  
✅ Run filtered searches  
✅ Demonstrate indexing and before/after query performance

---

# 1. Prerequisites

Install:

- Docker Desktop (Mac / Windows / Linux)
- Python 3.9+
- pip

Verify:

```bash
docker --version
python3 --version
```

---

# 2. Project Structure

Your folder should look like this:

```
flask_pg_simple/
│
├── app.py
├── data.json
├── .env
└── README.md
```

`data.json` contains the rows that will be inserted into PostgreSQL.

---

# 3. PostgreSQL Docker Setup

## Option A — Use Your Existing Container (Recommended)

You already have:

```
pgacid   postgres:15   PORT 5432
```

Start it if needed:

```bash
docker start pgacid
```

Verify:

```bash
docker ps
```

You should see:

```
pgacid   postgres   5432/tcp
```

---

## Option B — Create a New PostgreSQL Container

If starting fresh:

```bash
docker run --name pgacid \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  -d postgres:16
```

### Container Settings

| Setting | Value |
|---|---|
| Container Name | pgacid |
| Database | postgres |
| Username | postgres |
| Password | postgres |
| Port | 5432 |

---

## Verify Database Access

Connect inside container:

```bash
docker exec -it pgacid psql -U postgres
```

List databases:

```sql
\l
```

Exit:

```
\q
```

---

# 4. Create Python Virtual Environment

Inside project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install Flask psycopg2-binary python-dotenv
```

---

# 5. Configure Database Connection

Create `.env`:

```bash
touch .env
```

Add:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
```

This matches your **pgacid Docker container**.

(No need to manually set `DATABASE_URL`; the app builds it automatically.)

---

# 6. Run the Flask Application

Start the API:

```bash
python app.py
```

Expected output:

```
Running on http://127.0.0.1:5000
```

---

# 7. Seed Data from data.json

The API automatically reads rows from `data.json`.

Run:

```bash
curl -X POST http://localhost:5000/seed
```

Expected response:

```json
{
  "ok": true,
  "inserted": 20,
  "source": "data.json"
}
```

This will:

- create table `customers`
- truncate existing data
- insert rows from `data.json`

---

# 8. Test the Filtered Search Endpoint

Example:

```bash
curl "http://localhost:5000/search?city=Minneapolis&status=active"
```

Example response:

```json
{
  "query_time_ms": 1.2,
  "results": [...]
}
```

### Available Filters

| Parameter | Example |
|---|---|
| city | `city=Seattle` |
| status | `status=active` |
| name | `name=Ava` |

Combine filters:

```bash
curl "http://localhost:5000/search?city=Minneapolis&status=active&name=Ava"
```

---

# 9. Measure Query Performance (Before Indexing)

Run:

```bash
curl "http://localhost:5000/perf?city=Minneapolis&status=active"
```

This executes:

```
EXPLAIN (ANALYZE, BUFFERS)
```

Look for:

```
Seq Scan on customers
```

Meaning PostgreSQL scans the whole table.

---

# 10. Add Database Indexes (Optimization)

Create indexes:

```bash
curl -X POST http://localhost:5000/index
```

Indexes created:

- `idx_customers_city`
- `idx_customers_status`

These optimize filtered searches.

---

# 11. Measure Performance Again (After Indexing)

Run again:

```bash
curl "http://localhost:5000/perf?city=Minneapolis&status=active"
```

Now you may see:

```
Index Scan
```

or

```
Bitmap Index Scan
```

This shows PostgreSQL using indexes.

The endpoint returns:

- BEFORE execution plan
- AFTER execution plan
- Execution timing comparison

---

# 12. Compare Query Timing

Run search again:

```bash
curl "http://localhost:5000/search?city=Minneapolis&status=active"
```

Compare:

```
query_time_ms
```

before and after indexing.

> Note: With only ~20 rows, PostgreSQL may still choose a sequential scan because it is faster for tiny tables. This is normal behavior.

---

# 13. Stop PostgreSQL Container

Stop:

```bash
docker stop pgacid
```

Remove (optional):

```bash
docker rm pgacid
```

---

# 14. Restart Later

```bash
docker start pgacid
```

---

# 15. Troubleshooting

## Port Already in Use

Run Postgres on another port:

```bash
-p 5433:5432
```

Update `.env`:

```env
DB_PORT=5433
```

---

## Cannot Connect to Database

Check logs:

```bash
docker logs pgacid
```

---

## Verify Tables Exist

```bash
docker exec -it pgacid psql -U postgres -c "\dt"
```

You should see:

```
customers
```

---

# 16. What This Demo Shows

This minimal project demonstrates:

- Flask REST API
- PostgreSQL running in Docker
- Loading data from JSON file
- Filtered querying
- Basic indexing optimization
- Query plan comparison using EXPLAIN ANALYZE
- Before vs After performance analysis

---

✅ You now have a complete local Flask + PostgreSQL (Docker) development setup.