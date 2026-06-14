# MAPA — FJ App (fj-app)

> Referencia rápida del proyecto para no tener que re-explorar `index.html` (~1MB, ~9000 líneas) desde cero en cada sesión. Actualizar este archivo después de cambios estructurales relevantes (no hace falta para fixes chicos).

## Qué es

App single-file HTML (`index.html`) para FJ Desarrollos Inmobiliarios — gestión del proyecto "Los Eucaliptus" (~305 clientes/lotes). Roles: **Sacha admin / admin / colab**. Tipos de cliente: regular, agrimensor, colab.

- Deploy: GitHub Pages, repo `BassoMarcos/fj-app`, rama main, archivo `index.html` en la raíz.
- Sync: Firebase Realtime Database (`fj-app-44df3`) + Google Sheets (Apps Script) como backup.
- Token GitHub: guardado en memoria de Claude (no se incluye aquí por seguridad — GitHub bloquea pushes con tokens en texto plano).

## Estructura de páginas (divs `.page` / `#page-*`)

- `#page-home` — landing, selección de rol (`selectRole`, `openLoginModal`)
- `#page-public` — consulta pública de cuota (`initPublic`, `onPubEtapa`, `onPubMz`, `consultarCuotaPublica`)
- `#page-colab` — vista colaborador (`renderColab`, `mostrarDetColab`, `renderDetColab`, filtros `initCobFilters`/`initCobMzFilter`/`initCobLoteFilter`)
- `#page-admin` — panel admin, con tabs vía `adminTab(nombre)`:
  - `inicio` → `renderInicio` (resumen general)
  - `stats` → `renderStats` (estadísticas, gráficos)
  - `balances` → `renderBalances` (caja del día, cierres, agrimensores, gastos/ingresos)
  - `lista` → `renderAdminTable` (lista de clientes — tab principal, layout split con sidebar)
  - `historial` → `renderHistorial`
  - `datos` → export/import JSON (`exportarDatos`, `importarDatos`)
  - `icc` → incremento ICC (`renderIccStatus`, `aplicarICC`, `buscarICCIndec`/`buscarICCClaude`)
  - `morapanel` → `renderPanelMora` (gestión de mora)
  - `vistaclient` → `renderVistaCliente`

Modales globales relevantes: `#modal-clave` (pedir contraseña — `confirmarConClave`/`confirmarConClaveColab`), `#modal-edit` (alta/edición cliente), `#gestion-pagos-modal` (botón "✓ Pagos"), `#theme-panel` (selector de temas), `#confirm-modal-dyn` (creado dinámicamente por `showConfirmModal`).

## Modelo de datos (cada cliente, array `BASE` / `loadData()`)

Campos clave: `id` (ej `"M1-4B"`, `"ETAPA 2-3"`, `"E4-M1-9B"`), `mz` (manzana/etapa: `"M1".."M4"`, `"ETAPA 2"`, `"ETAPA 3"`, `"E4-M1".."E4-M5"`), `lote` (**puede ser number o string** — ver gotcha abajo), `titular`, `tri` (trimestre/planilla: Verde/Rosa/Azul), `ca` (cuota actual), `ct` (cuotas totales), `monto`, `saldo` (a favor/deuda, manual, independiente del pago), `est` (`"activo"`/`"finalizado"`), `moneda` (`ARS`/`USD`), `agrimensor` (bool), `autopago` (bool), `pago`/`pagoTs` (derivados de `pagoStore`, NO se guardan directos), `tel`, `dni[]`, `obs[]`, `hist[]` (histórico de cuotas pagadas), `primeraCuota`/`primeraCuotaAnio` (cliente pausado), `titulares[]`, `adicionalMonto`/`adicionalHasta` (escalonado).

`getEtapa(mz)` mapea manzana→etapa. Orden de manzanas/etapas: `M1→M2→M3→M4→ETAPA 2→ETAPA 3→E4-M1→E4-M3→E4-M4→E4-M5`.

## Constantes / passwords

- `ADMIN_PASS = 'fyj41252.0'`, `COLAB_PASS = 'fyj4125'`, `EDIT_PASS = 'm4rk14125'`
- `AGRIMENSOR_LOTES` — Set de ids con lote de agrimensor
- `FJ_THEMES` — 10 temas (incluye Cian profundo, Grafito & naranja, Lavanda oscuro, Acero azul, Ámbar negro), aplicados vía CSS variables con `applyFjTheme(t)`. Selector en navbar (`toggleThemePanel`).

## Sistema de pagos / caja (clave para entender bugs)

