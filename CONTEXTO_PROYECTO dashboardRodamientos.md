# Contexto del Proyecto — Dashboard de Rodamientos (SEG Ingeniería)

> Documento de traspaso para continuar en otro chat. Contiene todo lo necesario
> para retomar el proyecto sin perder contexto. **Etapas 1–5 completas con mejoras.
> Próximo paso: Etapa 6 (Deploy Railway).**

---

## 1. Qué es el proyecto

Sistema para generar **dashboards de seguimiento de rodamientos** de dos parques eólicos,
a partir de Excels que se cargan mes a mes. Los datos se acumulan en una base de datos
(el dashboard "crece" con cada carga) y se puede exportar un HTML standalone para entregar
al cliente.

**Los dos parques:**
- **Cerro Grande (CG)** — 22 turbinas, código interno `WEC01`–`WEC22`
- **Peralta I (PSP)** — 50 turbinas, código interno `PSP-01`–`PSP-50`

---

## 2. Decisiones de arquitectura ya tomadas (y por qué)

### Separación de ambientes
- **Desarrollo:** Docker local con PostgreSQL.
- **Producción:** Railway. Pendiente de configurar (Etapa 6).

### Entregable al cliente
- HTML standalone que se abre **sin internet**, con los datos embebidos como JSON.
- Es un snapshot generado desde la DB en el momento de exportar.
- El sistema interno (con persistencia y edición) y el export son **dos cosas separadas**.
- El standalone usa tema claro con la identidad visual de **SEGHeliotec** (logo embebido,
  rojo `#E41714`, barra de pie en los tres colores de la hoja membretada).

### Separación por capas (alta cohesión, bajo acoplamiento)
```
app/
├── modelos/        ← define las tablas (SQLAlchemy), nada más
├── repositorios/   ← todas las queries (acceso a datos)
├── servicios/      ← lógica de negocio, ETL, orquestación
├── etl/            ← parsers de Excel
├── rutas/          ← API FastAPI
├── templates/      ← standalone.html (template del export)
└── database.py     ← conexión
```

### Convención de idioma
- **TODO en español**: variables, clases, funciones, comentarios, URLs de la API.
- Sin acentos en identificadores de código.

### Modelo de warnings: solo agregados (NO eventos crudos)
Se guardan **conteos agregados**, no eventos individuales. Dos tablas:
- `warnings_por_mes` — conteo por (turbina, mes, anio). `mes`/`anio` siempre tienen valor.
- `warnings_por_tipo` — conteo por (turbina, tipo, mes, anio). **`mes`/`anio` pueden ser NULL**
  solo para el seed histórico de Peralta (que no tiene granularidad de fecha por tipo).
  Los datos cargados desde logbook ROTORsoft siempre tienen `mes`/`anio`.

---

## 3. Estado actual: Etapas 1–5 COMPLETAS

### Etapa 1 ✓ — Base de datos
5 tablas: `parques`, `turbinas`, `cargas`, `inspecciones_rodamientos`,
`warnings_por_mes`, `warnings_por_tipo`. SQLAlchemy + Alembic aplicado.

### Etapa 2 ✓ — ETL
Probado end-to-end con los Excels reales. Resultados de la última corrida:
```
Seed CG          → 22 inspecciones
Seed PSP         → 50 inspecciones
Warnings PSP     → 404 conteos por mes + 108 por tipo (histórico 2025, sin fecha de tipo)
Logbook CG abril → 22 eventos → 3 conteos/mes + 4 conteos/tipo (con mes/anio)
Logbook PSP abril→ 30 eventos → 7 conteos/mes + 10 conteos/tipo (con mes/anio)
Control mensual CG y PSP → cargas de inspecciones desde Nuevo_Control_De_Rodamientos
```
DB: 72+ inspecciones, 414 warn_mes, 122 warn_tipo, 5+ cargas.

**Fixes aplicados al ETL:**
- `parser_rodamientos.py` → `_a_fecha()` maneja tanto `YYYY-MM-DD` como `DD/MM/YYYY` (strings)
  y también `datetime`/`date` de openpyxl. Sin esto PSP-06 mostraba fecha incorrecta.
