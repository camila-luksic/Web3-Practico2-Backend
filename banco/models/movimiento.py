from django.db import models

from banco.models import Cuenta


class Movimiento(models.Model):
    Tipos = [
        ("ingreso", "Ingreso"),
        ("egreso", "Egreso"),
        ("transferencia", "transferencia"),
    ]
    tipo = models.CharField(max_length=20, choices=Tipos)
    cuenta = models.ForeignKey(Cuenta, on_delete=models.CASCADE)

    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cuenta} {self.tipo} {self.monto} {self.fecha}  "
