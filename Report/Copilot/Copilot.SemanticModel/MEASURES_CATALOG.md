# 📊 Catálogo de Medidas DAX

**Ubicación:** `Copilot.SemanticModel/definition/tables/Measure.tmdl` y `Measure_Advanced.tmdl`

---

## 🔍 Índice Rápido

| Categoría | Medidas | Tabla |
|-----------|---------|-------|
| **Monetarias Básicas** | Gross Amount, Net Amount, Discount, Savings | Measure |
| **Volumen** | Total Requests, Exceeded Requests, MTD/YTD | Measure |
| **Costo Unitario** | Avg Cost/Request, Theoretical, Ratio | Measure |
| **Temporal** | Prior Month, MoM Growth, YTD, Avg Daily | Measure_Advanced |
| **Optimización** | Efficiency Score, Quota Headroom, Budget | Measure_Advanced |
| **Alertas** | Over Quota, Cost Spike | Measure_Advanced |

---

## 📈 Medidas Base (Tabla: Measure)

### Ingresos y Costos

#### **[Gross Amount Total]**
```
Fórmula: SUM(Billing[gross_amount])
Significado: Costo teórico total (sin descuentos aplicados)
Caso de uso: Baseline para calcular ahorros
Formato: Moneda ($)
```

#### **[Net Amount Total]**
```
Fórmula: SUM(Billing[net_amount])
Significado: Costo real pagado (con plan de descuento aplicado)
Caso de uso: Presupuestaria, comparativas de período
Formato: Moneda (€)
```

#### **[Discount Amount]**
```
Fórmula: SUM(Billing[discount_amount])
Significado: Total ahorrado por plan/contrato
Caso de uso: Evaluar ROI del plan actual
Formato: Moneda ($)
Relación: Discount Amount = Gross - Net
```

#### **[Savings %]**
```
Fórmula: DIVIDE([Discount Amount], [Gross Amount Total], 0)
Significado: % del costo que se ahorra vs baseline
Caso de uso: KPI de valor del plan
Formato: Porcentaje
Rango típico: 10-40% (bien = > 20%)
```

### Volumen de Consumo

#### **[Total Requests]**
```
Fórmula: SUM(Billing[quantity])
Significado: Número total de requests/consumos en el período
Caso de uso: Métricas de adopción, comparativas
Formato: Número entero
Nota: quantity = # de requests (dependiendo del SKU)
```

#### **[MTD Requests]** (Month-To-Date)
```
Fórmula: TOTALMTD([Total Requests], Dim_Date[Date])
Significado: Requests acumulados desde inicio de mes actual
Caso de uso: Progress vs cuota mensual
Formato: Número entero
Nota: Se recalcula diariamente
```

#### **[Exceeded Requests]**
```
Fórmula: CALCULATE(SUM(Billing[quantity]), Billing[exceeds_quota] = TRUE)
Significado: # de requests que superan la cuota mensual
Caso de uso: Flag de overspend, alertas
Formato: Número entero
Crítico: Si > 0, se está excediendo
```

#### **[Avg Daily Requests]**
```
Fórmula: AVERAGEX(VALUES(Dim_Date[Date]), [Total Requests])
Significado: Consumo promedio diario en período seleccionado
Caso de uso: Trend smoothing, baseline
Formato: Número decimal (2 decimales)
```

### Costo Unitario (Indicadores de Eficiencia)

#### **[Avg Cost per Request]**
```
Fórmula: DIVIDE([Net Amount Total], [Total Requests], 0)
Significado: Costo real promedio por cada request
Caso de uso: Comparar eficiencia entre modelos/usuarios
Formato: Moneda €
Insight: Menor = mejor negocio / plan más eficiente
```

#### **[Theoretical Cost per Request]**
```
Fórmula: DIVIDE([Gross Amount Total], [Total Requests], 0)
Significado: ¿Cuánto costaría SIN descuento?
Caso de uso: Baseline para calculateCost Ratio
Formato: Moneda €
Nota: Usado en [Cost per Request Ratio]
```

