# dashboard/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from empresas.models import Empresa
from extintores.models import Extintor
from usuarios.models import Perfil


class SuperAdminKPIsView(APIView):
    """
    GET /dashboard/superadmin/kpis/
    KPIs globales para el dashboard del superadmin
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Verificar que sea superadmin
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol != Perfil.ROLE_SUPERADMIN:
            return Response(
                {'error': 'Solo superadmins pueden acceder'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # KPIs de empresas
        total_empresas = Empresa.objects.count()
        empresas_activas = Empresa.objects.filter(activa=True).count()
        empresas_inactivas = Empresa.objects.filter(activa=False).count()

        # KPIs de extintores
        total_extintores = Extintor.objects.count()
        
        # Calcular estados
        extintores = Extintor.objects.all()
        estados = {'verde': 0, 'amarillo': 0, 'rojo': 0}
        for ext in extintores:
            estados[ext.estado] += 1

        # Extintores por vencer (próximos 30 días)
        hoy = timezone.now().date()
        mes_proximo = hoy + timedelta(days=30)
        por_vencer = Extintor.objects.filter(
            fecha_vencimiento__lte=mes_proximo,
            fecha_vencimiento__gte=hoy
        ).count()

        # Revisiones pendientes
        revisiones_pendientes = Extintor.objects.filter(
            proxima_revision__lte=hoy
        ).count()

        data = {
            'empresas': {
                'total': total_empresas,
                'activas': empresas_activas,
                'inactivas': empresas_inactivas,
                'porcentaje_activas': round((empresas_activas / total_empresas * 100), 1) if total_empresas > 0 else 0
            },
            'extintores': {
                'total': total_extintores,
                'por_estado': {
                    'verde': estados['verde'],
                    'amarillo': estados['amarillo'],
                    'rojo': estados['rojo'],
                },
                'por_vencer_30_dias': por_vencer,
                'revisiones_pendientes': revisiones_pendientes,
            },
            'fecha_actualizacion': timezone.now().isoformat()
        }
        
        return Response(data)


class RiesgoEmpresasView(APIView):
    """
    GET /dashboard/superadmin/riesgo-empresas/
    Ranking de empresas por nivel de riesgo
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol != Perfil.ROLE_SUPERADMIN:
            return Response(
                {'error': 'Solo superadmins pueden acceder'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        empresas = Empresa.objects.filter(activa=True).prefetch_related('extintores')
        ranking = []

        for empresa in empresas:
            extintores = empresa.extintores.all()
            total = extintores.count()
            
            if total == 0:
                continue

            # Calcular porcentaje de extintores en rojo
            rojos = sum(1 for e in extintores if e.estado == 'rojo')
            amarillos = sum(1 for e in extintores if e.estado == 'amarillo')
            
            porcentaje_rojo = (rojos / total) * 100
            porcentaje_amarillo = (amarillos / total) * 100

            # Nivel de riesgo
            if porcentaje_rojo > 30:
                nivel_riesgo = 'ALTO'
            elif porcentaje_rojo > 15 or porcentaje_amarillo > 40:
                nivel_riesgo = 'MEDIO'
            else:
                nivel_riesgo = 'BAJO'

            ranking.append({
                'empresa_id': empresa.id,
                'empresa_nombre': empresa.nombre,
                'tipo_inmueble': empresa.tipo_inmueble,
                'total_extintores': total,
                'extintores_rojos': rojos,
                'extintores_amarillos': amarillos,
                'extintores_verdes': total - rojos - amarillos,
                'porcentaje_rojo': round(porcentaje_rojo, 1),
                'porcentaje_amarillo': round(porcentaje_amarillo, 1),
                'nivel_riesgo': nivel_riesgo,
            })

        # Ordenar por mayor riesgo
        ranking.sort(key=lambda x: (x['porcentaje_rojo'], x['porcentaje_amarillo']), reverse=True)
        
        return Response(ranking[:20])  # Top 20


class ActividadRecienteView(APIView):
    """
    GET /dashboard/superadmin/actividad/
    Actividad reciente normalizada (creaciones, actualizaciones)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol != Perfil.ROLE_SUPERADMIN:
            return Response(
                {'error': 'Solo superadmins pueden acceder'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # Últimos 7 días
        desde = timezone.now() - timedelta(days=7)
        
        # Actividad de empresas
        empresas_nuevas = Empresa.objects.filter(created_at__gte=desde).select_related('creado_por')
        
        # Actividad de extintores
        extintores_nuevos = Extintor.objects.filter(created_at__gte=desde).select_related('creado_por', 'empresa')
        
        actividades = []

        # Formatear actividades de empresas
        for emp in empresas_nuevas:
            creador = emp.creado_por
            nombre_creador = creador.get_full_name() or creador.username if creador else 'Sistema'
            
            actividades.append({
                'id': f'emp_{emp.id}',
                'tipo': 'EMPRESA',
                'accion': 'CREACIÓN',
                'descripcion': f'Nueva empresa: {emp.nombre}',
                'usuario': nombre_creador,
                'fecha': emp.created_at.isoformat(),
                'icono': 'building',
                'color': '#10b981'
            })

        # Formatear actividades de extintores
        for ext in extintores_nuevos:
            creador = ext.creado_por
            nombre_creador = creador.get_full_name() or creador.username if creador else 'Sistema'
            empresa_nombre = ext.empresa.nombre if ext.empresa else 'Sin empresa'
            
            actividades.append({
                'id': f'ext_{ext.id}',
                'tipo': 'EXTINTOR',
                'accion': 'CREACIÓN',
                'descripcion': f'Nuevo extintor {ext.codigo} - {empresa_nombre}',
                'usuario': nombre_creador,
                'fecha': ext.created_at.isoformat(),
                'icono': 'flame',
                'color': '#ef4444'
            })

        # Ordenar por fecha (más reciente primero)
        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        
        return Response(actividades[:30])  # Últimas 30 actividades


class AlertasOperativasView(APIView):
    """
    GET /dashboard/superadmin/alertas/
    Alertas operativas centralizadas
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        perfil = getattr(request.user, 'perfil', None)
        if not perfil or perfil.rol != Perfil.ROLE_SUPERADMIN:
            return Response(
                {'error': 'Solo superadmins pueden acceder'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        hoy = timezone.now().date()
        semana_proxima = hoy + timedelta(days=7)
        mes_proximo = hoy + timedelta(days=30)
        
        alertas = []

        # 1. Extintores vencidos
        vencidos = Extintor.objects.filter(
            fecha_vencimiento__lt=hoy
        ).select_related('empresa')
        
        for ext in vencidos[:10]:
            alertas.append({
                'id': f'vencido_{ext.id}',
                'tipo': 'CRÍTICA',
                'categoria': 'VENCIMIENTO',
                'titulo': f'Extintor vencido: {ext.codigo}',
                'descripcion': f'Venció el {ext.fecha_vencimiento.strftime("%d/%m/%Y")}',
                'empresa': ext.empresa.nombre if ext.empresa else 'Sin empresa',
                'fecha': ext.fecha_vencimiento.isoformat(),
                'severidad': 'alta',
                'accion_requerida': 'Reemplazo inmediato'
            })

        # 2. Extintores por vencer (próximos 7 días)
        por_vencer = Extintor.objects.filter(
            fecha_vencimiento__gte=hoy,
            fecha_vencimiento__lte=semana_proxima
        ).select_related('empresa')
        
        for ext in por_vencer[:10]:
            dias = (ext.fecha_vencimiento - hoy).days
            alertas.append({
                'id': f'por_vencer_{ext.id}',
                'tipo': 'ADVERTENCIA',
                'categoria': 'PRÓXIMO VENCIMIENTO',
                'titulo': f'Extintor por vencer: {ext.codigo}',
                'descripcion': f'Vence en {dias} días ({ext.fecha_vencimiento.strftime("%d/%m/%Y")})',
                'empresa': ext.empresa.nombre if ext.empresa else 'Sin empresa',
                'fecha': ext.fecha_vencimiento.isoformat(),
                'severidad': 'media',
                'accion_requerida': 'Programar recarga'
            })

        # 3. Revisiones vencidas
        revisiones_vencidas = Extintor.objects.filter(
            proxima_revision__lt=hoy
        ).select_related('empresa')
        
        for ext in revisiones_vencidas[:10]:
            alertas.append({
                'id': f'revision_{ext.id}',
                'tipo': 'CRÍTICA',
                'categoria': 'REVISIÓN VENCIDA',
                'titulo': f'Revisión vencida: {ext.codigo}',
                'descripcion': f'Revisión debía ser el {ext.proxima_revision.strftime("%d/%m/%Y")}',
                'empresa': ext.empresa.nombre if ext.empresa else 'Sin empresa',
                'fecha': ext.proxima_revision.isoformat(),
                'severidad': 'alta',
                'accion_requerida': 'Revisión técnica urgente'
            })

        # 4. Revisiones próximas (próximos 15 días)
        proximas_revisiones = Extintor.objects.filter(
            proxima_revision__gte=hoy,
            proxima_revision__lte=mes_proximo
        ).select_related('empresa')
        
        for ext in proximas_revisiones[:10]:
            dias = (ext.proxima_revision - hoy).days
            alertas.append({
                'id': f'prox_revision_{ext.id}',
                'tipo': 'INFORMATIVA',
                'categoria': 'REVISIÓN PRÓXIMA',
                'titulo': f'Revisión próxima: {ext.codigo}',
                'descripcion': f'Revisión programada en {dias} días ({ext.proxima_revision.strftime("%d/%m/%Y")})',
                'empresa': ext.empresa.nombre if ext.empresa else 'Sin empresa',
                'fecha': ext.proxima_revision.isoformat(),
                'severidad': 'baja',
                'accion_requerida': 'Agendar revisión'
            })

        # 5. Empresas sin extintores
        empresas_sin_extintores = Empresa.objects.annotate(
            num_extintores=Count('extintores')
        ).filter(num_extintores=0, activa=True)
        
        for emp in empresas_sin_extintores[:5]:
            alertas.append({
                'id': f'sin_ext_{emp.id}',
                'tipo': 'ADVERTENCIA',
                'categoria': 'SIN EXTINTORES',
                'titulo': f'Empresa sin extintores: {emp.nombre}',
                'descripcion': 'No tiene extintores registrados',
                'empresa': emp.nombre,
                'fecha': emp.created_at.isoformat(),
                'severidad': 'media',
                'accion_requerida': 'Registrar extintores'
            })

        # Ordenar por severidad y fecha
        severidad_orden = {'alta': 0, 'media': 1, 'baja': 2}
        alertas.sort(key=lambda x: (severidad_orden[x['severidad']], x['fecha']), reverse=False)
        
        return Response({
            'total': len(alertas),
            'por_severidad': {
                'alta': sum(1 for a in alertas if a['severidad'] == 'alta'),
                'media': sum(1 for a in alertas if a['severidad'] == 'media'),
                'baja': sum(1 for a in alertas if a['severidad'] == 'baja'),
            },
            'alertas': alertas[:50]  # Máximo 50 alertas
        })