- El control mensual (`Nuevo_Control_De_Rodamientos`) ahora se carga para ambos parques
  desde los Excels actualizados en la raíz del proyecto.

### Etapa 3 ✓ — API FastAPI
Todos los endpoints funcionando en `localhost:8000`:

```
GET    /parques                        → lista de parques
GET    /resumen/{codigo_parque}        → contadores A/B/C/D + warnings por mes y tipo (con mes/anio)
GET    /mapa-estado/{codigo_parque}    → grid de turbinas con última inspección
GET    /turbina/{id}                   → detalle: inspecciones + warnings mes/tipo (con mes/anio)
PUT    /inspeccion/{id}                → editar una inspección (tipo, categorías, comentarios)
DELETE /inspeccion/{id}                → eliminar una inspección individual
GET    /admin/cargas/{codigo_parque}   → historial de cargas
POST   /admin/cargar                   → subir Excel (multipart/form-data)
DELETE /admin/carga/{id}               → revertir una carga completa
GET    /exportar/{codigo_parque}       → descarga HTML standalone con datos embebidos
```

**Cambio importante en `/resumen/{parque}`:** `warnings_por_tipo` devuelve filas individuales
con `{tipo, cantidad, mes, anio}` (para filtrado client-side), NO totales pre-agregados.
La agregación la hace el cliente con `agregarPorTipo()`.

### Etapa 4 ✓ — Dashboard interactivo (con mejoras)
`app/dashboard.html`. Tema dark, 4 pestañas:

- **Resumen**: contadores A/B/C/D + filtro de período (Desde/Hasta) +
  gráfico de barras **apilado por tipo** (stacked bar Plotly) + breakdown horizontal por tipo.
- **Mapa Estado**: grid de turbinas con badges de categoría. Click lleva a Por Turbina.
- **Por Turbina**: sidebar + detalle con:
  - **Header**: nombre turbina + badge "N warnings" + pills de top tipos + categorías Del/Tras + fecha última inspección.
  - Filtro de período (Desde/Hasta).
  - **Gráfico principal** (ancho completo, 270px): barras **apiladas por tipo** de warning +
    **línea vertical verde punteada** en el mes de cada inspección/mantenimiento con el nombre del evento.
    Meses sin desglose de tipo muestran segmento gris "Sin desglose".
    Anotaciones con el total bajo cada barra.
  - Layout 2 columnas: **Breakdown por subgrupo** (horizontal bar) | **Historial inspecciones** (tabla editable).
- **Administración**: formulario de carga de Excels + historial con opción de revertir.
- Botón **Exportar HTML** en el header.

#### Helpers JS clave en `dashboard.html`
```js
// Estado global
let resumenDataRaw = null;   // { warnings_por_mes, warnings_por_tipo, contadores }
let turbinaDataRaw = null;   // { warnings_por_mes, warnings_por_tipo, inspecciones }

// Constantes
const TYPE_COLORS = ['#38bdf8','#818cf8','#f472b6','#34d399','#fb923c','#a78bfa','#fbbf24'];
const MESES = ['','Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

// Helpers de fecha
parseMes(str)               // "YYYY-MM" → [anio, mes] | null
mesKey(anio, mes)           // anio * 100 + mes (clave única para comparaciones)
mesLabel(mes, anio)         // → "Abr 2025"

// Filtrado
filtrarPorRango(arr, desdeStr, hastaStr)  // excluye mes=null cuando hay filtro activo
rellenarMeses(arr, campo)                 // rellena con 0 los meses faltantes entre min y max
rangoStr(arr)               // → {min: "YYYY-MM", max: "YYYY-MM"} del rango de datos

// Agregación
agregarPorTipo(arr)         // suma cantidad por tipo → [{tipo, total}] ordenado alfabéticamente
tipoConFechaAgrupar(arr)    // agrupa {tipo, mes, anio, cantidad} sumando por turbina (para resumen)
abrevTipo(tipo)             // "Lub. Sin presión" → "Lub"

// UI
filterBarHTML(idDesde, idHasta, min, max)  // genera HTML del filtro de período
limpiarFiltro(idDesde, idHasta)
onFiltroChange(idDesde, idHasta)           // despacha a renderResumenCharts o renderTurbinaCharts

// Render
renderResumenCharts(desdeStr, hastaStr)    // stacked bar parque + breakdown
renderTurbinaCharts(desdeStr, hastaStr)    // stacked bar turbina + inspection lines + breakdown
```

