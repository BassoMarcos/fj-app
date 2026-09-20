# CLAUDE.md — FJ App (BassoMarcos/fj-app)

> Contexto maestro del proyecto para Claude. Leer esto ENTERO al iniciar cualquier sesión, junto con `MAPA.md` (fuente de verdad arquitectónica) e `index.html`.

## Qué es

- App de **administración de pagos de propiedades** de F&J Desarrollos Inmobiliarios.
- Proyecto de loteo administrado: **"Los Eucaliptus"** — ~321 lotes en Etapas 1–4 con varias manzanas.
- **Un solo archivo `index.html`** (~1MB, ~9000 líneas) en vanilla JS con JS inline. Es la herramienta operativa principal hoy.
- Deploy: **GitHub Pages** (repo `BassoMarcos/fj-app`, rama `main`, `index.html` en la raíz).
- Datos: **Firebase Realtime Database** (`fj-app-44df3-default-rtdb.firebaseio.com`) + Google Sheets (Apps Script) como backup.
- Roles de usuario: **admin** y **colaborador**.
- Marcos es **empleado administrativo** de F&J Desarrollos (no el dueño) y es quien creó esta app (y MasterPlan) desde cero junto con Claude. fj-app es el **área administrativa** que después migra a MasterPlan.
- Marcos NO tiene formación técnica: depende de Claude para escribir y deployar todo el código. Comunicación en español rioplatense, directo y analítico.

## Módulos operativos (todos funcionando)

- Cuotas mensuales, mora, ajustes ICC, cierres.
- Caja Física, Caja del día, Caja de Mora, Cierres de Transferencias.
- Adelantos (con historial permanente), agrimensores (con separación de mora).
- Sistema de notificaciones de mora (reemplazó las aprobaciones pendientes).
- Extras con rendido/reactivación; calendario de Ventas.
- Concepto de recorrido de 8 etapas; workflow de cierre final.
- Backup/restore con backup mensual obligatorio antes de cobro y de cierre.
- Protecciones de sync multi-dispositivo.
- Panel de Lotes Finalizados con seguimiento de certificados.

## Reglas de negocio confirmadas (LEER antes de tocar lógica de pagos)

- **Efectivo físico** = valor del campo `entregó` (el vuelto NO se resta).
- **CP** = `montoCobrable(c).total`.
- **Interés del mes** → Caja de Mora; **cuota pura** → Caja del día.
- Después del **cierre final**, todo lo vencido cae a Caja de Mora.
- **Lotes en USD nunca reciben ICC.**
- **Préstamos** (`autopago:true`, `est:finalizado`): reciben ICC y avanzan números de cuota, pero se **excluyen** de los cierres mensuales y de los balances.
- La categoría **`empresaPaga`** (ej. Retamozo ETAPA 3-53) es distinta de los préstamos.
- **Mora arranca el día 11** del mes operativo.
- A la caja de mora se le aplica un **split 30%/70%**.

## Gotchas críticos (romper esto causa bugs silenciosos)

- **Regla de `loadData()`**: CADA campo nuevo de cliente debe agregarse en **AMBAS** normalizaciones — la reconstrucción campo por campo (~línea 1209) Y el `full.map` (~línea 1274). Omitir cualquiera de las dos causa pérdida silenciosa del campo en cada carga.
- **12 lotes de Etapa 4** con ICC mal asignado (primera cuota julio 2026, la cuota 3 cae en septiembre): deberían ser trimestre **Rosa**, no **Azul**. `calcTrimestrePorCuota` asigna el trimestre equivocado al momento de cargar. (Pendiente de resolver.)
- Archivo enorme: navegar con búsquedas `grep -n` puntuales por nombre de función, no leer rangos gigantes.

## Trabajo de integridad de datos ya hecho

- Reparados los huecos en el historial de cuotas; numeración corregida.
- Identificada la mala asignación de ICC de los 12 lotes de Etapa 4 (arriba).

## Flujo de deploy

1. Editar `index.html`.
2. Validar sintaxis JS con `node --check` (extraer los `<script>` a un temp y chequear).
3. **Incrementar el número de versión** (rango actual v1.06xx).
4. Deployar a `main`.
5. Hard refresh en el navegador (`Ctrl+Shift+R`) — GitHub Pages cachea agresivo.
6. Actualizar **`MAPA.md`** en el mismo lote que cambios estructurales de código.

## Robot ICC

- Un robot de **GitHub Actions** (Playwright, espera 15s por el SPA de INDEC) corre a diario y guarda en **`icc-data.json`** en este repo.

## Cómo trabaja Marcos

- Respuestas concisas, sin explicaciones largas salvo que las pida.
- Todo el código completo y listo para copiar y pegar.
- Quiere **preview antes** de implementar cualquier cambio de cobro o sensible a datos.
- Verifica totales contra las planillas físicas de Excel/PDF (fuente de verdad): siempre cruzar contra eso al diagnosticar diferencias; nunca asumir que la app está bien sin verificar.
- Retoma exactamente donde quedó, sin re-explicar contexto al inicio.

## Nota sobre acceso a GitHub (contexto de migración, sep-2026)

- Este repo se está migrando a **Claude Code** (claude.ai/code) porque las sesiones tipo Cowork/nube quedaron con un proxy de git que bloquea `push` ("not in this session's authorized repository set"). En Claude Code, con el repo agregado como fuente, el push/deploy funciona normal.
- **Nunca** poner tokens de GitHub en archivos del repo (el secret scanning bloquea el push). Los tokens van en la memoria de Claude, no acá.

## Estrategia a largo plazo

- FJ App eventualmente migra módulo por módulo al pilar **Administración** de MasterPlan (repo `masterplan-management`). Primero se terminan todas las features administrativas de FJ App, después se integra.
- Mapa neuronal interactivo (`mapa.html` + `mapa-data.json`, en el repo de MasterPlan) conecta ambos sistemas y es accesible desde ambas apps con el botón 🧠.
