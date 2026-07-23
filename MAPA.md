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
- `AGRIMENSOR_LOTES_DEFAULT` — Set estático de 19 ids (seed/fallback). **Ya no usar `AGRIMENSOR_LOTES` directo.**
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

## Agrimensores — sistema dinámico (v1.0298+)

- `loadAgrimensorLotes()` → `Set` de ids. Fuente: `dKey('agrimensorLotes')` en localStorage/Firebase. Si vacío, usa `AGRIMENSOR_LOTES_DEFAULT` (seed de 19 ids).
- `saveAgrimensorLotes(set)` → guarda en localStorage + Firebase (`_fbSet('agrimensorLotes',arr)`).
- `toggleLoteAgrimensor(loteId, makeAgri)` → agrega/quita lote del Set, persiste, y si el cliente existe setea `c.agrimensor`.
- `esAgrimensor(id)` → `loadAgrimensorLotes().has(id)` (antes era `AGRIMENSOR_LOTES.has(id)` estático).
- `esLoteAgrimensor(etapa,mz,lote)` → `loadAgrimensorLotes().has(id)` (antes chequeaba `LOTES_LIBRES_E4[id]===true`).
- `LOTES_LIBRES_E4` sigue existiendo como inventario de lotes disponibles E4 (sólo sus keys importan; los booleans ya no definen qué es agrimensor).
- Firebase init carga `agrimensorLotes`; listener actualiza localStorage y re-renderiza `balances` en tiempo real.
- UI: Balances → ⚖️ Agrimensores → botón **⚙️ Gestionar lotes** → `renderBalances('agr-gestionar')` — lista actual con "✗ Quitar" y form "+ Agregar lote".

## Lotes vacantes E1/E2/E3 (v1.0298+)

- **`loadLotesLibresE123()`/`saveLotesLibresE123()`** — Set persistido (Firebase-synced) de lotes que quedaron vacantes al eliminar un cliente de M1/M2/M3/M4/ETAPA 2/ETAPA 3.
- `delCliente()` ahora llama `agregarLoteLibreE123(c.id)` si el lote pertenece a esas manzanas.
- `getLotesDisponibles(etapa,mz)` actualizado: para `etapa==='E1'/'E2'/'E3'` ahora lee de `loadLotesLibresE123()` (antes devolvía `[]` siempre).
- `getManzanasPorEtapa('E1')` ahora también cuenta lotes libres (antes solo E4).
- `renderSelectorManzana()` muestra sub-manzanas M1-M4 para E1 igual que E4-M1...M5.
- Al guardar nuevo cliente (`saveCliente`), cada lote asignado se quita de la lista de vacantes vía `quitarLoteLibreE123(lId)`.

## Lotes Finalizados — vista + certificados (v1.0298+)

- Nuevo tab **"🏁 Lotes Finalizados"** en la barra de navegación admin (`adminTab('terminados')` → `atab-terminados` → `renderLotesTerminados('terminados')`).
- También accesible desde Estadísticas vía botón compacto que llama `adminTab('terminados')`.
- **`loadLotesCerts()`/`saveLotesCerts()`** — Firebase-synced, key `lotesCerts`. Por lote: `{fecha, certSolicitado, certRecibido, certEntregado, urgente}`.
- `renderLotesTerminados(origen)` — agrupa en acordeones por etapa (Etapa 1: M1→M2→M3→M4; Etapa 2; Etapa 3; Etapa 4: **orden invertido M5→M4→M3→M2→M1**, igual que el resto de la app; Préstamos al final). Cerrados muestran chips verdes con los IDs; al abrir, fila por lote con fecha editable y 3 botones de certificado + urgente.
- Estado de acordeones/filas abiertas se preserva entre re-renders (guardado antes de `innerHTML=html`, restaurado después) — necesario porque cada toggle de certificado re-renderiza toda la vista.
- **Auto-finalización**: `marcarPago()` detecta `c.ca>=c.ct` tras el pago → setea `c.est='finalizado'` automáticamente, registra fecha en `lotesCerts`, muestra toast "🏁 ¡Última cuota! Lote finalizado". El cliente sale solo del cobro/cierre/mora y aparece en Lotes Finalizados sin acción manual.
- Resumen agregado en `renderStats()`: cards de Terminaron/Préstamos/Urgentes + Sin cert. entregado/Cert. entregado.
- **Lotes "préstamo"** = `est:'finalizado'` + `autopago:true`. Son lotes 100% pagados por el cliente pero cuya plata FJ tomó prestada de los dueños del campo; FJ les devuelve mes a mes. Funcionan como cualquier lote (reciben ICC), la ÚNICA diferencia es que `autopago` los excluye del cierre mensual (no generan mora, no se cobran). `aplicarICC` y su preview (`iccPctEditado`) ahora SÍ los incluyen (antes solo filtraba por `est==='activo'`).