#### **[Quota Usage %]**
```
Fórmula: DIVIDE([Total Requests], MAX(Billing[total_monthly_quota]), 0)
Significado: % de cuota mensual consumida
Caso de uso: Progress bar, alertas de límite
Formato: Porcentaje
Rango: 0-100%+ (>100% = over quota)
Crítico: > 80% = Amarillo; > 100% = Rojo
```

### Informativas

#### **[Reporting Period]**
```
Fórmula: MIN(Dim_Date[Date]) & " - " & MAX(Dim_Date[Date])
Significado: Rango de fechas del reporte
Caso de uso: Label en cards/headers
Formato: Texto
Ejemplo: "2024-01-01 - 2024-01-31"
```

#### **[Last Refresh Date]**
```
Fórmula: NOW()
Significado: Última hora de actualización de datos
Caso de uso: Mostrar actualidad de datos
Formato: DateTime
Nota: Se recalcula en cada refresh
```

---

## 📊 Medidas Avanzadas (Tabla: Measure_Advanced)

### Análisis Temporal Comparativo

#### **[Prior Month Cost]**
```
Fórmula: CALCULATE([Net Amount Total], DATEADD(Dim_Date[Date], -1, MONTH))
Significado: Costo del mes anterior para benchmarking
Caso de uso: Calcular MoM growth, trending
Formato: Moneda €
Nota: Útil en gráficos de evolución
```

#### **[Prior Month Requests]**
```
Fórmula: CALCULATE([Total Requests], DATEADD(Dim_Date[Date], -1, MONTH))
Significado: Requests del mes anterior
Caso de uso: Comparativa de adopción
Formato: Número entero
```

#### **[Cost MoM Growth %]** ⭐ IMPORTANTE
```
Fórmula: DIVIDE([Net Amount Total] - [Prior Month Cost], [Prior Month Cost], BLANK())
Significado: % mensual de incremento/decremento en costo
Caso de uso: Visualizar tendencia de gasto
Formato: Porcentaje
Interpretación:
  -10% = Disminuyó 10% (BIEN ✅)
  +20% = Aumentó 20% (ALERTA ⚠️)
```

#### **[Requests MoM Growth %]**
```
Fórmula: DIVIDE([Total Requests] - [Prior Month Requests], [Prior Month Requests], BLANK())
Significado: % cambio en adopción/consumo mes a mes
Caso de uso: Track de adoption velocity
Formato: Porcentaje
```

#### **[YTD Net Cost]** (Year-To-Date)
```
Fórmula: TOTALYTD([Net Amount Total], Dim_Date[Date])
Significado: Costo acumulado desde Jan 1 del año actual
Caso de uso: Tracking presupuestario anual
Formato: Moneda €
Nota: Se recalcula a medida que avanza el año
```

#### **[YTD Requests]**
```
Fórmula: TOTALYTD([Total Requests], Dim_Date[Date])
Significado: Requests acumulados desde inicio de año
Caso de uso: Target vs actual annual
Formato: Número entero
```

#### **[Avg Daily Cost]**
```
Fórmula: AVERAGEX(VALUES(Dim_Date[Date]), [Net Amount Total])
Significado: Gasto promedio diario en período
Caso de uso: Budget burn rate, trending
Formato: Moneda €
Uso: Proyectar gasto mensual
```

### Optimización y Eficiencia

#### **[Cost per Request Ratio]** ⭐ INDICADOR CLAVE
```
Fórmula: DIVIDE([Avg Cost per Request], [Theoretical Cost per Request], BLANK())
Significado: Ratio de costo actual vs teórico (descuento relativo)
Caso de uso: Evaluar efectividad del plan
Formato: Porcentaje (ej: 65% = 35% descuento)
Interpretación:
  50% = Pagando mitad del precio (EXCELENTE)
  75% = 25% descuento (BUENO)
  100% = Sin descuento (REVISAR)
  >100% = Premium pricing (REVISAR)
```

#### **[Total Savings]**
```
Fórmula: [Gross Amount Total] - [Net Amount Total]
Significado: Monto total ahorrado en el período
Caso de uso: KPI de valor financiero
Formato: Moneda €
Ejemplo: €50,000 ahorrados vs baseline
```

#### **[Avg Savings per Request]**
```
Fórmula: DIVIDE([Total Savings], [Total Requests], 0)
Significado: Ahorro promedio por cada request
Caso de uso: Comparar eficiencia de planes
Formato: Moneda €
```

