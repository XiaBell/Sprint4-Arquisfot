# Plan de Experimentos - Sprint 4

## Experimento 1: Latencia (CQRS)

### Objetivo
Demostrar que el uso de CQRS con MongoDB reduce significativamente la latencia de consultas de inventario comparado con consultas SQL complejas.

### Escenarios

#### Escenario A: Línea Base (PostgreSQL)
- **Endpoint**: `GET /api/v1/inventory/sql-list`
- **Base de Datos**: PostgreSQL
- **Consulta**: JOIN complejo con múltiples tablas
- **Datos**: 100,000 productos

#### Escenario B: CQRS Optimizado (MongoDB)
- **Endpoint**: `GET /api/v1/inventory/nosql-list`
- **Base de Datos**: MongoDB
- **Consulta**: Find simple en documentos desnormalizados
- **Datos**: 100,000 documentos sincronizados

### Métricas a Medir

1. **Latencia promedio** (ms)
2. **Latencia p95** (ms)
3. **Latencia p99** (ms)
4. **Tasa de error** (%)
5. **Throughput** (requests/segundo)

### Configuración de Prueba

- **Herramienta**: JMeter o Apache Bench
- **Usuarios concurrentes**: 100
- **Duración**: 5 minutos
- **Ramp-up**: 30 segundos

### Script JMeter

```xml
<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2">
  <hashTree>
    <TestPlan>
      <stringProp name="TestPlan.comments">Prueba de Latencia - CQRS</stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
        <intProp name="ThreadGroup.num_threads">100</intProp>
        <intProp name="ThreadGroup.ramp_time">30</intProp>
        <longProp name="ThreadGroup.start_time">0</longProp>
        <longProp name="ThreadGroup.end_time">300</longProp>
      </ThreadGroup>
      <hashTree>
        <HTTPSamplerProxy>
          <stringProp name="HTTPSampler.domain">INVENTORY_SERVICE_IP</stringProp>
          <stringProp name="HTTPSampler.path">/api/v1/inventory/sql-list</stringProp>
          <stringProp name="HTTPSampler.method">GET</stringProp>
          <intProp name="HTTPSampler.port">8000</intProp>
        </HTTPSamplerProxy>
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
```

### Resultados Esperados

- **PostgreSQL**: Latencia promedio > 2 segundos
- **MongoDB**: Latencia promedio < 2 segundos (ASR cumplido)

### Análisis

Comparar los resultados y demostrar que MongoDB (CQRS) cumple con el ASR de latencia (< 2s) mientras que PostgreSQL no.

---

## Experimento 2: Seguridad (RBAC)

### Objetivo
Demostrar que el sistema de RBAC previene el 100% de los intentos no autorizados de modificación/eliminación de ítems de pedidos.

### Escenarios

#### Escenario A: Prueba de Integridad (OPERARIO)
- **Endpoint**: `PUT /api/v1/orders/{id}/items/{item_id}`
- **Token**: JWT con rol `OPERARIO`
- **Acción**: Intentar marcar ítem como no disponible
- **Resultado Esperado**: `403 Forbidden` en el 100% de los casos

#### Escenario B: Trade-off Base (Sin Validación)
- **Endpoint**: `PUT /api/v1/orders/{id}/items/{item_id}`
- **Token**: JWT con rol `GESTOR`
- **Acción**: Marcar ítem como no disponible
- **Nota**: Medir tiempo sin validación JWT (hipotético)

#### Escenario C: Trade-off Seguro (Con Validación)
- **Endpoint**: `PUT /api/v1/orders/{id}/items/{item_id}`
- **Token**: JWT con rol `GESTOR`
- **Acción**: Marcar ítem como no disponible
- **Medición**: Tiempo total incluyendo validación JWT

### Métricas a Medir

1. **Tasa de rechazo** para OPERARIO (%)
2. **Tasa de éxito** para GESTOR (%)
3. **Latencia promedio** con validación (ms)
4. **Tiempo de validación JWT** (ms)
5. **Overhead de seguridad** (diferencia entre B y C)

### Configuración de Prueba

- **Herramienta**: JMeter o script personalizado
- **Iteraciones**: 1000 requests
- **Tokens**: 
  - 500 requests con token OPERARIO
  - 500 requests con token GESTOR

### Resultados Esperados

- **OPERARIO**: 100% de respuestas `403 Forbidden`
- **GESTOR**: 100% de respuestas `200 OK` o `204 No Content`
- **Overhead de seguridad**: < 10% de la latencia base

### Análisis del Trade-off

Si el overhead de seguridad es:
- **< 10%**: Trade-off positivo, seguridad eficiente
- **10-20%**: Trade-off aceptable
- **> 20%**: Trade-off negativo, considerar optimizaciones

---

## Ejecución de Experimentos

### Pre-requisitos

1. Servicios desplegados y funcionando
2. Base de datos poblada con 100,000 productos
3. MongoDB sincronizado
4. Usuarios de prueba en Auth0 con roles asignados

### Comandos de Ejecución

#### Experimento 1: Latencia

```bash
# Prueba PostgreSQL
ab -n 10000 -c 100 http://INVENTORY_SERVICE_IP:8000/api/v1/inventory/sql-list

# Prueba MongoDB
ab -n 10000 -c 100 http://INVENTORY_SERVICE_IP:8000/api/v1/inventory/nosql-list
```

#### Experimento 2: Seguridad

```bash
# Script personalizado con tokens JWT
python scripts/test_security.py \
  --orders-url http://ORDERS_SERVICE_IP:8001 \
  --token-operario TOKEN_OPERARIO \
  --token-gestor TOKEN_GESTOR \
  --iterations 1000
```

### Recopilación de Resultados

1. Exportar métricas de JMeter/AB
2. Analizar logs de los servicios
3. Comparar resultados
4. Generar reporte con gráficos

---

## Reporte de Resultados

El reporte debe incluir:

1. **Resumen Ejecutivo**
2. **Metodología**
3. **Resultados por Experimento**
4. **Análisis y Conclusiones**
5. **Gráficos y Tablas**
6. **Recomendaciones**

### Plantilla de Resultados

| Métrica | PostgreSQL | MongoDB (CQRS) | Mejora |
|---------|------------|---------------|--------|
| Latencia Promedio (ms) | X | Y | Z% |
| Latencia P95 (ms) | X | Y | Z% |
| Latencia P99 (ms) | X | Y | Z% |
| Throughput (req/s) | X | Y | Z% |

| Escenario | Tasa de Éxito | Tasa de Rechazo | Latencia (ms) |
|-----------|---------------|-----------------|---------------|
| OPERARIO (PUT) | 0% | 100% | X |
| GESTOR (PUT) | 100% | 0% | Y |
| Overhead Seguridad | - | - | Z% |

