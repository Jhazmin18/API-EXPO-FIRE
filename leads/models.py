from django.db import models


class Lead(models.Model):
    nombre = models.CharField(max_length=180)
    empresa = models.CharField(max_length=180)
    correo = models.EmailField()
    telefono = models.CharField(max_length=40)
    servicio = models.CharField(max_length=160)
    mensaje = models.TextField(blank=True)
    captcha_success = models.BooleanField(default=False)
    captcha_challenge_ts = models.DateTimeField(null=True, blank=True)
    captcha_hostname = models.CharField(max_length=255, blank=True)
    captcha_action = models.CharField(max_length=255, blank=True)
    captcha_cdata = models.CharField(max_length=255, blank=True)
    email_enviado = models.BooleanField(default=False)
    email_enviado_at = models.DateTimeField(null=True, blank=True)
    email_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f'{self.nombre} - {self.empresa}'
