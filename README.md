# Lumio
Lumio is an application that uses a modular monolithic architecture, aiming to provide support and foster independence for individuals with severe visual impairments. This is a project for the course "Software Innovation Supported by New Technologies" (2026-2).

## Desarrollo local con Docker (API + Postgres)

```sh
docker compose up -d --build                          # migra y arranca la API en :8000
docker compose exec api python -m app.scripts.seed_dev_user   # UUID para LumioDevUserID
docker compose logs -f api
docker compose down                                   # `down -v` borra también los datos
```

Para probar desde un iPhone físico en la misma red Wi-Fi, usa la IP del equipo en
`LumioAPIBaseURL` (por ejemplo `http://192.168.10.32:8000`) y permite el puerto 8000
en el firewall (`sudo ufw allow 8000/tcp`). Comprueba desde Safari en el iPhone que
`http://<IP>:8000/health` responde.

## Desarrollo local sin Docker para la API

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose up -d db            # solo Postgres (bases lumio y lumio_test)
alembic upgrade head
python -m app.scripts.seed_dev_user # imprime el UUID del usuario de desarrollo
uvicorn app.main:app --reload
```

Mientras no exista el inicio de sesión, los endpoints de rutas identifican al usuario
con el header `X-User-Id` (UUID de un usuario existente). En iOS, ese UUID va en la
clave `LumioDevUserID` del `Info.plist`.

## Pruebas

```sh
ruff check .
pytest                                    # unitarias; las de integración se omiten
export TEST_DATABASE_URL=postgresql+psycopg://lumio:lumio@localhost:5432/lumio_test
pytest -rs                                # unitarias + integración contra Postgres
```

`TEST_DATABASE_URL` debe apuntar a una base de datos dedicada: las pruebas de
integración reconstruyen su esquema con las migraciones y vacían sus tablas.
