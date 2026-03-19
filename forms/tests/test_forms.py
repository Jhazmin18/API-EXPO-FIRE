from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from empresas.models import Empresa
from extintores.models import Extintor
from forms.models import FormRun, FormTemplate


class FormsWorkflowTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_forms')
        cls.usuario = get_user_model().objects.create_user(
            username='tecnico',
            password='clave-segura',
        )
        cls.empresa = Empresa.objects.create(nombre='Oxígeno SA')
        hoy = date.today()
        cls.extintor_pqs = Extintor.objects.create(
            codigo='EXT-PQS-01',
            ubicacion='Planta Baja',
            tipo='PQS_ABC',
            capacidad='6 kg',
            fecha_vencimiento=hoy + timedelta(days=365),
            proxima_revision=hoy + timedelta(days=180),
            empresa=cls.empresa,
        )
        cls.extintor_co2 = Extintor.objects.create(
            codigo='EXT-CO2-01',
            ubicacion='Almacén',
            tipo='CO2',
            capacidad='5 kg',
            fecha_vencimiento=hoy + timedelta(days=365),
            proxima_revision=hoy + timedelta(days=180),
            empresa=cls.empresa,
        )
        cls.template = FormTemplate.objects.get(codigo='UIPC_SEH', version=1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.usuario)
        self.base_url = '/api/forms/runs/'

    def _payload(self, scope_id=None, estado=FormRun.ESTADO_BORRADOR, tipo_servicio='mantenimiento', respuestas=None):
        return {
            'template': self.template.pk,
            'empresa': self.empresa.pk,
            'estado': estado,
            'scope_type': FormRun.SCOPE_EXTINTOR,
            'scope_id': scope_id,
            'tipo_servicio': tipo_servicio,
            'respuestas_json': respuestas or {'ubicacion_correcta': True},
        }

    def test_crea_run_borrador_sin_requeridos(self):
        payload = self._payload(scope_id=str(self.extintor_pqs.pk), estado=FormRun.ESTADO_BORRADOR)
        response = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FormRun.objects.count(), 1)

    def test_completar_sin_requeridos_retorna_error(self):
        respuestas = {
            'ubicacion_correcta': True,
            'tiene_senaletica': True,
        }
        payload = self._payload(
            scope_id=str(self.extintor_pqs.pk),
            estado=FormRun.ESTADO_COMPLETADO,
            respuestas=respuestas,
        )
        response = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('respuestas_json', response.data)

    def test_completar_tipo_invalido(self):
        respuestas = {
            'ubicacion_correcta': True,
            'tiene_senaletica': True,
            'presion_optima': 'si',
            'danos_cilindro': True,
            'danos_cilindro_descripcion': 'Daño evidente',
            'vigente_mantenimiento_recarga': True,
        }
        payload = self._payload(
            scope_id=str(self.extintor_pqs.pk),
            estado=FormRun.ESTADO_COMPLETADO,
            respuestas=respuestas,
        )
        response = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('presion_optima', response.data['respuestas_json'])

    def test_presion_optima_co2_normalizada(self):
        respuestas = {
            'ubicacion_correcta': True,
            'presion_optima': True,
            'danos_cilindro': False,
            'vigente_mantenimiento_recarga': True,
        }
        payload = self._payload(
            scope_id=str(self.extintor_co2.pk),
            estado=FormRun.ESTADO_COMPLETADO,
            respuestas=respuestas,
        )
        response = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(response.status_code, 201)
        run_id = response.data['id']
        run = FormRun.objects.get(pk=run_id)
        self.assertNotIn('presion_optima', run.respuestas_json)

    def test_danos_sin_descripcion_retorna_error(self):
        respuestas = {
            'ubicacion_correcta': True,
            'tiene_senaletica': True,
            'presion_optima': True,
            'danos_cilindro': True,
            'vigente_mantenimiento_recarga': True,
        }
        payload = self._payload(
            scope_id=str(self.extintor_pqs.pk),
            estado=FormRun.ESTADO_COMPLETADO,
            respuestas=respuestas,
        )
        response = self.client.post(self.base_url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('danos_cilindro_descripcion', response.data['respuestas_json'])

    def test_crea_template_via_api(self):
        payload = {
            'codigo': 'CONSULTA_VT',
            'titulo': 'Consulta VT',
            'version': 1,
            'activo': True,
            'descripcion': 'Plantilla de prueba',
            'preguntas': [
                {
                    'clave': 'en_establecimiento',
                    'etiqueta': '¿Estás en el establecimiento?',
                    'tipo': 'seleccion',
                    'orden': 1,
                    'opciones': [
                        {'valor': 'si', 'etiqueta': 'Sí', 'orden': 1},
                        {'valor': 'no', 'etiqueta': 'No', 'orden': 2},
                    ],
                },
                {
                    'clave': 'ubicacion',
                    'etiqueta': 'Ubicación',
                    'tipo': 'texto',
                    'orden': 2,
                },
            ],
        }
        response = self.client.post('/api/forms/templates/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(FormTemplate.objects.filter(codigo='CONSULTA_VT').count(), 1)
