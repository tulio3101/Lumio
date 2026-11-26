# SCRUM-319 · HU: Configurar Contactos de Confianza

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorios | `Lumio` y `LumioFrontend` |
| Commits | 3 (2026-11-24) |
| Es dependencia de | SCRUM-35 (Botón de Emergencia) |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

> Como usuario con discapacidad visual, quiero registrar contactos de confianza para que reciban mi
> alerta cuando active el botón de emergencia.

**Criterios de aceptación**
- Agregar, editar y eliminar contactos con su correo.
- Se valida el formato del correo antes de guardar.
- Los contactos se guardan en el backend y siguen al volver a iniciar sesión.
- Se informa por audio si se guardó o no.
- Gestión usable con VoiceOver.

Alcance: solo correo; el push a contactos con la app queda fuera del MVP.

## Prompts · Backend (commit `b61fb49`)

### Prompt 1 · Módulo de contactos

```text
Crea el módulo app/modules/contacts (models, schemas, repository, service, router, exceptions) e
inclúyelo en main.py:
- TrustedContact: id, user_id con FK a users ondelete CASCADE, name, email, created_at; único
  (user_id, email). Migración 0006_trusted_contacts y regístrala en alembic/env.py.
- Reglas: name de 1 a 60 caracteres tras recortar y unir espacios (letras, espacios, ', . y -);
  email con formato válido, recortado y en minúsculas; no se repite entre tus contactos; no puede
  ser el de tu cuenta; máximo 5 por usuario.
- Endpoints con Bearer (sin token 401 invalid_session), cada usuario solo ve los suyos (el de
  otro responde 404):
  GET /contacts (del más antiguo al más reciente), POST /contacts (201; 409 contact_duplicate o
  contact_limit_reached; 422 contact_is_own_email), PUT /contacts/{id} (nombre y correo siempre
  los dos; 404 contact_not_found), DELETE /contacts/{id} (204).
  Fallos de base: 500 contact_save_failed / contact_delete_failed, 503.
- Errores con {"detail", "code"}; detail en español para que la app lo locute.
No envíes ningún correo de verificación: el envío es del botón de emergencia.
```

### Prompt 2 · Pruebas y README

```text
Escribe tests/modules/contacts/test_contacts.py (cada regla, límite de 5, correo propio,
duplicado con mayúsculas) y tests/integration/test_contacts_api.py con Postgres (aislamiento
entre usuarios, cascada al eliminar la cuenta). Documenta la sección «Contactos de confianza» del README con la tabla de
endpoints y errores.
```

## Prompts · iOS (commits `b7fcd5b`, `a6b6336`)

### Prompt 3 · Dominio, servicio y datos

```text
En Features/Contacts crea:
- Domain/TrustedContact y ContactsPolicy: nombre 1–60 con las reglas del nombre de la cuenta
  (reutiliza las de UserProfile), formato del correo con CredentialsPolicy, correo no repetido
  entre los contactos cargados y máximo 5, igual que el backend.
- Data/RemoteTrustedContactsService: GET, POST, PUT y DELETE /contacts con AuthorizedHTTPClient.
  No hay copia local: los contactos viven solo en el backend.
- Application/TrustedContactsService: valida antes de enviar (con errores o sin cambios no envía),
  manda el correo recortado y en minúsculas y locuta todo resultado por el árbitro (contexto
  trusted-contacts). Un fallo deja la lista como estaba.
La app no lee el code del backend (HTTPClientError solo guarda el estado): locuta 409 como «ese
correo ya está en tu lista o ya tienes 5 contactos» y 422 como «el servidor no aceptó los datos…
ni tu propio correo». Repetido y máximo se detectan antes, en el teléfono, con mensaje exacto.
```

### Prompt 4 · Pantalla accesible

```text
Crea TrustedContactsView y TrustedContactsViewModel en Preferencias > Emergencia > Contactos de
confianza. Cada contacto se lee como «nombre, correo» seguido de «Editar a …» y «Eliminar a …».
Eliminar pide confirmación. Agregar con el máximo no abre el formulario y lo dice. El formulario
es una pantalla de la navegación (no una hoja), con el error de cada campo en su pista; no muevas
el foco para no superponer VoiceOver con el árbitro. Agrega la entrada en SettingsView y
documenta en docs/ARCHITECTURE.md y el README.
```

### Prompt 5 · Pruebas de la app y corrección (commits `b7fcd5b`, `a6b6336`)

```text
Escribe TrustedContactsTests con un servicio remoto y un árbitro falsos: validación de nombre y
correo, repetido y máximo detectados en el teléfono, 409 y 422 del backend con su mensaje, editar
sin cambios no envía, eliminar con confirmación. Si alguna prueba falla en CI, corrige la prueba
o el código según corresponda y dime qué cambiaste.
```

## Verificación final

- Backend: `pytest -rs` cubre reglas, límite, aislamiento y cascada.
- iOS: con VoiceOver se agrega un contacto, se oye «Contacto guardado», se edita y se elimina con
  confirmación; al cerrar e iniciar sesión siguen ahí.

## Commits cubiertos

| Commit | Repo | Mensaje |
|---|---|---|
| `b61fb49` | Lumio | SCRUM-319 HU: Configurar Contactos de Confianza |
| `b7fcd5b` | LumioFrontend | SCRUM-319 HU: Configurar Contactos de Confianza |
| `a6b6336` | LumioFrontend | SCRUM-319 HU: Fixing errors |