## ICC — rediseño completo del flujo (v1.0298+)

Rediseño basado en la lógica real del negocio, conversada y confirmada con el usuario tras detectar que el ICC de Mayo 2026 no se aplicó a 10+ clientes (M2-17A entre ellos) por una doble-lectura de `loadData()` con posible carrera con Firebase.

**Lista 1 — ICC mensual individual** (nueva, independiente de si se aplicó algo):
- `loadIccMensual()`/`saveIccMensual()` — Firebase-synced, key `iccMensual`.
- `registrarIccMensual(mesIdx, anio, pct)` — guarda/actualiza `{mesKey, mes, anio, pct, ts}`. Se llama automáticamente desde `buscarICCClaude()` y `buscarICCIndec()` cuando encuentran un dato válido nuevo, y también desde `aplicarICC()` con el % tipeado manualmente.
- `getIccMensual(mesIdx, anio)` / `trimestreCompletoEnLista1(mesIdx, anio)` — verifica si el mes en curso + los 2 anteriores están registrados.

**Lista 2 — Incrementos trimestrales aplicados** = el `loadICC()`/`saveICC()` que ya existía, sin cambios de estructura.

**`aplicarICC()` — 2 candados nuevos antes de cualquier cálculo:**
1. Cierre final del mes en curso (`loadCierreFinal()`, comparado contra mes/año de HOY, no contra el cierre más reciente cualquiera) debe estar hecho → si no, alert explicativo y `return`.
2. Lista 1 debe tener los 3 meses consecutivos (mes en curso + 2 anteriores) → si falta alguno, alert con los nombres de los meses faltantes y `return`.

**Cambio de lógica de color**: el trimestre/planilla a incrementar se determina por el **mes SIGUIENTE** al mes en curso (`ICC_MAP[(mesEnCurso+1)%12]`), NO por el mes del cierre final como antes (eso era ambiguo/incorrecto). El total trimestral se calcula sumando los 3 valores reales de Lista 1, no leyendo el dataset de `icc-apply-btn` ni recalculando contra el historial de aplicados.

**Bug eliminado**: la función hacía `loadData()` dos veces (`data` para contar, `d` para aplicar) — sospechoso de ser la causa de clientes que quedaban afuera del incremento por sincronización de Firebase entre ambas lecturas. Ahora usa una sola lectura (`data`) para contar y aplicar.

**`iccPctEditado()`** (preview en vivo mientras se tipea el %) corregido para usar la misma lógica: mes siguiente para el color, conteo incluye préstamos (`est==='finalizado'&&autopago`), suma desde Lista 1 en vez de `getIccDeHistorial` (que solo encontraba meses con trimestre YA aplicado, no meses individuales sueltos).

## Agrimensores en mora (v1.0298+)

- **`registrarCobroCuotaMora(mora, c, interes, ts, fecha)`** — helper centralizado para los 3 sitios de cobro de mora (panel admin, colab, modal flujo) y `registrarPagoMora`. Si `esAgrimensor(id)` → `entry.cuota=0`, `entry.cuotaAgrimensor=c.monto`, y la cuota pura va a `bal.agrimensores`. El interés queda en el entry de mora igual que cualquier cliente (para ser transferido a extras vía `pasarInteresMora`).
- `cuotaAgrimensor` — campo opcional en entries de `mora[]`. Presente sólo para lotes agrimensor. En el display de "Caja de Mora" aparece como "Cuota (⚖️ Agr.): $X" en lugar de "Cuota: $0".
- **Cierre final**: removida exclusión `||c.agrimensor` en los 3 sitios de generación de mora (`ejecutarCierreFinal`, `borrarCierreFinalYReaplicar`, `hacerCierreFinal`). Ahora los lotes agrimensor que no pagaron entran a mora igual que cualquier cliente.



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