- `pagoStore` (Firebase/localStorage, prefijo `dKey('pagos')`) = mapa `{id: timestamp}`. `c.pago` y `c.pagoTs` en `loadData()` se DERIVAN de acá, no se guardan en `BASE`/`saveData`.
- `marcarPago(id, interesOverride)` — flujo normal de cobro individual (botón en ficha cliente/colab): marca `pagoStore`, y además **registra en caja** vía `registrarPagoEnCaja` (caja del día / `bal.abierto`) o `registrarPagoMora` (si tiene mora → caja de mora).
- `desmarcarPago(id)` — inverso: limpia `pagoStore`, sacar de `bal.abierto`/`bal.cierres`/mora/adelantos pendientes.
- **`abrirGestionPagos()` ("✓ Pagos")** — modal con grilla de lotes por etapa/manzana para marcar/desmarcar pagos en bloque (`gestionOnEtapa`, `gestionOnMz`, `gestionRenderLotes`, `gestionToggleLote`, `gestionGuardar`).
  - Toggle **"💰 Registrar en caja del día"** (`gestionToggleCaja`, var `_gpRegistrarCaja`, default OFF): si está OFF, `gestionGuardar` solo toca `pagoStore` (no afecta caja). Si está ON, por cada cambio real llama a `marcarPago`/`desmarcarPago` (mismo efecto que cobro individual, incluye caja/caja de mora).
  - Botones "Marcar todos como pagados"/"Desmarcar todos" → `gestionMarcarTodosConfirm(pago)`: muestra `showConfirmModal` con aviso (incluye nota si el toggle de caja está activo) y luego `confirmarConClave` (pide contraseña admin) antes de aplicar `gestionMarcarTodos`.
- `c.saldo` es un campo manual independiente (a favor/deuda inicial pactada), nunca se modifica por el flujo de pagos.
- "Caja" = `bal.abierto` (caja del día) + `bal.cierres` (cierres mensuales) + `bal.agrimensores`, todo dentro de `loadBalances()`/`saveBalances()`. Caja de mora aparte vía `loadMora()`/`saveMora()`.
- Cierre mensual: `ejecutarCierreFinal()` → avanza `ca` de todos los activos no pausados, genera mora para los que no pagaron, limpia `pagoStore`.

## Gotchas / convenciones importantes

- **`c.lote` puede ser `number`** para Etapa 2/3 (y algunos E4). Cualquier `.localeCompare`, `.toLowerCase()`, `===` contra un string del DOM debe envolver en `String()`. Ya fixeado en 5 lugares (`a.lote.localeCompare(b.lote,...)` → `String(a.lote).localeCompare(String(b.lote),...)`), pero si se agregan nuevos filtros/sorts por lote, aplicar el mismo patrón.
- `dKey('xxx')` prefija localStorage con `fj_eucaliptus_` (multi-desarrollo).
- Tabs admin usan nombres internos `'lista'`, `'mora'`, etc. — no `'clientes'`.
- `initCobFilters()` y similares deben llamarse DESPUÉS de que Firebase cargue datos, no en DOMContentLoaded directo.
- Confirmaciones custom: `showConfirmModal(titulo, msg, onConfirm, btnLabel?, btnColor?)` (creado en runtime, no usar `confirm()` nativo). Password: `confirmarConClave(accion)` (admin) / `confirmarConClaveColab(accion)` (colab).
- GitHub Pages cachea agresivamente — tras deploy, esperar unos minutos o `Ctrl+Shift+R`. `?v=N` solo sirve para verificar, no para forzar a todos los usuarios.

## Flujo de trabajo / deploy

1. Descargar `index.html` fresco del repo (GET contents API, decodificar base64).
2. Editar con Python (`str.replace` o similar), validar con `node --check` sobre el JS extraído de los `<script>`.
3. Subir con PUT (GET sha actual → PUT base64 nuevo contenido + sha + mensaje de commit descriptivo).
4. Avisar al usuario: `Ctrl+Shift+R` para ver el cambio.

## Changelog reciente

- Fix `lote.localeCompare` con `String()` en 5 funciones (incluye Gestión de Pagos) — resolvía que Etapa 2/3 no mostraran lotes en varios selectores.
- `showConfirmModal` ahora acepta `btnLabel`/`btnColor` configurables.
- Nueva `gestionMarcarTodosConfirm` — aviso + contraseña admin antes de marcar/desmarcar todos los pagos en bloque.
- Sistema de 10 temas con selector en navbar; fixes de contraste para tema oscuro en mora/ICC/adelantos/gastos.
