from django.contrib.auth.models import User
from django.db import models

from banco.models import Cuenta


class Beneficiario(models.Model):
    nombreCompleto = models.CharField(max_length=100)
    # Cuenta de la cual es beneficiario
    cuenta_beneficiaria = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name='beneficiarios_de' ,default=1
    )
    # Usuario que es el beneficiario
    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='beneficiarios'
    )
    # Cuenta propia del beneficiario
    cuenta_propia = models.ForeignKey(
        Cuenta, on_delete=models.CASCADE, related_name='propietarios',default=1
    )

    def __str__(self):
        return f"{self.nombreCompleto} - Beneficiario de: {self.cuenta_beneficiaria} - Propietario de: {self.cuenta_propia}"

