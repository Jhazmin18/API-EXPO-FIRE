from django.core.management.base import BaseCommand

from forms.models import FormTemplate, Question


class Command(BaseCommand):
    help = 'Siembra la plantilla UIPC_SEH con preguntas específicas.'

    PREGUNTAS = [
        {
            'clave': 'ubicacion_correcta',
            'etiqueta': 'Ubicación correcta del extintor',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 1,
            'reglas_visibilidad': None,
            'reglas_validacion': None,
        },
        {
            'clave': 'tiene_senaletica',
            'etiqueta': '¿Cuenta con señalética del extintor?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 2,
        },
        {
            'clave': 'tiene_seguro_metalico',
            'etiqueta': '¿Cuenta con seguro metálico?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 3,
        },
        {
            'clave': 'seguro_con_marchamo',
            'etiqueta': 'El seguro cuenta con marchamo',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 4,
        },
        {
            'clave': 'presion_optima',
            'etiqueta': '¿Cuenta con presión óptima?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': True,
            'orden': 5,
            'reglas_visibilidad': {
                'mostrar_si': [
                    {'campo': 'agente_extintor', 'operador': '!=', 'valor': 'CO2'},
                ]
            },
        },
        {
            'clave': 'tiene_corbatin',
            'etiqueta': '¿Cuenta con corbatín?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 6,
            'reglas_visibilidad': {
                'mostrar_si': [
                    {'campo': 'agente_extintor', 'operador': '==', 'valor': 'PQS'},
                    {
                        'campo': 'tipo_servicio',
                        'operador': 'in',
                        'valor': ['mantenimiento', 'recarga'],
                    },
                ]
            },
        },
        {
            'clave': 'danos_cilindro',
            'etiqueta': '¿Cuenta con daños físicos el cilindro?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': True,
            'orden': 7,
        },
        {
            'clave': 'danos_cilindro_descripcion',
            'etiqueta': 'Descripción de daños',
            'tipo': Question.TIPO_TEXTO,
            'requerido': False,
            'orden': 8,
            'reglas_validacion': {
                'requerido_si': {'campo': 'danos_cilindro', 'operador': '==', 'valor': True},
                'min_longitud': 5,
            },
        },
        {
            'clave': 'vigente_mantenimiento_recarga',
            'etiqueta': '¿Se encuentra vigente la fecha de mantenimiento/recarga?',
            'tipo': Question.TIPO_BOOLEANO,
            'requerido': False,
            'orden': 9,
        },
        {
            'clave': 'reporte_equipo',
            'etiqueta': '¿Desea enviar algún reporte de este equipo?',
            'tipo': Question.TIPO_TEXTO,
            'requerido': False,
            'orden': 10,
        },
    ]

    def handle(self, *args, **options):
        plantilla, _ = FormTemplate.objects.update_or_create(
            codigo='UIPC_SEH',
            version=1,
            defaults={
                'titulo': 'Revisión UIPC/SEH',
                'activo': True,
                'descripcion': 'Plantilla oficial para inspecciones UIPC/SEH.',
            },
        )
        plantilla.activo = True
        plantilla.save()

        for datos in self.PREGUNTAS:
            pregunta, _ = Question.objects.update_or_create(
                template=plantilla,
                clave=datos['clave'],
                defaults={
                    'etiqueta': datos['etiqueta'],
                    'tipo': datos['tipo'],
                    'requerido': datos.get('requerido', False),
                    'orden': datos['orden'],
                    'reglas_visibilidad': datos.get('reglas_visibilidad'),
                    'reglas_validacion': datos.get('reglas_validacion'),
                },
            )

        self.stdout.write(self.style.SUCCESS('Plantilla UIPC_SEH sembrada con éxito.'))
