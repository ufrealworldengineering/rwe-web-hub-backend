# RWEHUB Backend

### Start your venv

1. 
```
python -m venv .venv # or python3 or py 
```
2. 
```
source .venv/bin/activate # for macOS and linux
.venv\Scripts\activate # for windows cmd
.venv\Scripts\Activate # for windows powershell
```
### Install requirements
```
pip install -r requirements.txt
```

### Start the app
```
uvicorn main:app --reload
```
or
```
python main.py
```

### Albemic
if database migrations are needed, run these commands 

to generate the migration script, run this
```
alembic revision --autogenerate -m "initial migration" # example message
```
to apply the changes to supabse
```
alembic upgrade head
```

### Tests (pytest + Postgres test DB)
These tests use a real Postgres database pointed to by `DATABASE_URL_TEST`.

If you don't already have a local Postgres, you can run a disposable test DB via Docker:
```
docker compose -f docker-compose.test.yml up -d
```

Then in PowerShell:
```
$env:DATABASE_URL_TEST = "postgresql://postgres:postgres@localhost:5433/rwehub_test"
python -m pytest
```

or CMD
```
set DATABASE_URL_TEST=postgresql://postgres:postgres@localhost:5433/rwehub_test
python -m pytest
```

or Linux 
```
export DATABASE_URL_TEST=postgresql://postgres:postgres@localhost:5433/rwehub_test
python -m pytest
```