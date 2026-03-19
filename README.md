# Backend - Sistema de Gestión de Extintores

> ✅ **BACKEND COMPLETADO - LISTO PARA PRODUCCIÓN**

Este directorio contiene el backend del Sistema de Gestión de Extintores, desarrollado con Django y Django REST Framework.

**Estado:** 100% Implementado | **Requiere:** Solo configuración inicial

---

## ⚡ Estado del Backend

| Componente | Estado | Detalles |
|------------|--------|----------|
| Modelo de Datos | ✅ Completo | Extintor con QR automático |
| API REST | ✅ Completa | 8 endpoints funcionando |
| Django Admin | ✅ Personalizado | Interfaz visual con colores |
| Autenticación | ✅ Configurada | JWT + Session Auth |
| Generación QR | ✅ Automática | Al crear extintor |
| Sistema de Estados | ✅ Implementado | Semáforo verde/amarillo/rojo |

**📖 Para guía rápida de 10 minutos:** [`../BACKEND_HANDOFF.md`](../BACKEND_HANDOFF.md)

## 🎯 Lo que YA Está Implementado

**No necesitas programar nada.** El backend está 100% completo con:

✅ **Modelo Extintor completo**
- UUID como primary key
- 12 campos incluyendo fechas, ubicación, agente extintor
- Properties calculadas: `estado`, `dias_para_vencer`, `dias_para_revision`
- Generación automática de QR codes
- Timestamps automáticos

✅ **API REST funcional**
- CRUD completo (Create, Read, Update, Delete)
- Endpoint público para QR scanner
- Búsqueda y filtrado
- Paginación automática
- Estadísticas agregadas

✅ **Django Admin personalizado**
- Indicadores visuales de estado (🟢🟡🔴)
- Preview y vista completa de QR codes
- Filtros por agente extintor, fechas
- Búsqueda avanzada
- Campos readonly apropiados

✅ **Sistema completo**
- JWT Authentication configurado
- CORS para frontend
- Variables de entorno
- Migraciones listas
- Scripts de prueba incluidos

**Solo requiere:** Configuración inicial (base de datos, dependencias, variables de entorno)

---

## 📋 Requisitos Previos

- Python 3.9 o superior
- PostgreSQL 12 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

Crear la base de datos en PostgreSQL:

```sql
CREATE DATABASE extintores_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE extintores_db TO postgres;
```

### 4. Configurar variables de entorno

Copiar el archivo `.env.example` como `.env` y ajustar los valores:

```bash
cp .env.example .env
```

Editar `.env` con tus credenciales de base de datos.

### 5. Ejecutar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

Seguir las instrucciones para crear un usuario administrador.

### 7. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Estructura del Proyecto

```
backend/
├── core/                   # Configuración del proyecto Django
│   ├── __init__.py
│   ├── settings.py        # Configuración principal
│   ├── urls.py            # URLs principales
│   ├── wsgi.py
│   └── asgi.py
├── extintores/                    # App principal de la API
│   ├── migrations/        # Migraciones de base de datos
│   ├── __init__.py
│   ├── models.py          # Modelo Extintor
│   ├── serializers.py     # Serializadores DRF
│   ├── views.py           # ViewSets de la API
│   ├── urls.py            # URLs de la API
│   ├── admin.py           # Configuración del Django Admin
│   └── apps.py
├── media/                  # Archivos subidos (QR codes)
├── staticfiles/            # Archivos estáticos
├── manage.py              # Utilidad de Django
├── requirements.txt       # Dependencias Python
├── .env.example          # Plantilla de variables de entorno
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

### Autenticación

- `POST /api/token/` - Obtener token JWT
- `POST /api/token/refresh/` - Refrescar token JWT
- `GET /api/perfil/` - Perfil del usuario autenticado (crea si no existe) 🔒

### Extintores

**Base URL (dev):** `http://localhost:8000`

- `GET /extintores/` - Listar todos los extintores
- `POST /extintores/` - Crear un nuevo extintor
- `GET /extintores/{id}/` - Detalle de un extintor
- `PUT /extintores/{id}/` - Actualizar un extintor
- `PATCH /extintores/{id}/` - Actualización parcial
- `DELETE /extintores/{id}/` - Eliminar un extintor
- `GET /extintores/por-codigo/{codigo}/` - Buscar por código (público)
- `GET /extintores/estadisticas/` - Estadísticas generales
- `GET /extintores/kpis/` - KPIs rápidos (totales, porcentajes por estado y empresas)
- `GET /extintores/{id}/etiqueta/` - Etiqueta QR lista para imprimir
- `POST /extintores/impresionmasiva/` - ZIP con etiquetas PNG (body: `{ "ids": ["uuid1", "uuid2"] }`) 🔒

