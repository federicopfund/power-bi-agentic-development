# 📊 Dashboard de Facturación de GitHub Copilot

**Versión:** 2.0  
**Estado:** Normalizado y optimizado  
**Última actualización:** Abril 2026

---

## 🎯 Visión del Proyecto

Este es un **Dashboard Integral de Facturación y Control de Costos** diseñado para que ejecutivos, managers y equipos de operaciones monitoren, analicen y optimicen el gasto en **GitHub Copilot** en sus organizaciones.

### 📌 Usuarios Objetivo
- **CFO / Finanzas**: Visión consolidada de costos, presupuestaria y ahorro
- **Cost Center Managers**: Control granular por departamento y equipo
- **Product Managers**: Análisis de adopción y eficiencia de modelos IA
- **IT / Operations**: Cumplimiento de cuotas, alertas, governance

---

## 📐 Estructura del Modelo Semántico

### **Tablas de Hechos (Fact Tables)**

#### **Billing**
Registro detallado de cada transacción de consumo
```
Campos: date, username, product, sku, model, quantity, 
         gross_amount, net_amount, discount_amount, total_monthly_quota, exceeds_quota
Granularidad: Por usuario/día/modelo
```

#### **Usage** 
Agregación de consumo por dimensión
```
Campos: date, product, sku, quantity, gross_amount, net_amount, 
         repository, cost_center_name
Granularidad: Por fecha/producto/repositorio
```

### **Tablas de Dimensión (Dimension Tables)**

#### **Dim_Date**
Dimensión temporal estándar
```
Campos: Date, Year, MonthName, MonthNumber, Quarter, YearMonth
Uso: Filtros de fecha, análisis temporal
```

#### **Dim_User** *(Normalizado)*
Usuarios únicos que consumen Copilot
```
Campos: username (PK), User Key, Primary Key
Source: Derivada de Billing
```

#### **Dim_Product** *(Normalizado)*
Productos y modelos disponibles
```
Campos: product (PK), sku, model, Product Key, Primary Key
Source: Derivada de Billing
```

#### **Dim_Model** *(Normalizado)*
Clasificación de modelos IA
```
Campos: model (PK), Model Category (GPT-4/GPT-3.5/Other), 
         Model Tier (Premium/Standard/Basic), Model Key, Primary Key
Source: Derivada de Billing con lógica de categorización
```

---

## 📊 Medidas DAX (Catálogo Completo)

### **Core Measures** (Tabla: Measure)

#### Ingresos y Costos
```
[Gross Amount Total]       → SUM(Billing[gross_amount])
[Net Amount Total]         → SUM(Billing[net_amount])
[Discount Amount]          → SUM(Billing[discount_amount])
[Total Savings]            → [Gross Amount Total] - [Net Amount Total]
```

#### Volumen
```
[Total Requests]           → SUM(Billing[quantity])
[Exceeded Requests]        → CALCULATE(SUM(...), exceeds_quota = TRUE)
[MTD Requests]             → TOTALMTD([Total Requests], Dim_Date[Date])
[Avg Daily Requests]       → AVERAGEX(VALUES(Dim_Date[Date]), [Total Requests])
```

#### Eficiencia
```
[Avg Cost per Request]           → [Net Amount Total] / [Total Requests]
[Theoretical Cost per Request]   → [Gross Amount Total] / [Total Requests]
[Cost per Request Ratio]         → [Avg Cost] / [Theoretical Cost]
[Quota Usage %]                  → [Total Requests] / MAX(total_monthly_quota)
[Quota Headroom %]               → 1 - [Quota Usage %]
[Model Efficiency Score]         → Score 0-100 sobre eficiencia relativa
```

#### Informativas
```
[Reporting Period]   → MIN(Date) & " - " & MAX(Date)
[Last Refresh Date]  → NOW()
```

### **Advanced Measures** (Tabla: Measure_Advanced)

#### Análisis Temporal Comparativo
```
[Prior Month Cost]            → CALCULATE([Net Amount Total], DATEADD(Dim_Date, -1, MONTH))
[Prior Month Requests]        → CALCULATE([Total Requests], DATEADD(Dim_Date, -1, MONTH))
[Cost MoM Growth %]           → ([Net Amount Total] - [Prior Month Cost]) / [Prior Month Cost]
[Requests MoM Growth %]       → ([Total Requests] - [Prior Month Requests]) / [Prior Month Requests]
[YTD Net Cost]               → TOTALYTD([Net Amount Total], Dim_Date[Date])
[YTD Requests]               → TOTALYTD([Total Requests], Dim_Date[Date])
[Avg Daily Cost]             → AVERAGEX(VALUES(Dim_Date[Date]), [Net Amount Total])
[Avg Savings per Request]    → [Total Savings] / [Total Requests]
```

#### Análisis de Alertas
```
[Over Quota Alert]           → IF([Quota Usage %] > 1, 1, 0)
[Cost Spike Flag]            → IF([Cost MoM Growth %] > 0.2, 1, 0)
[Cost by Product Rank]       → RANK([Net Amount Total], ALL(product), DESC)
```

---

## 📄 Páginas del Reporte (7 Total)

### 1️⃣ **Portada**
- Intro visual
- KPI summary de alto nivel
- Última actualización

