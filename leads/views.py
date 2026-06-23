import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Lead
from .serializers import LeadCreateSerializer, LeadSerializer


TURNSTILE_SITEVERIFY_URL = 'https://challenges.cloudflare.com/turnstile/v0/siteverify'


class LeadCreateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LeadCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        captcha_result = self._verify_turnstile(
            serializer.validated_data['captchaToken'],
            self._get_client_ip(request),
        )
        if not captcha_result.get('success'):
            return Response(
                {
                    'detail': 'Captcha inválido.',
                    'captcha_errors': captcha_result.get('error-codes', []),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        lead = Lead.objects.create(
            nombre=serializer.validated_data['nombre'],
            empresa=serializer.validated_data['empresa'],
            correo=serializer.validated_data['correo'],
            telefono=serializer.validated_data['telefono'],
            servicio=serializer.validated_data['servicio'],
            mensaje=serializer.validated_data.get('mensaje', ''),
            captcha_success=True,
            captcha_challenge_ts=self._parse_turnstile_datetime(captcha_result.get('challenge_ts')),
            captcha_hostname=captcha_result.get('hostname', ''),
            captcha_action=captcha_result.get('action', ''),
            captcha_cdata=captcha_result.get('cdata', ''),
        )
        self._send_lead_email(lead)

        return Response(
            {
                'detail': 'Lead recibido correctamente.',
                'lead': LeadSerializer(lead).data,
                'email_enviado': lead.email_enviado,
                'email_error': lead.email_error or None,
            },
            status=status.HTTP_201_CREATED,
        )

    def _verify_turnstile(self, token, remote_ip=None):
        secret = getattr(settings, 'TURNSTILE_SECRET_KEY', '')
        if not secret:
            return {'success': False, 'error-codes': ['missing-secret-key']}

        payload = {
            'secret': secret,
            'response': token,
        }
        if remote_ip:
            payload['remoteip'] = remote_ip

        data = urlencode(payload).encode('utf-8')
        request = Request(
            TURNSTILE_SITEVERIFY_URL,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST',
        )

        try:
            with urlopen(request, timeout=8) as response:
                return json.loads(response.read().decode('utf-8'))
        except (URLError, TimeoutError, json.JSONDecodeError):
            return {'success': False, 'error-codes': ['siteverify-unavailable']}

    def _get_client_ip(self, request):
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _parse_turnstile_datetime(self, value):
        if not value:
            return None
        return parse_datetime(value)
    
    def _send_lead_email(self, lead):
        recipients = getattr(settings, 'LEADS_TO_EMAIL', [])
        if not recipients:
            lead.email_error = 'No se configuró LEADS_TO_EMAIL.'
            lead.save(update_fields=['email_error'])
            return

        # Si por alguna razón LEADS_TO_EMAIL viene como texto plano en lugar de lista, lo convierte
        if isinstance(recipients, str):
            recipients = [email.strip() for email in recipients.split(',')]

        try:
            # Enviamos el correo con fail_silently=True
            sent = send_mail(
                f'Nuevo lead: {lead.nombre} - {lead.empresa}',
                f'Nombre: {lead.nombre}; Empresa: {lead.empresa}; Correo: {lead.correo}; Telefono: {lead.telefono}; Servicio: {lead.servicio}; Mensaje: {lead.mensaje}',
                settings.DEFAULT_FROM_EMAIL,
                recipients,
                fail_silently=True,  # <-- ESTO EVITA EL TIMEOUT DE 30 SEGUNDOS
            )
            
            # Si sent es mayor a 0, el correo se envió con éxito. Si es 0, falló en silencio.
            lead.email_enviado = sent > 0
            lead.email_enviado_at = timezone.now() if lead.email_enviado else None
            lead.email_error = '' if lead.email_enviado else 'Timeout o rechazo silencioso del servidor SMTP (Gmail).'
            
        except Exception as exc:
            # Esto solo atrapará errores raros del código, no caídas de conexión
            lead.email_enviado = False
            lead.email_error = str(exc)[:2000]

        # Guarda los resultados en la base de datos para que puedas auditarlos
        lead.save(update_fields=['email_enviado', 'email_enviado_at', 'email_error'])