#### Lógica del gráfico apilado (stacked chart)
1. `mesFiltrado` viene de `rellenarMeses(filtrarPorRango(warnings_por_mes, ...), 'cantidad')` → timeline con 0s.
2. `tipoChart` = `warnings_por_tipo` filtrado por rango + excluidos `mes=null`.
3. Un trace Plotly por tipo (color de `TYPE_COLORS` indexado por orden alfabético).
4. Para meses sin desglose de tipo: segmento extra "Sin desglose" en gris `#3d4a5c`
   (diferencia entre total de `warnings_por_mes` y suma de tipos con fecha).
5. Líneas de inspección: `shapes` Plotly con `x0=x1=mesLabel(mes,anio)`, `yref='paper'`,
   color `#22c55e`, `dash='dash'`. El label del evento va en `annotations` con `textangle=-90`.
6. Si no hay tipo con fecha → fallback a barra sólida `#38bdf8` con todos los totales.

**Limitación conocida (PSP):** El seed histórico de Peralta tiene `mes=null` en `warnings_por_tipo`.
Esos meses muestran "Sin desglose" (gris). Los meses cargados desde logbook ROTORsoft tienen
fecha y se muestran con colores. Se acumulará correctamente con cada nueva carga mensual.

### Etapa 5 ✓ — Export standalone HTML (con mejoras)
`app/templates/standalone.html` — template con placeholder `__DASHBOARD_DATA__`.

**Cambios en `exportar.py`:** Ahora pasa filas individuales `{tipo, cantidad, mes, anio}` en
`warnings_por_tipo` (tanto por turbina como en el resumen), en lugar de totales pre-agregados.
Esto permite que el standalone calcule el desglose por tipo correctamente.

**Nuevas funciones JS en `standalone.html`:**
```js
mKey(m, a)                              // a * 100 + m (clave mes)
agregarPorTipo(arr)                     // suma por tipo (igual que dashboard)
rellenarMeses(mesData, campo)           // rellena huecos con 0
abrevTipo(tipo)                         // abrevia nombre de tipo
svgVBarStacked(mesData, campo, tipoData, inspecciones)  // SVG de barras apiladas
  // - campo: 'cantidad' para turbina, 'total' para resumen
  // - tipoData con mes/anio para stacked; mes=null queda en "Sin desglose" gris
  // - inspecciones: línea verde punteada SVG en el mes del evento
  // - retorna SVG + leyenda de colores HTML (no requiere Plotly)
svgHBar(vals, labels)                   // SVG de barras horizontales (ya existía)
SVG_COLORS = [rojo, azul, naranja, ...]  // paleta para tipos
```

**Layout del standalone actualizado:**
- Turbina: header con "N warnings" + pills de tipo + cats + chart stacked (full width) + 2 col abajo
- Resumen: mismo gráfico stacked para el parque

---

## 4. Esquema de la base de datos

### Tabla `parques`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| nombre | String(100) | "Cerro Grande" |
| codigo | String(10) unique | "CG", "PSP" |
| cantidad_turbinas | Integer | |
| fecha_creacion | DateTime | UTC |

### Tabla `turbinas`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| parque_id | FK→parques | |
| codigo | String(20) | "WEC01", "PSP-01" |
| numero | Integer | 1..22 ó 1..50 |
| activa | Boolean | default True |

### Tabla `cargas`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| parque_id | FK→parques | |
| tipo_archivo | String(20) | "seed_rodamientos", "control_mensual", "logbook", "seed_warnings" |
| nombre_archivo | String(255) | |
| fecha_carga | DateTime | UTC |
| estado | String(20) | "exitosa", "fallida", "revertida" |
| registros_insertados | Integer | |
| notas | String(500) nullable | |

