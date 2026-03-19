"""
Modelos especÃ­ficos del dominio de usuarios.

AquÃ­ reside el perfil extendido que enlaza con el usuario autenticado.
"""
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Perfil(models.Model):
    """
    Perfil extendido para almacenar datos que no caben en User.
    """

    ROLE_SUPERADMIN = 'SUPERADMIN'
    ROLE_ADMIN_EMPRESA = 'ADMIN_EMPRESA'
    ROLE_SUPERVISOR = 'SUPERVISOR'
    ROLE_ANALISTA = 'ANALISTA'

    ROLE_CHOICES = [
        (ROLE_SUPERADMIN, 'Expro Fire'),
        (ROLE_ADMIN_EMPRESA, 'Admin. Empresa'),
        (ROLE_SUPERVISOR, 'Supervisor General'),
        (ROLE_ANALISTA, 'Analista'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='Usuario'
    )
    empresa = models.ForeignKey(
        'empresas.Empresa',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfiles',
        verbose_name='Empresa'
    )
    foto_perfil = models.ImageField(
        upload_to='perfiles/',
        blank=True,
        null=True,
        verbose_name='Foto de perfil'
    )
    telefono = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono'
    )
    domicilio = models.CharField(
        max_length=250,
        blank=True,
        verbose_name='Domicilio'
    )
    rol = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_ANALISTA,
        verbose_name='Rol'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de creaciÃ³n'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de actualizaciÃ³n'
    )

    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        ordering = ['user__username']

    def __str__(self):
        return self.user.get_username()

    @property
    def nombre_completo(self):
        return self.user.get_full_name() or self.user.get_username()