#### **[Quota Headroom %]** (Espacio disponible)
```
Fórmula: 1 - [Quota Usage %]
Significado: % de cuota DISPONIBLE (no consumida)
Caso de uso: Visualizar capacidad restante
Formato: Porcentaje
Interpretación:
  50% = 50% de cuota disponible (BUENO)
  5% = Solo 5% restante (ALERTA)
  -20% = Ya 20% sobre límite (CRÍTICO)
```

#### **[Model Efficiency Score]** 🔬 EXPERIMENTAL
```
Fórmula: VAR AvgCostAllModels = CALCULATE([Avg Cost/Request], ALL(model))
         VAR ThisModelCost = [Avg Cost per Request]
         VAR Efficiency = DIVIDE(AvgCostAllModels, ThisModelCost) * 100
         RETURN MIN(Efficiency, 100)
Significado: Score 0-100 de eficiencia relativa del modelo
Caso de uso: Comparar modelos (GPT-4 vs GPT-3.5)
Formato: Número 0-100
Interpretación:
  100 = Modelo más eficiente
  75 = 25% más caro que el mejor
  50 = 2x más caro que el mejor
```

#### **[Budget Variance]**
```
Fórmula: BLANK() (Placeholder)
Significado: Desviación presupuestaria
Estado: Requiere tabla Budget externa
Caso de uso: Cumplimiento presupuestario
```

### Alertas y Banderas

#### **[Over Quota Alert]** 🚨
```
Fórmula: IF([Quota Usage %] > 1, 1, 0)
Significado: Flag 1/0 si se excedió cuota
Caso de uso: Condicionales de formato/color
Formato: 0 o 1
Uso en visuals: Colored backgrounds, icon alerts
```

#### **[Cost Spike Flag]** ⚠️
```
Fórmula: IF([Cost MoM Growth %] > 0.2, 1, 0)
Significado: Flag si costo creció > 20% vs mes anterior
Caso de uso: Detección de anomalías
Formato: 0 o 1
Umbral: 20% reconfigurable
```

#### **[Cost by Product Rank]**
```
Fórmula: RANK([Net Amount Total], ALL(Billing[product]), DESC)
Significado: Ranking del producto en costo (1 = más caro)
Caso de uso: Top N visualization
Formato: Número entero
Uso: Filtrar TOP 5, TOP 10 productos
```

---

## 🎯 Guía de Uso por Escenario

### **Ejecutivo - KPI Dashboard**
Mostrar:
1. [Net Amount Total] - "Gasto real"
2. [Savings %] - "Valor del plan"
3. [Quota Usage %] - "% de cuota"
4. [Cost MoM Growth %] - "Tendencia"

### **Manager - Cost Control**
Mostrar:
1. [Net Amount Total] (vs [Prior Month Cost])
2. [Over Quota Alert] + [Exceeded Requests]
3. [Avg Cost per Request] por User/Product
4. [YTD Net Cost] vs Budget

### **Analyst - Detailed Investigation**
Mostrar:
1. All [Cost] measures + ratios
2. [Model Efficiency Score] por modelo
3. [Total Requests] + [MTD Requests]
4. Trend chart: [Avg Daily Cost]

### **Finance - Planning**
Mostrar:
1. [Gross Amount Total] (baseline)
2. [Net Amount Total] (actual)
3. [Discount Amount] + [Savings %]
4. YTD measures para forecasting

---

## ⚡ Tips de Performance

- Medir medidas es "caro" en Power BI: usar solo las necesarias
- [Cost MoM Growth %] puede ser BLANK si no hay datos previos
- Use BLANK() en lugar de 0 para comparatividad
- Dimensiones grandes (Billing): considerar agregaciones

---

## 🔄 Control de Cambios

| Versión | Medidas Agregadas | Notas |
|---------|------------------|-------|
| 1.0 | 12 medidas base | Financiero y volumen |
| 2.0 | +15 medidas advanced | Comparativas temporal, optimización, alertas |

---

**Última revisión:** Abril 2026  
**Autor:** Dashboard team  
**Estado:** ✅ Completado y documentado
