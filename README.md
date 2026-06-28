# AW Client Report Portal

A Flask + SQLite + ReportLab MVP for generating quarterly SACS and TCC reports.

## Local setup

```bash
python -m pip install -r requirements.txt
python seed.py
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Railway deployment

Use the included Procfile:

```text
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1
```

For persistent SQLite storage on Railway:

1. Add a Railway Volume.
2. Mount it at `/data`.
3. Add variable:

```text
RAILWAY_DATABASE_PATH=/data/app.db
```

## Important security note

This MVP uses demo data only. Do not deploy with real client financial data until authentication is added and every route is protected.