- **v1.0379–v1.0380 (22/7/2026) — INCIDENTE DE PÉRDIDA DE DATOS Y NUEVO MOTOR DE SINCRONIZACIÓN**:
  **Qué pasó**: abrir la app en una ventana de incógnito (que arranca con localStorage vacío y baja la versión de Firebase) disparó el listener `_fbListen('data')` en la ventana principal, que **sobrescribió los datos buenos con la versión de Firebase congelada en abril**. Se perdieron: cuotas de mayo/junio/julio de 244 clientes, 14 lotes de Etapa 4 cargados el 7/7, los 3 adelantos de julio y la lista `adelantos`.
  **Causa raíz**: `saveData` y todas las `save*` sólo subían a Firebase `if(window._firebaseReady)` y con `.catch(console.warn)` — si Firebase no estaba listo o la red fallaba, **el cambio quedaba sólo en ese navegador y nadie se enteraba**. `data` dejó de subir en abril y estuvo 3 meses desincronizado en silencio. `saveCierreFinal` directamente nunca sincronizó (arreglado en v1.0379).
  **Recuperación** (vía consola, sin tocar el código): el `addHist` de cada pago guarda `"Pago — {mz} Lote {lote} — {titular} — Cuota N/T — $monto"`, lo que permitió reconstruir `ca` (= última cuota pagada + 1) y el `hist` de 244 clientes; los 12 lotes E4 se reconstruyeron desde los pagos + `cuotasMora` (que sí guarda `totalCuotas`, `monto` y `moneda`); los adelantos se reaplicaron restando cuotas al `ct` (así funciona `aprobarAdelanto`: descuenta de `ct`, NO toca `ca`); los 2 lotes sin pagos ni mora (E4-M4-12A/12B) se cargaron a mano desde la planilla. Resultado: 318 clientes / 287 activos, todo verificado en Firebase.
  **Motor nuevo (v1.0380)**: (1) **cola de pendientes** `window._syncQueue` — `_fbSet` encola SIEMPRE y luego intenta subir; nada se pierde si Firebase no está listo. (2) **Reintento automático** cada 8s + al evento `online`. (3) **Indicador visual** `#sync-indicator` en el topbar (verde "Sincronizado" / naranja "Guardando N…" / rojo "Conflicto"), clickeable → `mostrarEstadoSync()`. (4) **Protección anti-pisado** en el listener de `data`: si la versión remota tiene menos clientes o >2 cuotas atrasadas respecto de la local, **se rechaza**, se avisa al usuario y se re-sube la local. (5) **`beforeunload`** avisa si se cierra la app con cambios sin subir. (6) Las 11 `save*` migradas a la cola.
  **Pendiente**: completar DNI/teléfono/fecha de firma de los 12 lotes E4 reconstruidos.