**Nota:** puedes filtrar listados por empresa usando `?empresa=<id|nombre>`.

### Empresas

**Base URL (dev):** `http://localhost:8000/empresas/`

- `GET /empresas/` - Listar empresas registradas (para filtrar extintores).
- `POST /empresas/` - Crear una nueva empresa responsable.
- `PUT/PATCH /empresas/{id}/` - Actualizar los datos de la empresa.
- `DELETE /empresas/{id}/` - Eliminar una empresa (si no tiene extintores).

### Usuarios / Perfiles

**Base URL (dev):** `http://localhost:8000/usuarios/`

- `GET /usuarios/` - Listar perfiles 🔒
- `POST /usuarios/` - Crear perfil/usuario (solo admin) 🔒
- `GET /usuarios/{id}/` - Detalle de perfil 🔒
- `PATCH /usuarios/{id}/` - Actualizar perfil 🔒

### Django Admin

Acceder a: `http://localhost:8000/admin`

## 📊 Modelo de Datos: Extintor

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | UUID | Identificador único |
| codigo | CharField | Código único del extintor |
| ubicacion | CharField | Ubicación física |
| tipo | CharField | Agente extintor (PQS_ABC, PQS_BC, CO2, AGUA, ESPUMA, HALOTRON, ACETATO_K) |
| capacidad | CharField | Capacidad del extintor |
| fecha_fabricacion | DateField | Fecha de fabricación |
| fecha_vencimiento | DateField | Fecha de vencimiento |
| ultima_revision | DateField | Fecha de última revisión |
| proxima_revision | DateField | Fecha de próxima revisión |
| observaciones | TextField | Notas adicionales |
| empresa | ForeignKey | Empresa responsable (opcional) |
| qr_code | ImageField | Código QR generado |
| created_at | DateTimeField | Fecha de creación |
| updated_at | DateTimeField | Fecha de actualización |

### Modelo Empresa

- `id` (AutoField / int) | identificador único.
- `nombre` (CharField) | nombre de la empresa.
- `razon_social` (CharField) | razón social (opcional).
- `logo` (ImageField) | logo de la empresa (opcional).
- `created_at` (DateTimeField) | timestamp de creación.

### Propiedades Calculadas

- `estado`: Verde, Amarillo o Rojo (según fechas)
- `dias_para_vencer`: Días restantes hasta el vencimiento
- `dias_para_revision`: Días restantes hasta la próxima revisión

## 🎨 Sistema de Estados (Semáforo)

El sistema calcula automáticamente el estado de cada extintor:

- **🟢 VERDE**: Más de 60 días para vencer y más de 30 días para revisión
- **🟡 AMARILLO**: Entre 30-60 días para vencer o 15-30 días para revisión
- **🔴 ROJO**: Menos de 30 días para vencer/vencido o revisión vencida

## 🔐 Autenticación

El sistema usa JWT (JSON Web Tokens) para autenticación:

1. Obtener token:
```bash
POST /api/token/
{
    "username": "tu_usuario",
    "password": "tu_contraseña"
}
```

2. Usar token en requests:
```bash
Authorization: Bearer <tu_token>
```

## 📝 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recopilar archivos estáticos
python manage.py collectstatic

# Shell de Django
python manage.py shell

# Verificar proyecto
python manage.py check
```

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Con cobertura
coverage run --source='.' manage.py test
coverage report
```

## 📦 Dependencias Principales

- **Django 4.2+**: Framework web principal
- **Django REST Framework**: API REST
- **psycopg2-binary**: Conector PostgreSQL
- **djangorestframework-simplejwt**: Autenticación JWT
- **django-cors-headers**: CORS para frontend
- **qrcode**: Generación de códigos QR
- **Pillow**: Procesamiento de imágenes
- **python-dotenv**: Variables de entorno

## 🔧 Configuración Adicional

### CORS

El backend está configurado para aceptar peticiones desde:
- `http://localhost:5173` (Frontend en desarrollo)

Editar en `settings.py` si es necesario.

### Media Files

Los códigos QR se guardan en `media/qr_codes/`

### Admin Personalizado

El Django Admin incluye:
- Vista de lista con estado en colores
- Preview de códigos QR
- Filtros por agente extintor, fechas
- Búsqueda por código y ubicación
- Estadísticas en tiempo real

## 🧪 Scripts de Prueba Incluidos

El proyecto incluye scripts útiles para testing:

