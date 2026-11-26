#!/bin/sh
# Aplica las migraciones pendientes antes de arrancar la API.
set -e
alembic upgrade head
exec "$@"