### Tabla `inspecciones_rodamientos`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| turbina_id | FK→turbinas | |
| carga_id | FK→cargas | |
| fecha | Date | |
| tipo_evento | String(100) | "Mant. Master 2025", "Insp. Rodamiento", etc. |
| categoria_delantera | String(5) | "A","B","C","D","ND" |
| categoria_trasera | String(5) | |
| cambio_rodamiento_delantero | Date nullable | |
| cambio_rodamiento_trasero | Date nullable | |
| comentarios | String(500) nullable | |
| fecha_creacion | DateTime | UTC |
| UNIQUE | (turbina_id, fecha) | |

### Tabla `warnings_por_mes`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| turbina_id | FK→turbinas | |
| carga_id | FK→cargas | |
| mes | Integer | siempre presente |
| anio | Integer | siempre presente |
| cantidad | Integer | |
| UNIQUE | (turbina_id, mes, anio) | |

### Tabla `warnings_por_tipo`
| Columna | Tipo | Notas |
|---------|------|-------|
| id | Integer PK | |
| turbina_id | FK→turbinas | |
| carga_id | FK→cargas | |
| tipo | String(100) | "Grasa vacio", "Lub. Sin presion", etc. |
| mes | Integer nullable | **null = seed histórico Peralta (sin granularidad de fecha)** |
| anio | Integer nullable | |
| cantidad | Integer | |
| UNIQUE | (turbina_id, tipo, mes, anio) | |

---

## 5. Estructura de archivos relevante

```
rodamientos-dashboard/
├── app/
│   ├── database.py
│   ├── modelos/
│   │   ├── parque.py, turbina.py, carga.py
│   │   ├── inspeccion_rodamiento.py
│   │   ├── warning_por_mes.py, warning_por_tipo.py
│   ├── repositorios/
│   │   ├── repositorio_parque.py
│   │   ├── repositorio_turbina.py
│   │   ├── repositorio_carga.py
│   │   ├── repositorio_inspeccion.py      ← incluye obtener_todas_por_parque
│   │   ├── repositorio_warning_por_mes.py ← incluye obtener_todas_por_parque
│   │   ├── repositorio_warning_por_tipo.py← incluye obtener_todas_por_parque
│   ├── servicios/
│   │   └── servicio_carga.py
│   ├── etl/
│   │   ├── parser_rodamientos.py          ← _a_fecha() maneja ISO y DD/MM/YYYY
│   │   ├── parser_logbook.py
│   │   ├── parser_warnings_peralta.py
│   │   └── agregador_warnings.py
│   ├── rutas/
│   │   ├── parques.py, mapa_estado.py
│   │   ├── resumen.py                     ← warnings_por_tipo con mes/anio por fila
│   │   ├── turbina.py, inspecciones.py
│   │   ├── admin.py
│   │   └── exportar.py                    ← exporta tipo con mes/anio (no pre-agregado)
│   ├── templates/
│   │   └── standalone.html                ← SVG stacked charts, offline, tema claro SEGHeliotec
│   ├── dashboard.html                     ← frontend interno (dark theme, Plotly)
│   ├── dependencias.py
│   └── main.py
├── alembic/
├── scripts/
│   └── probar_etl.py
├── seed.py
├── requerimientos.txt
├── Procfile                               ← web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
├── runtime.txt                            ← python-3.12.0
├── docker-compose.yml
├── alembic.ini
└── .env                                   ← URL_BASE_DE_DATOS=postgresql://seg:seg123@localhost:5432/rodamientos
```

---

## 6. Quirks del ETL (para no repetir debugging)

- Headers de Excel tienen `\n` embebidos → helper `_normalizar` colapsa saltos.
- `Estado_Rodamientos` tiene fila vacía antes de headers → `_encontrar_header` detecta dinámicamente.
- **Fechas en Excel de CG:** `Nuevo_Control_De_Rodamientos` trae fechas como strings `'DD/MM/YYYY'`.
  `_a_fecha()` en `parser_rodamientos.py` ahora maneja ambos formatos: ISO (`YYYY-MM-DD`) y `DD/MM/YYYY`.
  Sin este fix, PSP-06 mostraba la fecha del seed (incorrecta) en vez de la del control mensual.