### crear_extintor_test.py

Crea un extintor de prueba con todos los campos:

```bash
python crear_extintor_test.py

# Output:
# OK - Extintor creado exitosamente!
#    ID: xxxx-xxxx-xxxx-xxxx
#    Codigo: EXT-001
#    Ubicacion: Planta Baja - Pasillo Principal
#    Estado: verde
#    Dias para vencer: 730
#    QR generado: True
```

**Uso:** Para verificar que todo funciona después del setup

### listar_extintores.py

Lista todos los extintores con formato visual:

```bash
python listar_extintores.py

# Output:
# === Extintores Registrados ===
# 
# [EXT-001] - Planta Baja - Pasillo Principal
#   Agente extintor: CO2 | Capacidad: 5kg
#   Estado: 🟢 VERDE
#   Vencimiento: 2028-01-01 (730 días)
```

**Uso:** Para ver rápidamente todos los extintores sin abrir Django Admin

---

## 🚨 Troubleshooting Expandido

### Error: "django-admin: command not found"

**Causa:** Python no está en PATH o entorno virtual no activado

**Solución:**
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Verificar
which python  # Debería mostrar ruta del venv
```

### Error: "FATAL: password authentication failed for user postgres"

**Causa:** Credenciales incorrectas en `.env`

**Solución:**
1. Verificar contraseña de PostgreSQL:
   ```bash
   psql -U postgres -d postgres
   # Si pide contraseña, usa la que configuraste
   ```
2. Actualizar `DB_PASSWORD` en `.env`
3. Reiniciar servidor Django

### Error: "No such table: extintores_extintor"

**Causa:** Migraciones no ejecutadas

**Solución:**
```bash
python manage.py migrate

# Si persiste:
python manage.py migrate --run-syncdb
```

### Error: "Port 8000 is already in use"

**Causa:** Otro servidor Django corriendo

**Solución:**
```bash
# Opción 1: Usar otro puerto
python manage.py runserver 8080

# Opción 2: Matar proceso (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Opción 2: Matar proceso (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

### Error: ModuleNotFoundError (qrcode, PIL, rest_framework, etc.)

**Causa:** Dependencias no instaladas o entorno virtual no activado

**Solución:**
```bash
# Verificar que venv esté activado
# Deberías ver (venv) al inicio del prompt

# Reinstalar dependencias
pip install -r requirements.txt

# Verificar instalación
pip list | grep django
pip list | grep qrcode
```

### Error: QR code no se genera

**Causa 1:** Permisos en carpeta `media/`

**Solución:**
```bash
# Windows: Click derecho → Propiedades → Seguridad → Dar permisos
# Linux/Mac:
chmod -R 755 media/
```

**Causa 2:** Pillow no instalado correctamente

**Solución:**
```bash
pip uninstall Pillow
pip install Pillow
```

### Error: "ImproperlyConfigured: SECRET_KEY"

**Causa:** Archivo `.env` no existe o no se está leyendo

**Solución:**
```bash
# Crear .env desde ejemplo
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Verificar que existe
ls -la  # Debería mostrar .env
```

### Error: CORS en producción

**Causa:** Frontend en dominio diferente y CORS no configurado

**Solución:**
Editar `settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://tu-dominio-frontend.com",
]
```

### Error: "OperationalError: FATAL: database does not exist"

**Causa:** Base de datos no creada

**Solución:**
```bash
# Conectar a PostgreSQL
psql -U postgres

# Crear base de datos
CREATE DATABASE extintores_db;
\q

# Ejecutar migraciones
python manage.py migrate
```

### Problema: Extintores sin QR

**Causa:** QR no se generó al crear (posible error)

**Solución:**
```bash
python manage.py shell

# Dentro del shell:
>>> from extintores.models import Extintor
>>> for e in Extintor.objects.all():
...     if not e.qr_code:
...         e.generar_qr()
...         e.save()
>>> exit()
```

### Problema: Estado siempre "rojo"

**Causa:** Fechas no configuradas correctamente

**Solución:**
- Verificar que `fecha_vencimiento` y `proxima_revision` estén en el futuro
- Verificar formato de fecha: YYYY-MM-DD
- Revisar zona horaria en `settings.py`

## 📖 Documentación Adicional

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 👥 Desarrollo

Este backend está diseñado para ser:
- **Simple**: Sigue los patrones estándar de Django
- **Autodocumentado**: Comentarios y docstrings claros
- **Extensible**: Fácil de mantener y ampliar
- **Estándar**: Usa Django Admin nativo

## 📄 Licencia

[Especificar licencia del proyecto]
