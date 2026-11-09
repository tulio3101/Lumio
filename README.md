# Lumio
Lumio is an application that uses a modular monolithic architecture, aiming to provide support and foster independence for individuals with severe visual impairments. This is a project for the course "Software Innovation Supported by New Technologies" (2026-2).

## Desarrollo local con Docker (API + Postgres)

```sh
docker compose up -d --build                          # migra y arranca la API en :8000
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
uvicorn app.main:app --reload
```

## Rutas

Todos los endpoints de `/places` exigen `Authorization: Bearer <access_token>` (el de
`POST /users/login`); sin token o con uno inválido responden 401 `invalid_session`. Para
probar, crea una cuenta desde la app iOS o con `POST /users`.

| Método | Ruta | Uso |
|---|---|---|
| `PUT` | `/places/routes/active` | Crear Ruta: guarda la ruta calculada en el dispositivo y cancela la abierta anterior |
| `GET` | `/places/routes/active` | Ruta activa o pausada del usuario (404 `active_route_not_found`) |
| `PUT` | `/places/routes/{route_id}/destination` | Modificar Ruta: misma ruta, nuevo recorrido desde la ubicación actual; progreso a 0. 404 `route_not_found`, 409 `route_not_open` |
| `POST` | `/places/routes/{route_id}/finish` | Finalizar Ruta: `{"status": "completed" \| "cancelled", "finished_at"}` con la hora del dispositivo (acotada entre el inicio y ahora). Si ya estaba cerrada no cambia nada; 404 `route_not_found` |
| `POST` | `/places/routes/history` | Guardar una ruta finalizada sin conexión que nunca llegó al backend (cuerpo de crear ruta + `id`, `status`, `started_at`, `finished_at`). No toca la ruta activa; reenviar el mismo `id` no la duplica; 409 `route_id_conflict` si el id es de otro usuario |
| `GET` | `/places/routes/history?limit=20&offset=0` | Consultar Rutas Recientes: rutas completadas o canceladas (al iniciar otra), de la más reciente a la más antigua por `finished_at`; sin la ruta abierta. `limit` 1–100 |

Si tu base local se creó antes de renumerar la migración de rutas (`0002` → `0003`),
recréala con `docker compose down -v`.

## Pruebas

```sh
ruff check .
pytest                                    # unitarias; las de integración se omiten
export TEST_DATABASE_URL=postgresql+psycopg://lumio:lumio@localhost:5432/lumio_test
pytest -rs                                # unitarias + integración contra Postgres
```

`TEST_DATABASE_URL` debe apuntar a una base de datos dedicada: las pruebas de
integración reconstruyen su esquema con las migraciones y vacían sus tablas.
