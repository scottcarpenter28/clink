#!/bin/sh
set -e

echo "Starting Clink application..."

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-clink}"
DB_USER="${DB_USER:-clink_user}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT}..."

MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "PostgreSQL is unavailable - attempt $RETRY_COUNT/$MAX_RETRIES"

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "ERROR: PostgreSQL did not become ready in time"
        exit 1
    fi

    sleep 2
done

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating default admin user if needed..."
python manage.py create_default_admin

SERVER_TYPE="${SERVER_TYPE:-gunicorn}"

if [ "$SERVER_TYPE" = "development" ]; then
    echo "Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Starting Gunicorn server..."
    exec gunicorn clink.wsgi:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-4}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL:-info}"
fi
