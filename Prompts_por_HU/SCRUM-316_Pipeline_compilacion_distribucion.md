# SCRUM-316 · HU: Configurar el pipeline de compilación y la distribución gratuita del MVP

| | |
|---|---|
| Responsable (Jira) | Daniel Patiño |
| Estado Jira | Finalizado |
| Repositorio | `LumioFrontend` |
| Commits | 7 (2026-10-09 → 2026-10-29) |
| Rama | `SCRUM-316-hu-configurar-el-pipeline-de-compilacion-y-la-distribucion-gratuita-del-mvp` |

> Prompts reconstruidos a partir de los commits y de la HU en Jira; no son el historial literal del chat.

## La HU

El equipo no pagó el Apple Developer Program, así que no hay TestFlight. El repo es público para
usar gratis los runners macOS de GitHub Actions. Un workflow compila un `.ipa` **sin firmar**, lo
publica en GitHub y cada integrante lo instala con Sideloadly o AltStore con un Apple ID de pruebas.

**Criterios de aceptación**
- Un workflow genera un `.ipa` sin firmar en cada cambio a la rama principal.
- El `.ipa` queda disponible para todo el equipo en GitHub.
- Se revisó que el repositorio no tiene secretos antes de hacerlo público.
- Hay una guía para instalar con Sideloadly o AltStore (Modo desarrollador, renovar cada 7 días).
- Al menos dos integrantes sin Mac instalaron una versión con la guía.
- El login con Google funciona en la app instalada así.
- La app permite ver o exportar sus registros sin Xcode.

## Prompts

### Prompt 1 · Workflow que compila y publica el `.ipa` (commit `2178f5f`)

```text
Estamos arrancando el repo iOS de Lumio (SwiftUI) y no tenemos Apple Developer Program ni Mac
para todos. El repo es público, así que los runners macOS de GitHub Actions son gratis.

Crea .github/workflows/xcode-distribution.yml que:
- corra en macos-15 en push a main, develop y ramas feature/**, y con workflow_dispatch;
- imprima xcodebuild -version para dejar registro de la versión de Xcode;
- compile el scheme para iphoneos en Release SIN firmar
  (CODE_SIGNING_ALLOWED=NO, CODE_SIGNING_REQUIRED=NO, CODE_SIGN_IDENTITY="");
- empaquete el .app en Payload/ y lo comprima como Lumio-unsigned.ipa;
- lo suba con actions/upload-artifact con el sha en el nombre.
No metas ningún secreto ni certificado: la firma la hace cada uno en su PC con Sideloadly/AltStore.
```

### Prompt 2 · Pasos extra del runner (commit `58f77de`)

```text
El job falla porque el runner no sabe qué proyecto usar. Agrega al workflow:
- un paso que seleccione el Xcode instalado (xcode-select) antes de compilar;
- un paso que liste schemes y destinos (xcodebuild -list) para depurar desde el log;
- que el paso de compilar falle con un mensaje claro si no encuentra el .app en DerivedData.
```

### Prompt 3 · Proyecto definido sin Xcode (commits `3a050fe`, `80bffa3`)

```text
No queremos versionar el .xcodeproj: la mitad del equipo usa Windows/Linux y cada cambio al
pbxproj genera conflictos. Crea un project.yml de XcodeGen con:
- target de app iOS "lumio" (iOS 17+), bundle id del equipo, fuentes en Sources/LumioFrontend;
- target de tests con Tests/LumioFrontendTests;
- Info.plist generado y configuración Debug/Release.
Luego actualiza el workflow para instalar xcodegen con brew y correr
`xcodegen generate --spec project.yml` antes de compilar. Usa "lumio" como nombre del proyecto
en el yml y en el workflow.
```

### Prompt 4 · Estructura Swift Package (commit `5360efe`)

```text
Crea la estructura mínima para que el código portable compile con SwiftPM en cualquier máquina
(swift build / swift test), además de en Xcode:
- Package.swift con el target LumioFrontend y el target de tests LumioFrontendTests;
- Sources/LumioFrontend/LumioFrontend.swift con el @main de la app protegido para que SwiftPM
  en Linux no intente compilar SwiftUI;
- un test trivial que pase;
- .gitignore para .build, DerivedData, *.xcodeproj y xcuserdata.
```

### Prompt 5 · Esqueleto por funcionalidades (commit `1665163`)

```text
Ahora monta el esqueleto de la app para que cada integrante trabaje en su feature sin pisarse.
Organiza Sources/LumioFrontend así:
- App/: AppDependencies (composición de dependencias) y RootView;
- Core/: Errors/FeatureUnavailable y Networking/HTTPClient (solo comprueba códigos HTTP; sin
  auth, reintentos ni lógica offline);
- Features/<Audio|Narration|Navigation|Places|Safety|Settings|Users>/ con Domain/ y, solo
  donde haga falta, Data/ y Presentation/;
- Shared/UI/FeatureStatusView para mostrar qué funciones aún no están disponibles.
Define solo contratos de dominio (AudioMessage, AudioContracts, RoutePlan, SavedPlace,
SafetyContracts, UserProfile, NarrationDTO) y servicios "Unavailable" para que la app arranque.
Escribe docs/ARCHITECTURE.md explicando la estructura, reglas (un solo @main, no editar el
pbxproj, DTOs en Data/, tokens nunca en UserDefaults) y cómo probar con swift test.
Actualiza README.md con el arranque.
```

### Prompt 6 · Compilar e instalar desde Linux con xtool (commit `1b10ed3`)

```text
Para los que no tienen Mac, agrega soporte de xtool: xtool.yml con el bundle id y el nombre de
la app, el .bsp/xtool.json para que el editor resuelva el paquete, y ajusta Package.swift para
que xtool encuentre el producto. Ignora en git los artefactos de xtool.
```

### Prompt 7 · Guía de instalación y cierre

```text
Escribe en el README la guía de instalación sin Mac:
1. Descargar el artefacto Lumio-unsigned.ipa de la última corrida de GitHub Actions.
2. Instalar con Sideloadly o AltStore usando un Apple ID aparte para pruebas.
3. Activar Modo desarrollador (iOS 16+) y confiar en el perfil.
4. La firma gratuita dura 7 días y permite 3 apps: cómo renovarla.
5. Avisar que Sideloadly/AltStore pueden cambiar el bundle id (afecta el login con Google).
Antes de hacer público el repo, revisa el historial de commits buscando claves, tokens,
.env o certificados y dime qué encontraste.
```

## Verificación final

- El workflow genera el `.ipa` sin firmar en push y el artefacto aparece en la corrida.
- `swift test` pasa en Linux/macOS y `xcodegen generate` crea el proyecto sin tocar el pbxproj a mano.
- Pendiente de evidencia fuera del repo: instalación por dos integrantes sin Mac, login con Google
  en la app instalada y exportar registros sin Xcode.

## Commits cubiertos

| Commit | Fecha | Autor | Mensaje |
|---|---|---|---|
| `2178f5f` | 2026-10-09 | DanielPM | Pipeline compilation setup and distribution of ipa file |
| `58f77de` | 2026-10-09 | DanielPM | Adding aditional steps to Xcode setup |
| `3a050fe` | 2026-10-09 | DanielPM | Adding proyect yml to define the structure and configuration without Xcode |
| `5360efe` | 2026-10-09 | DanielPM | Creating swift project structure |
| `80bffa3` | 2026-10-09 | DanielPM | Changing project name in yml |
| `1665163` | 2026-10-25 | DanielPM | add: project scaffolding |
| `1b10ed3` | 2026-10-29 | DanielPM | build: Adding xtool setup to project |
