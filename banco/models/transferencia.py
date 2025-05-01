from django.db import models

from banco.models import Cuenta


class Transferencia(models.Model):
    emisor = models.ForeignKey(Cuenta, related_name='transferencias_enviadas', on_delete=models.CASCADE)
    receptor = models.ForeignKey(Cuenta, related_name='transferencias_recibidas', on_delete=models.CASCADE)
    monto = models.CharField(max_length=10)
    fecha = models.DateField(null=True)


def __str__(self):
    return f"{self.emisor} {self.monto} {self.fecha} {self.receptor} "
