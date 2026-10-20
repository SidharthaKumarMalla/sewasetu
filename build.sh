#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

pip install --upgrade pip
pip install -r app/requirements.txt

# Initialize DB schema (safe to re-run because of IF NOT EXISTS)
python -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
with open('app/schema.sql') as f:
    cur.execute(f.read())
conn.commit()

# Load seed data only if the table is empty
cur.execute('SELECT count(*) FROM applications')
if cur.fetchone()[0] == 0:
    print('Loading seed data...')
    with open('seed/seed.sql') as f:
        cur.execute(f.read())
    conn.commit()
    print('Seed data loaded.')
else:
    print('Data already exists, skipping seed.')
cur.close()
conn.close()
"
