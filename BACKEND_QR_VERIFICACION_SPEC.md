# QR - Botón de Verificación

## Lo que necesitamos

**Endpoint:** `POST /extintores/{id}/verificar/`

**Quién puede usarlo:** Solo Analistas y Admins (con token JWT)

**Body del request:**
```json
{
  "observaciones": "Extintor en buen estado" // opcional
}
```

**Response esperado:**
```json
{
  "message": "Verificación registrada exitosamente",
  "verificacion_id": 123,
  "fecha": "2026-01-20T15:30:00Z"
}
```

Si no tiene permisos, que retorne un 403 con mensaje de error.

---

## Para qué sirve

Según el PDF del cliente, los Analistas en campo escanean el QR del extintor y marcan un "check" de que lo verificaron. Necesitamos guardar:

- Qué extintor verificaron
- Quién lo verificó (usuario)
- Cuándo (fecha/hora)
- Observaciones opcionales (si el analista quiere agregar algo)

---

## Tabla sugerida

¿Pueden crear una tabla de verificaciones? Algo como:

```python
class VerificacionExtintor:
    extintor = ForeignKey(Extintor)
    verificado_por = ForeignKey(User)
    fecha_verificacion = DateTimeField(auto_now_add=True)
    observaciones = TextField(blank=True)
```

---

## Estado del frontend

El frontend ya está listo:
- Página `/qr/EXT-001` funciona
- Muestra toda la info del extintor
- Botón "Verificar" detecta si el usuario está logueado y si tiene permisos
- Solo falta conectarlo al endpoint (ahorita muestra un alert temporal)

Archivo: `frontend/src/pages/QRPublico.jsx`

---

## Testing rápido

```bash
# Como Analista (debería funcionar)
curl -X POST http://localhost:8000/extintores/1/verificar/ \
  -H "Authorization: Bearer {token}" \
  -d '{"observaciones": "OK"}'

# Como Empresa (debería dar 403)
curl -X POST http://localhost:8000/extintores/1/verificar/ \
  -H "Authorization: Bearer {token_empresa}" \
  -d '{"observaciones": "Test"}'
```
