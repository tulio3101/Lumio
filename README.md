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

## Cuenta

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/users/login/google` | Iniciar sesión o crear cuenta con Google: `{"id_token"}` del SDK de Google. Se verifica firma, emisor, vigencia y audiencia (`GOOGLE_CLIENT_IDS`). La cuenta se reconoce por el `sub` de Google; si no existe se crea sin contraseña con el correo verificado. 200 o 201 (cuenta nueva) con el `TokenPair`. 401 `invalid_google_token` o `google_email_not_verified`, 409 `google_account_conflict` (el correo ya es de una cuenta con contraseña: no se vincula sola, porque el registro con correo no verifica el correo), 500 `google_sign_in_failed`, 503 `google_auth_unavailable` (sin configurar o sin acceso a las llaves de Google) |
| `POST` | `/users/password-reset` | Recuperar Contraseña: `{"email"}`. Si es de una cuenta con contraseña propia, envía un código de 6 dígitos por correo (vence en 15 min, 5 intentos, solo vale el último, un pedido por minuto). Responde siempre 202 con el mismo mensaje, exista o no la cuenta (las cuentas solo Google no reciben código). 500 `password_reset_failed`, 503 |
| `POST` | `/users/password-reset/confirm` | `{"email", "code", "new_password"}` (8–128). 204; se cierran las sesiones de todos los dispositivos y se inicia sesión con la nueva. 400 `invalid_reset_code` (incorrecto, vencido, agotado o correo sin cuenta: misma respuesta), 422, 500 `password_reset_failed`, 503 |
| `GET` | `/users/me` | Cuenta del usuario: `email`, `display_name` y `phone` (los dos últimos pueden ser `null`) |
| `PATCH` | `/users/me` | Personalizar Cuenta (SCRUM-6): cambia solo los campos enviados; `null` o `""` los quita. `display_name`: 1–60 caracteres tras recortar y unir espacios, letras, espacios, `'`, `.` y `-`. `phone`: celular colombiano, 10 dígitos que empiezan por 3 (acepta espacios y guiones; se guarda sin ellos). El correo no se puede cambiar (otros campos: 422). Devuelve la cuenta. 422 datos inválidos, 500 `profile_update_failed`, 503 |
| `GET` | `/users/me/preferences` | Preferencias de voz y vibración (copia de respaldo del teléfono). Sin guardar: las predeterminadas con `updated_at: null`. 401, 503 |
| `PUT` | `/users/me/preferences` | Reemplaza todas: `voice_language` (`es-MX`, `es-ES`, `es-419`…), `voice_identifier` (o `null`), `speech_rate` (0,5–2), `haptics_enabled`, `haptic_intensity` (`soft`, `medium`, `strong`) y `haptic_disabled_events` (solo `routeReady`, `routeFailed`, `routeFinished`). 200 con lo guardado y `updated_at`. 422 datos inválidos, 500 `preferences_update_failed`, 503 |
| `PUT` | `/users/me/password` | Cambiar contraseña: `{"current_password", "new_password"}` (8–128, distinta de la actual). 204; este dispositivo conserva su sesión y las demás se revocan. 403 `invalid_current_password` (no 401, para que el cliente no renueve la sesión), 409 `password_not_set` (cuenta solo Google), 422 inválida o `password_unchanged`, 500 `password_change_failed`, 503 |
| `DELETE` | `/users/me` | Eliminar Cuenta (SCRUM-7): con `Authorization: Bearer <access_token>`, borra la cuenta y en cascada sus sesiones de todos los dispositivos, la ruta activa y el historial (y los contactos de confianza y eventos SOS, que deben declarar su FK con `ondelete="CASCADE"`). 204 sin cuerpo; luego sus tokens responden 401 y el login con ese correo 401. El correo puede registrarse de nuevo como una cuenta vacía. 401 `invalid_session`, 500 `account_deletion_failed` o 503 `database_unavailable` (en ambos la cuenta sigue intacta) |

El perfil (nombre y celular) llega con la migración `0005`. Las preferencias de voz y
vibración (`user_preferences`, migración `0008`) son una copia de respaldo: el teléfono las lee
siempre de su almacenamiento local y nunca espera al backend para aplicarlas; se borran en
cascada al eliminar la cuenta. Por ahora no se conserva ningún dato por razones legales (pendiente de confirmar
en la HU).

## Contactos de confianza

Contactos que recibirán por correo la alerta del botón de emergencia (SCRUM-319). Todos los
endpoints de `/contacts` exigen `Authorization: Bearer <access_token>`; sin token o con uno
inválido responden 401 `invalid_session`. Cada usuario solo ve y modifica los suyos (el
contacto de otro responde 404). La tabla llega con la migración `0006` y se borra en cascada
al eliminar la cuenta.

