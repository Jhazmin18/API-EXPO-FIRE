# Formularios Dinámicos - Mejoras Backend

Hola equipo,

El frontend ya está listo para trabajar con formularios dinámicos. El flujo funciona así:

1. Usuario hace clic en "Agregar extintor"
2. Ve 3 opciones: Levantamiento, ANGRI, Venta
3. Selecciona una → se carga el formulario dinámico del backend
4. Llena el formulario → se crea el extintor + se guarda el FormRun

---

## Lo que ya funciona

El frontend puede usar estos endpoints que ya existen:

```
GET  /api/forms/templates/{codigo}/activo/   ✅
POST /api/forms/runs/                        ✅
POST /api/extintores/                        ✅
PATCH /api/forms/runs/{id}/                  ✅
```

**Pero hay algunas limitaciones:**

---

## Mejoras necesarias (no urgentes)

### 1. Endpoint que filtre plantillas por rol

**Problema:** `GET /api/forms/templates/` retorna todas las plantillas sin filtrar.

**Lo que necesitamos:**
```
GET /api/forms/templates/?disponibles=true
```

Este endpoint debe retornar SOLO las plantillas que el usuario puede usar según su rol:
- **SUPERADMIN** → LEVANTAMIENTO, ANGRI, VENTA, UIPC
- **ANALISTA** → SOLO UIPC
- **EMPRESA/SUPERVISOR** → Ninguna (array vacío)

**Por ahora:** El frontend filtra manualmente, pero no es lo ideal.

---

### 2. Validación de permisos en creación

**Problema:** `POST /api/forms/runs/` no valida si el usuario tiene permisos para esa plantilla.

**Lo que necesitamos:**
- Si un ANALISTA intenta crear un formulario de VENTA → retornar `403 Forbidden`
- Si un EMPRESA intenta crear cualquier formulario → retornar `403 Forbidden`

**Ejemplo de error:**
```json
{
  "detail": "No tienes permisos para llenar este formulario"
}
```

**Por ahora:** Solo el frontend valida, pero técnicamente alguien podría hacer POST directo.

---

### 3. Endpoint unificado: crear extintor desde FormRun

**Problema:** El frontend debe hacer 3 llamadas:
1. `POST /forms/runs/` (con scope_id temporal)
2. `POST /extintores/` (extrae datos del FormRun)
3. `PATCH /forms/runs/{id}/` (actualiza scope_id con el ID del extintor)

Si falla alguna, puede quedar inconsistente.

**Lo que sería ideal:**
```
POST /api/forms/runs/crear-con-extintor/
```

Body:
```json
{
  "template": 1,
  "empresa": 5,
  "tipo_servicio": "levantamiento",
  "respuestas_json": { ... }
}
```

Response:
```json
{
  "extintor_id": 123,
  "form_run_id": 456,
  "mensaje": "Extintor creado exitosamente"
}
```

Este endpoint haría todo en una transacción:
- Crear FormRun
- Extraer datos del `respuestas_json` y crear Extintor
- Vincular ambos con `scope_id`
- Si algo falla, hacer rollback

**Por ahora:** El frontend hace las 3 llamadas manualmente.

---

### 4. Estándar de claves para mapeo automático

**Problema:** Las plantillas deben tener preguntas con claves específicas que coincidan con campos de Extintor.

**Lo que necesitamos documentar:**

Cuando creen plantillas en Django Admin, usen estas claves para que el frontend/backend pueda mapear automáticamente:

| Clave | Campo Extintor | Tipo |
|-------|----------------|------|
| `codigo_extintor` | `codigo` | texto |
| `tipo_extintor` | `tipo` | seleccion |
| `capacidad` | `capacidad` | numero |
| `ubicacion` | `ubicacion` | texto |
| `fecha_fabricacion` | `fecha_fabricacion` | fecha |
| `fecha_recarga` | `fecha_ultima_recarga` | fecha |
| `estado_actual` | `estado` | seleccion |

**Por ahora:** El frontend tiene el mapeo hardcodeado en `ExtintorFormRender.jsx` (líneas 461-469).

---

## Testing

Para que el frontend funcione, necesitan:

1. Crear al menos una plantilla activa en Django Admin para cada tipo:
   - Código: `LEVANTAMIENTO`
   - Código: `ANGRI`
   - Código: `VENTA`

2. Cada plantilla debe tener preguntas con las claves estándar mencionadas arriba

3. Usuario con rol `ADMINISTRADOR` en el sistema (para probar)

---

## Estado actual

✅ **El frontend YA funciona** con el backend actual (con las limitaciones mencionadas)
⏳ Las mejoras son para hacerlo más robusto y seguro

Cualquier duda, nos avisan. Gracias!