- Campo `Plant` del logbook: CG tiene código al final (`E921084-CG10` → `WEC10`);
  Peralta al principio (`PSP-48 E920311` → `PSP-48`).
- Excel de Peralta trae tipos con tilde; el clasificador usa sin tilde → normalización en el parser.
- Seed de Peralta llega hasta Mar'26 → primer logbook mensual de PSP debe ser Abr'26 en adelante.
- Seed PSP `warnings_por_tipo` tiene `mes=null, anio=null` (no hay granularidad mensual por tipo en el histórico).
  Esto es esperado. El gráfico stacked lo muestra como "Sin desglose" hasta que se carguen logbooks.

---

## 7. Comandos útiles (PowerShell, Windows)

```powershell
# Ruta del proyecto
cd C:\Users\Joaquín\Documents\SEG\rodamientos-dashboard

# Levantar Postgres
docker compose up -d

# Correr la API
uvicorn app.main:app --reload

# Migraciones
alembic revision --autogenerate -m "mensaje"
alembic upgrade head

# Seed inicial (parques y turbinas)
python seed.py

# Probar el ETL completo
python scripts/probar_etl.py

# Ver tablas en DB
docker exec -it rodamientos-dashboard-postgres-1 psql -U seg -d rodamientos -c "\dt"

# Limpiar datos (mantiene parques y turbinas)
docker exec -it rodamientos-dashboard-postgres-1 psql -U seg -d rodamientos -c "TRUNCATE inspecciones_rodamientos, warnings_por_mes, warnings_por_tipo, cargas RESTART IDENTITY CASCADE;"
```

Notas de entorno:
- Python 3.12, sin venv (instalación global).
- Contenedor Docker: `rodamientos-dashboard-postgres-1`.
- DB local: usuario `seg`, password `seg123`, base `rodamientos`, puerto 5432.
- `.env` tiene `URL_BASE_DE_DATOS=postgresql://seg:seg123@localhost:5432/rodamientos`.
- Repo GitHub: `https://github.com/JoaquinKarawacki/rodamientos-dashboard`.

---

## 8. Stack tecnológico

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 + Alembic, openpyxl
- **DB:** PostgreSQL 16 (Docker local / Railway producción)
- **Frontend:** HTML/CSS/JS vanilla + Plotly.js (dashboard interno, dark theme)
- **Export:** HTML standalone con SVG charts embebidos (sin dependencias externas)
- **Deploy:** Railway (Etapa 6 — pendiente)

---

## 9. PRÓXIMO PASO: Etapa 6 — Deploy Railway

El código está listo y pusheado a GitHub. `Procfile` y `runtime.txt` creados.

Pasos pendientes:
1. Crear proyecto en Railway y conectar el repo de GitHub.
2. Agregar un servicio PostgreSQL en Railway.
3. Configurar la variable de entorno `URL_BASE_DE_DATOS` con la URL interna de Railway
   (Railway provee `DATABASE_URL` automáticamente; hay que renombrarlo o adaptarlo).
4. Correr `alembic upgrade head` y `python seed.py` contra la DB de Railway
   (usar `DATABASE_PUBLIC_URL` desde afuera de Railway).
5. Verificar que la API levante y responda en la URL pública de Railway.
6. Actualizar `const API` en `dashboard.html` para apuntar a la URL de Railway en vez de `localhost:8000`.

**Nota importante sobre Railway:**
- `DATABASE_URL` usa sintaxis de referencia interna de Railway.
- El seed debe correr contra `DATABASE_PUBLIC_URL` desde fuera de Railway.
- Antecedente del proyecto de licencias: el deploy falló con `secret FRONTEND_URL not found`
  porque Railway no resuelve variables en build time igual que en runtime.
  Verificar que todas las variables estén seteadas antes del primer deploy.