- **v1.0356–v1.0371 (22/7/2026) — Rediseño completo de Mora + Informes PDF**:
  (1) **Panel de Mora agrupado por CLIENTE** (antes por mes): jerarquía desplegable Etapa ▸ Manzana ▸ Lote con subtotales en CP en los encabezados (alineados con su columna), dos vistas alternables con preferencia guardada en `fj_mora_vista`: "compacta" (bloques desplegables) y "lista" (plana ultra densa estilo planilla). Desglose por cuota con 5 columnas: Cuota pura | Días (a hoy) | % interés | Interés | Total. Buscador global que encuentra lotes aunque su bloque esté cerrado (matchea formato con guion). Flujo de cobro intacto (ids `adm-mora-*`, `onAdmMoraCheck`, `cobrarAdmMora`).
  (2) **Header del panel**: "Total adeudado" muestra solo cuota pura; la burbuja de la pestaña Mora cuenta LOTES en mora (no cuotas).
  (3) **Caja de Mora agrupada por lote**: línea resumen con badge de cantidad de cuotas + detalle desplegable; botón "→ Pasar intereses a Extras" que pasa TODOS los intereses pendientes del lote a Ingresos en una sola operación (`pasarInteresesGrupo`, marca `interesEnExtras` en cada pago).
  (4) **Modales altos con scroll interno** (max-height:90vh) — fix para cobros con muchas cuotas.
  (5) **Informe PDF individual para Legales** (`generarInformeMora`): botón en el desglose de cada moroso; jsPDF + autotable cargados on-demand desde cdnjs; incluye datos del cliente, último pago, resumen de deuda, tabla completa y gráfico de barras apiladas capital+interés. Parámetro `soloTest` devuelve tamaño sin descargar.
  (6) **Informe mensual general** (`generarInformeMensual`): botón "📊 Informe mensual" en el header del panel; KPIs del mes cerrado, torta pagaron/mora, barras de deuda CP por etapa, tablas por etapa y manzana, lista simplificada de morosos, cobranza del mes (hist) + mora cobrada últimos 30 días.
  (7) **Deuda histórica cargada**: 216 cuotas viejas (May 2024–Abr 2026) importadas desde planilla PDF a `cuotasMora` con `dia10Ts` original — el interés 2%/día se calcula automático al cobrar.

- **v1.0354/55 (21/7/2026)** — FIX CRÍTICO del cierre final: `ejecutarCierreFinal` y `hacerCierreFinal` tenían un bloque que borraba `pagoStore` ANTES de leer quién pagó (si existía un cierre anterior) → todos aparecían impagos y se generaba mora masiva (rompió los cierres de junio y julio 2026). Eliminado. Además: (1) `saveSnapshot`/`revertirCierre` corregidos — antes leían/escribían claves equivocadas (`pago_store` vs `pagos`, `cuotas_mora` vs `fj_cuotas_mora`, etc.) y no sincronizaban a Firebase; ahora la foto es completa y el revertir usa las funciones `save*`. Solo sirve para cierres hechos desde v1.0354, desde el mismo dispositivo. (2) `repararCierreJunio2026` DESACTIVADA (auto-run comentado) — era parche de una sola vez y al quedar activa renombraba cualquier cierre legítimo de Julio 2026 a Junio, corrompiendo moras e historial. (3) Cierre de julio 2026 revertido y rehecho con éxito por script (244 pagos restaurados desde cajas, 282 moras falsas eliminadas). (4) Cargadas 216 cuotas de deuda histórica (May 2024–Abr 2026, 20 lotes morosos) a `cuotasMora` desde planilla PDF, con `numeroCuota = ca-1-(mesesAtrás)` y `dia10Ts` original para que el interés 2%/día se calcule automático.
- **v1.0298** — Sesión grande: (1) Agrimensores reciben mora correctamente + lista dinámica de lotes agrimensor con UI de gestión. (2) Lotes vacantes E1/E2/E3 al eliminar cliente, reutilizables en selector de nuevo cliente. (3) Tab nuevo "Lotes Finalizados" con certificados de firma, urgencias, y auto-finalización al pagar la última cuota. (4) Préstamos (finalizado+autopago) ahora reciben ICC. (5) Rediseño completo del flujo ICC: Lista 1 (mensual individual) + 2 candados (cierre final hecho + trimestre completo) + fix de bug de doble loadData() que causaba clientes excluidos del incremento.
- Fix `lote.localeCompare` con `String()` en 5 funciones (incluye Gestión de Pagos) — resolvía que Etapa 2/3 no mostraran lotes en varios selectores.
- `showConfirmModal` ahora acepta `btnLabel`/`btnColor` configurables.
- Nueva `gestionMarcarTodosConfirm` — aviso + contraseña admin antes de marcar/desmarcar todos los pagos en bloque.
- Sistema de 10 temas con selector en navbar; fixes de contraste para tema oscuro en mora/ICC/adelantos/gastos.
