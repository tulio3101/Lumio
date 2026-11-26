# SCRUM-35 · HU: Botón de Emergencia

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 2 (2026-11-25) |
| Depende de | SCRUM-319 (contactos), ADR-310 (Amazon SES) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario de Lumio, quiero activar una función de emergencia para que mis contactos de confianza
> reciban mi ubicación cuando necesite ayuda.

**Criterios de aceptación**
- Se activa con una interacción accesible.
- Hay un margen breve para cancelar, comunicado por audio.
- Feedback de activación por audio y háptica.
- Se envía un correo a los contactos con la ubicación actual, si hay permiso.
- El correo dice quién lo envía y que es una alerta de emergencia.
- Sin contactos se informa; sin conectividad se informa que no se pudo enviar.
- Se comunica que no sustituye a los servicios de emergencia.

Alcance: solo correo; push y ubicación en tiempo real fuera del MVP.

## Prompts · Backend (commit `d1b6b10`)

### Prompt 1 · Envío de correo con SES y respaldo en logs

```text
El ADR-310 fija Amazon SES para el correo. Crea app/modules/sos/email.py con una interfaz de envío
y dos implementaciones elegidas por EMAIL_BACKEND: log (solo escribe en los logs y solo se permite
con ENVIRONMENT=local) y ses (boto3 con el rol de la EC2). En dev y prod sin SES el envío debe
fallar con 502, no fingir que salió. Agrega EMAIL_BACKEND y SES_SENDER_EMAIL a Settings y a
.env.example; con ses, SES_SENDER_EMAIL es obligatorio al arrancar.
```

### Prompt 2 · Mensaje y registro de la alerta

```text
- sos/message.py: correo de texto plano en español con quién lo envía (nombre o correo de la
  cuenta), la hora, el enlace al mapa si hay ubicación (o que no se pudo obtener) y que es una
  alerta de emergencia que no sustituye a los servicios de emergencia (línea 123).
- sos/models.py: SosEvent (user_id con CASCADE, idempotency_key única por usuario con
  uq_sos_events_user_key, latitude/longitude/accuracy_m opcionales, status que arranca en
  pending, contacts_total, contacts_sent, created_at). Migración 0007_sos_events.
```

### Prompt 3 · Endpoint POST /sos

```text
POST /sos con Bearer y {"idempotency_key": uuid, "latitude"?, "longitude"?, "accuracy_m"?}
(latitude y longitude van juntas o ninguna):
- manda un correo por contacto de confianza; 201 con {id, status, contacts_total, contacts_sent,
  location_included, created_at}; status sent (todos) o partial (algunos);
- repetir la misma idempotency_key de una alerta ya entregada responde 200 con la misma y no
  envía nada; una que falló se reintenta;
- 409 no_trusted_contacts (no envía nada), 502 sos_delivery_failed (no salió a nadie),
  500 sos_record_failed, 422, 401, 503.
En deploy.sh activa SES si existe el parámetro /lumio/<env>/SES_SENDER_EMAIL y en
infra/lumio-dev.yaml da a la EC2 el permiso ses:SendEmail. Pruebas: tests/modules/sos
(test_email con los dos backends, test_sos con cada caso) y tests/integration/test_sos_api.py
con un enviador falso. Documenta en el README, incluido lo
pendiente fuera del código: verificar el dominio (Easy DKIM, SPF, DMARC), crear el parámetro y
pedir la salida del sandbox de SES.
```

## Prompts · iOS (commit `1a3d927`)

### Prompt 4 · Dominio y servicio

```text
En Features/Emergency crea:
- Domain/Emergency: estados (en reposo, cuenta atrás n, enviando, enviada, parcial, falló) y
  resultados.
- Data/CoreLocationEmergencyLocator: pide la ubicación SIN pedir permiso; sin permiso o sin señal
  la alerta sale sin ubicación.
- Data/RemoteEmergencyService: POST /sos con una llave de idempotencia.
- Application/EmergencyService:
  1. activate() da feedback al instante (HapticCue.emergencyActivated y audio con prioridad
     inmediata que recuerda que no sustituye al 123) y abre 10 s para cancelar; una segunda
     activación durante el margen se ignora;
  2. durante el margen pide la ubicación y cuenta los contactos (GET /contacts, sin audio); sin
     ninguno lo informa de inmediato en lugar de esperar;
  3. cancel() no envía nada y lo dice;
  4. al terminar el margen envía; sin conexión conocida no lo intenta y lo informa;
  5. «Reintentar» reenvía la misma alerta con la misma llave y sin nueva cuenta atrás, así nunca
     duplica correos;
  6. todo resultado se locuta (contexto emergency) con háptica de éxito o error; un parcial dice a
     cuántos llegó y todo fallo recuerda el 123. Sesión rechazada: borra tokens y vuelve a la
     bienvenida al cerrar el aviso.
Agrega los HapticCue emergencyActivated, emergencySent y emergencyFailed en UIKitHapticFeedback.
```

### Prompt 5 · Control fijo y accesible

```text
Crea EmergencyControl y EmergencyViewModel, fijo sobre la pila de Trayecto (.emergencyControl en
RootView). Un solo botón cambia de «Emergencia» a «Cancelar alerta (n)» y a «Reintentar envío»
sin cambiar de identidad, para que el foco de VoiceOver no se pierda y quien activó con doble
toque cancele con otro doble toque en el mismo lugar. Estilo destructivo (color de error con
borde, icono y texto), sin depender solo del color. Documenta en docs/ARCHITECTURE.md y el README.
```

## Verificación final

- Backend: `pytest -rs` con EMAIL_BACKEND=log cubre envío total, parcial, sin contactos,
  idempotencia y fallo.
- iOS: con VoiceOver, doble toque activa y se oye la cuenta atrás; otro doble toque cancela;
  dejarla correr envía y dice a cuántos llegó.
- **Pendiente fuera del código:** dominio verificado en SES y salida del sandbox; en sandbox solo
  se envía a direcciones verificadas.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `d1b6b10` | Lumio | SCRUM-35 HU: Botón de Emergencia |
| `1a3d927` | LumioFrontend | SCRUM-35 HU: Botón de Emergencia |