Reglas: `name` de 1 a 60 caracteres tras recortar y unir espacios (letras, espacios, `'`, `.` y
`-`); `email` con formato válido, se guarda sin espacios laterales y en minúsculas. El correo no
se repite entre tus contactos, no puede ser el de tu cuenta y hay un máximo de 5 por usuario.

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/contacts` | Lista los contactos, del más antiguo al más reciente: `[{id, name, email, created_at}]` |
| `POST` | `/contacts` | Agrega uno: `{"name", "email"}`. 201 con el contacto. 409 `contact_duplicate` o `contact_limit_reached`, 422 datos inválidos o `contact_is_own_email`, 500 `contact_save_failed`, 503 |
| `PUT` | `/contacts/{contact_id}` | Edita el nombre y el correo (siempre los dos). 200 con el contacto. 404 `contact_not_found`, 409 `contact_duplicate`, 422, 500 `contact_save_failed`, 503 |
| `DELETE` | `/contacts/{contact_id}` | Elimina el contacto. 204 sin cuerpo. 404 `contact_not_found`, 500 `contact_delete_failed`, 503 |

Los errores propios llevan `{"detail": <mensaje en español>, "code": <identificador>}`: la app
locuta `detail`. Los 422 de validación usan el formato estándar de FastAPI. No se envía ningún
correo de verificación al contacto; el envío de la alerta es del botón de emergencia.

## Botón de emergencia

Alerta por correo a los contactos de confianza (SCRUM-35). `POST /sos` exige
`Authorization: Bearer <access_token>`. El ADR-310 fija Amazon SES; la tabla `sos_events`
llega con la migración `0007` y se borra en cascada con la cuenta.

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/sos` | `{"idempotency_key": <uuid>, "latitude"?, "longitude"?, "accuracy_m"?}`. Manda un correo por contacto con quién lo envía, la hora, el enlace al mapa y que es una alerta de emergencia. Sin ubicación se envía igual, avisándolo en el correo (`latitude` y `longitude` van juntas o ninguna). 201 con `{id, status, contacts_total, contacts_sent, location_included, created_at}`; `status` es `sent` (todos) o `partial` (algunos). Repetir la misma `idempotency_key` de una alerta ya entregada responde 200 con la misma alerta y no envía nada; una que falló se reintenta. 409 `no_trusted_contacts` (no se envía nada), 502 `sos_delivery_failed` (no salió a ningún contacto), 500 `sos_record_failed`, 422, 401, 503 |

El correo es de texto plano y dice que no sustituye a los servicios de emergencia (con la
línea 123). Solo correo: sin push ni ubicación en tiempo real.

Configuración: `EMAIL_BACKEND` (`log` o `ses`) y `SES_SENDER_EMAIL`. Con `log` el correo solo se
escribe en los logs y solo funciona con `ENVIRONMENT=local`: en `dev` y `prod` sin SES el
envío responde 502 en lugar de fingir que salió. Con `ses` la EC2 usa su rol (`ses:SendEmail`,
ya en `infra/lumio-dev.yaml`). `deploy.sh` activa SES si existe el parámetro
`/lumio/<env>/SES_SENDER_EMAIL`.

**Pendiente fuera del código** (ADR-310): comprar y verificar el dominio en SES (Easy DKIM,
SPF, DMARC), crear el parámetro `SES_SENDER_EMAIL`, aplicar el stack de CloudFormation para dar
el permiso a la EC2 y **pedir la salida del sandbox de SES**: en sandbox solo se envía a
direcciones verificadas y los contactos no lo estarán.

## Narración del entorno

Describe con un VLM lo que el usuario tiene delante (SCRUM-38, ADR-308). `POST /vision/analyze`
exige `Authorization: Bearer <access_token>` y recibe `multipart/form-data`:

| Campo | Uso |
|---|---|
| `image` | Foto JPEG, ≤ 1 MB y ≤ 1024 px de lado largo. La app envía 768 px, calidad 0,7, sin EXIF ni GPS |
| `captured_at` | Hora de la captura (ISO 8601); la app descarta lo que llega más de 4 s después |
| `trigger` | `gesture` (por defecto) o `auto`; solo para métricas de uso y costo |
| `consent_version` | Versión del aviso aceptado (SCRUM-324). Sin ella: 403 `consent_required`, sin mirar la foto |
| `language` | `es` (por defecto) |

Respuesta 200: `{"text", "model", "latency_ms"}`. La app locuta `text` como P3. No hay nivel de
alerta: un riesgo nunca viene de la red, lo decide el loop de seguridad del teléfono.

Errores: 401 `invalid_session`, 403 `consent_required`, 413 `image_too_large`, 422
`invalid_image` (o un campo inválido), 429 `narration_rate_limited` (1 cada 3 s y 1.500 al día
por usuario, en memoria; las automáticas, 1 cada 10 s y 1.200 al día, ver abajo), 503 `narration_unavailable` (Bedrock falló, está saturado o la
narración no está configurada), 504 `narration_timeout` (más de 4 s).

