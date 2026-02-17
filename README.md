# RWEHUB Backend

### Start your venv

1. 
```
python -m venv .venv # or python3 or py 
```
2. 
```
source .venv/bin/activate # for macOS and linux
.venv\Scripts\activate.bat # for windows cmd
.venv\Scripts\Activate.ps1 # for windows powershell
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