### 2️⃣ **Executive Overview** ⭐ (Recién normalizada)
- 5 Cards KPI: Gross, Net, Savings, Quota %, Avg Cost
- 4 Slicers: Date, Organization, CostCenter, Product
- 2 Analíticos: LineChart (tendencia), DonutChart (distribución)
- **Layout:** Grid-based con spacing consistente 16px
- **Status:** ✅ Diseño profesional completado

### 3️⃣ **Usage Analysis**
- Análisis de consumo por dimensión
- Tablas detalladas: by Product, Model, Username
- Filtros interactivos vía slicers
- Gráficos de tendencia

### 4️⃣ **Premium Requests & Cuota - Governance** ⭐ (Más completa)
- Foco: Control de límites
- Alertas: Requests que exceden cuota
- Filtros: Organización, centro de costo
- Análisis: Distribución de excesos

### 5️⃣ **Cost Optimization** 🆕
- Top usuarios por costo/request
- Presupuesto vs actual (comparativo)
- Oportunidades de ahorro identificadas
- Recomendaciones de optimización
- Forecast de próximos 3 meses

### 6️⃣ **Models Performance** 🆕
- Comparativa: GPT-4 vs GPT-3.5 vs Otros
- Efficiency Score por modelo
- Adoption trends por modelo
- Cost/request y ROI por modelo
- Recomendación de modelo óptimo

### 7️⃣ **Trend Analysis** 🆕
- Línea de tendencia detallada (12 meses anteriores)
- YoY growth % y análisis
- Forecast ML simple (próximos 3 meses)
- Seasonality analysis
- Change point detection

---

## 🎨 Tema Profesional

**Archivo:** `Copilot.Report/definition/theme.json`

### Paleta de Colores
- **Primario:** Azul corporativo (#0078D4)
- **Éxito:** Verde (#107C10)
- **Alerta:** Ámbar (#FFB900)
- **Crítico:** Rojo (#D83B01)
- **Secundarios:** 8 colores adicionales para variedad

### Estilos Aplicados
- **Fuente:** Segoe UI Sans-Serif (estándar Microsoft)
- **Títulos:** 24pt Bold, color #1F497D
- **Leyendas:** 12pt regular
- **Tablas:** Borders sutiles (#D0CECE), fondo blanco
- **Cards:** Outline ligero, fondo blanco limpio
- **Gráficos:** Colores temáticos con buena legibilidad

---

## 🔗 Relaciones del Modelo

```
Billing ──── (FK) Dim_Date[Date]
   │
   ├──── (FK) Dim_User[username]
   │
   ├──── (FK) Dim_Product[product, sku]
   │
   └──── (FK) Dim_Model[model]

Usage ──── (FK) Dim_Date[Date]
   │
   └──── (FK) Dim_Product[product]

Measure ──────────── (No filtrable directamente)
Measure_Advanced ──── (No filtrable directamente)
```

---

## ✅ Mejoras Implementadas (v2.0)

| # | Mejora | Estado | Descripción |
|----|--------|--------|-------------|
| 1 | Normalización del esquema | ✅ | Tablas Dim creadas (User, Product, Model) |
| 2 | Medidas avanzadas | ✅ | 15 nuevas medidas para análisis comparativos |
| 3 | Nuevas páginas | ✅ | Cost Optimization, Models Performance, Trend Analysis |
| 4 | Tema profesional | ✅ | Paleta corporativa + estilos aplicados |
| 5 | Documentación | ✅ | README y guías de uso completadas |
| 6 | Grid layout | ✅ | Executive Overview: spacing 16px, márgenes 24px |
| 7 | Validación model | 🔄 | Requiere vista previa en Power BI/Fabric |

---

## 🚀 Próximos Pasos

### **Inmediatos**
1. Validar en Power BI Desktop o Fabric
2. Ajustar relaciones de modelo si es necesario
3. Verificar fórmulas DAX en contextos filtrados
4. Poblar visuals en nuevas páginas (5, 6, 7)

### **Corto Plazo**
1. Agregar bookmarks de navegación
2. Implementar drill-through entre páginas
3. Agregar tooltips personalizados
4. Crear favoritos para usuarios clave

### **Mediano Plazo**
1. Integrar datos presupuestarios (Budget vs Actual)
2. Análisis predictivo (ML para forecast)
3. Alertas automáticas (Power Automate)
4. Publicar en Power BI Service

---

## 📋 Notas Técnicas

### Decisiones de Diseño
- **Source:** Modelo semántico de 1290x900px (16:9)
- **Lenguaje:** DAX (Power BI) + M (Power Query)
- **Versionado:** TMDL + PBIR (Fabric format)
- **Paleta:** Material Design + Corporate Blue

### Cuidados Importantes
⚠️ Relaciones de modelo:
- Asegurar que Dim_User/Product/Model uses correctos

⚠️ Contexto de filtros:
- Medidas usan CALCULATE para contextos específicos
- Verificar ALL() clauses cuando se agrega

⚠️ Rendimiento:
- Limitar a 10,000 filas por página si es posible
- Usar aggregations si hay volumen alto

---

## 📞 Soporte y Contacto

Para preguntas o mejoras:
- Revisar skill de `semantic-models` en plugin
- Consultar documentación DAX en Microsoft Docs
- Usar agents de validación del plugin para diagnosticar

---

**© 2026 | Dashboard de Facturación Copilot v2.0**
