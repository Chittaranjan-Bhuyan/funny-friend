# Crush Calculator

HTML + CSS + JS frontend, FastAPI backend, MySQL database.

## Run it

1. Make sure MySQL is running.
2. Open `backend/main.py` and set `DB_USER` and `DB_PASSWORD`
   (or set the environment variables `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_NAME`).
3. Install and start:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

4. Open http://localhost:8000

The database `crush_calculator` and table `results` are created automatically.

## See the saved data

```sql
USE crush_calculator;
SELECT * FROM results ORDER BY id DESC;
```

## Share with friends on the same Wi-Fi

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Then friends open `http://YOUR_PC_IP:8000` on their phones.