**Solicitudes consecutivas (SCRUM-40).** La app pide una descripción sola cuando la escena cambia
(`trigger=auto`) y el backend las trata aparte para controlar costo y datos: 1 cada 10 s y 1.200
al día por usuario (`NARRATION_AUTO_MIN_INTERVAL_SECONDS`, `NARRATION_AUTO_DAILY_LIMIT`). El
intervalo cuenta desde la última narración del usuario, sea de botón o automática, y las 300 del
día que sobran del tope de 1.500 quedan para «Describir entorno», que siempre conserva su
intervalo de 3 s. Una automática rechazada responde 429 sin llamar al VLM; la app la ignora sin
avisar al usuario y espera antes de volver a intentar.

**Privacidad.** La foto solo vive en memoria durante la solicitud: no se escribe en disco, base
de datos ni S3, y Caddy limita `/vision/*` a 1100 KB para que el cuerpo nunca se pase a disco.
Los logs guardan solo metadatos (modelo, bytes, tokens, latencia); nunca la foto ni el texto. El
prompt de sistema (`app/modules/narration/prompt.py`) prohíbe dar metros, decir que el camino
es seguro y describir a las personas.

Configuración: `NARRATION_BACKEND` (`disabled`, `fake` o `bedrock`), `NARRATION_MODEL_ID` (por
defecto `us.anthropic.claude-haiku-5-5`, perfil de inferencia `us.`: solo EE. UU.) y
`NARRATION_TIMEOUT_SECONDS` (4). `fake` devuelve un texto fijo para probar la app sin AWS y
solo vale con `ENVIRONMENT=local`. `deploy.sh` activa Bedrock si existe el parámetro
`/lumio/<env>/NARRATION_MODEL_ID`.

**Pendiente fuera del código** (ADR-308): habilitar el acceso al modelo en la consola de
Bedrock (formulario de caso de uso de Anthropic), aplicar el stack para dar
`bedrock:InvokeModel` a la EC2, crear el parámetro `NARRATION_MODEL_ID`, verificar que el
*model invocation logging* siga apagado (`aws bedrock get-model-invocation-logging-configuration`),
crear la alarma de AWS Budgets para Bedrock en US$8/mes y revisar las cuotas del modelo. El
ADR sigue «Propuesto» hasta tener el benchmark; el modelo se cambia sin desplegar código.

## Rutas

Todos los endpoints de `/places` exigen `Authorization: Bearer <access_token>` (el de
`POST /users/login`); sin token o con uno inválido responden 401 `invalid_session`. Para
probar, crea una cuenta desde la app iOS o con `POST /users`.

| Método | Ruta | Uso |
|---|---|---|
| `PUT` | `/places/routes/active` | Crear Ruta: guarda la ruta calculada en el dispositivo y cancela la abierta anterior |
| `GET` | `/places/routes/active` | Ruta activa o pausada del usuario (404 `active_route_not_found`) |
| `PUT` | `/places/routes/{route_id}/destination` | Modificar Ruta: misma ruta, nuevo recorrido desde la ubicación actual; progreso a 0. 404 `route_not_found`, 409 `route_not_open` |
| `PUT` | `/places/routes/{route_id}/reroute` | Recalcular Ruta: mismo destino, recorrido nuevo desde donde se desvió el usuario (cuerpo de crear ruta + `rerouted_at`). Conserva el id, progreso a 0, queda activa y suma `reroute_count` / `last_rerouted_at` (hora del dispositivo acotada entre el inicio y ahora). 404 `route_not_found`, 409 `route_not_open` o `route_destination_mismatch` (para otro destino se usa `/destination`) |
| `POST` | `/places/routes/{route_id}/finish` | Finalizar Ruta: `{"status": "completed" \| "cancelled", "finished_at"}` con la hora del dispositivo (acotada entre el inicio y ahora). Si ya estaba cerrada no cambia nada; 404 `route_not_found` |
| `POST` | `/places/routes/history` | Guardar una ruta finalizada sin conexión que nunca llegó al backend (cuerpo de crear ruta + `id`, `status`, `started_at`, `finished_at`). No toca la ruta activa; reenviar el mismo `id` no la duplica; 409 `route_id_conflict` si el id es de otro usuario |
| `GET` | `/places/routes/history?limit=20&offset=0` | Consultar Rutas Recientes: rutas completadas o canceladas (al iniciar otra), de la más reciente a la más antigua por `finished_at`; sin la ruta abierta. `limit` 1–100 |

`ActiveRoute` incluye `reroute_count` y `last_rerouted_at` (migración `0004`).

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
