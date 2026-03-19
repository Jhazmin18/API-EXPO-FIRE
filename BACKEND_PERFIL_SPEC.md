# Requerimiento: Endpoint de Perfil de Usuario

## Contexto
El frontend necesita un endpoint para mostrar la información del perfil del usuario autenticado en una página dedicada.

## Endpoint Requerido

### GET /api/perfil/

**Descripción:** Devuelve la información del perfil del usuario autenticado.

**Autenticación:** 
- Requiere token JWT en header `Authorization: Bearer {token}`
- Mismo sistema de autenticación que se usa actualmente para `/api/extintores/`

---

## Respuesta Esperada

### Estructura JSON

```json
{
  "id": "uuid-o-integer",
  "username": "admin",
  "email": "admin@empresa.com",
  "nombre_completo": "Juan Pérez García",
  "empresa": "EXPRO FIRE",
  "foto_perfil": "http://localhost:8000/media/perfiles/foto.jpg",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-20T15:30:00Z"
}
```

### Descripción de Campos

#### Campos Obligatorios:
- **`username`** (string): Nombre de usuario del sistema
- **`email`** (string): Correo electrónico del usuario

#### Campos Opcionales:
- **`id`** (string|integer): Identificador del perfil
- **`nombre_completo`** (string): Nombre completo del usuario
  - Puede ser `null` o string vacío `""`
  - Si no existe, frontend mostrará "Nombre no disponible"
  
- **`empresa`** (string): Nombre de la empresa del usuario
  - Puede ser `null` o string vacío `""`
  - Si no existe, frontend mostrará "No especificada"
  
- **`foto_perfil`** (string|null): URL **completa** de la foto de perfil
  - Debe ser URL completa: `http://localhost:8000/media/perfiles/foto.jpg`
  - NO ruta relativa: `/media/perfiles/foto.jpg` ❌
  - Si no existe foto: `null`
  - Frontend mostrará avatar con inicial del nombre si es `null`
  
- **`created_at`** (datetime): Fecha de creación del perfil/usuario
  - Formato ISO 8601: `"2026-01-15T10:00:00Z"`
  - Frontend lo formateará a: "15 de enero, 2026"
  
- **`updated_at`** (datetime): Fecha de última actualización
  - Formato ISO 8601
  - Opcional, puede omitirse si no es relevante

---

## Códigos de Respuesta HTTP

| Código | Descripción | Cuándo usarlo |
|--------|-------------|---------------|
| **200 OK** | Perfil obtenido exitosamente | Respuesta normal |
| **401 Unauthorized** | Token inválido o no proporcionado | Usuario no autenticado |
| **404 Not Found** | Usuario no tiene perfil | *Opcional: Pueden crear el perfil automáticamente* |

---

## Implementación Sugerida

### Opción 1: Crear Perfil Automático (Recomendado)
Si el usuario no tiene un perfil asociado, el endpoint puede crearlo automáticamente con valores por defecto:

```python
try:
    perfil = request.user.perfil
except Perfil.DoesNotExist:
    perfil = Perfil.objects.create(
        user=request.user,
        nombre_completo="",
        empresa="",
        foto_perfil=None
    )
```

**Beneficio:** El frontend siempre recibe `200 OK` con datos (aunque sean vacíos).

### Opción 2: Retornar 404
Si prefieren que el admin cree los perfiles manualmente, pueden retornar `404 Not Found`.

---

## Relación con User de Django

El perfil debe estar relacionado con el modelo `User` de Django:

```python
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nombre_completo = models.CharField(max_length=200, blank=True)
    empresa = models.CharField(max_length=200, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Acceso a datos de User:
- `username`: desde `request.user.username` o `perfil.user.username`
- `email`: desde `request.user.email` o `perfil.user.email`

---

## Ejemplo de Request

```bash
curl -X GET http://localhost:8000/api/perfil/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

---

## Ejemplo de Response Exitoso (200 OK)

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@exprofire.com",
  "nombre_completo": "Juan Pérez García",
  "empresa": "EXPRO FIRE",
  "foto_perfil": "http://localhost:8000/media/perfiles/admin_photo.jpg",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-20T15:30:00Z"
}
```

---

## Ejemplo de Response con Perfil Vacío (200 OK)

```json
{
  "id": 2,
  "username": "operador1",
  "email": "operador1@exprofire.com",
  "nombre_completo": "",
  "empresa": "",
  "foto_perfil": null,
  "created_at": "2026-01-20T08:00:00Z",
  "updated_at": "2026-01-20T08:00:00Z"
}
```

---

## Ejemplo de Response de Error (401)

```json
{
  "detail": "No se proporcionaron las credenciales de autenticación."
}
```

---

## Estado Actual del Frontend

✅ El frontend **ya está implementado** con:
- Página de perfil completa (`/perfil`)
- Diseño responsive (mobile + desktop)
- Manejo de estados de carga y errores
- Avatar con iniciales si no hay foto
- Datos mock temporales para testing

⏳ **Esperando:** Endpoint `/api/perfil/` del backend

🔄 **Cuando esté listo:** Solo necesitamos descomentar el código de integración en:
- `frontend/src/pages/Perfil.jsx` (línea ~47)
- `frontend/src/context/AuthContext.jsx` (línea ~18)

---

## Notas Adicionales

1. **Solo lectura:** Por ahora, el endpoint solo necesita devolver información (GET). La edición puede implementarse después si es necesario.

2. **Consistencia con extintores:** El endpoint debe usar el mismo sistema de autenticación JWT que `/api/extintores/`.

3. **URL de foto:** Es crítico que `foto_perfil` sea URL completa (con dominio) para que funcione en el frontend.

4. **Valores nulos:** El frontend está preparado para manejar campos `null` o vacíos de forma elegante.

---

## Preguntas Frecuentes

**P: ¿Necesitan crear un modelo nuevo?**  
R: Sí, un modelo `Perfil` con relación OneToOne al `User` de Django.

**P: ¿Los perfiles se crean manualmente o automáticamente?**  
R: Recomendamos creación automática en el endpoint, pero pueden hacerlo manual si prefieren.

**P: ¿Necesitan endpoints de edición (PUT/PATCH)?**  
R: No por ahora. Solo visualización (GET) es suficiente para la primera versión.

**P: ¿Qué pasa con usuarios que ya existen?**  
R: Pueden crear perfiles vacíos para usuarios existentes con un comando de Django o creación automática en el endpoint.

---

## Contacto para Dudas

Si tienen preguntas sobre la integración o necesitan ajustar algo, por favor avisen y ajustamos el frontend según sea necesario.
