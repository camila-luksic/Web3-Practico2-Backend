from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from banco.apis import UserSerializer,CuentaSerializer
from banco.models import Beneficiario, Movimiento
from banco.models.cuenta import Cuenta



class MovimientoSerializer(serializers.ModelSerializer):

    nroCuenta = serializers.PrimaryKeyRelatedField(
        queryset=Cuenta.objects.all(),
        source='cuenta',
        write_only=True
    )
    cuenta= CuentaSerializer(
        read_only=True,
        many=False
    )

    class Meta:
        model = Movimiento
        fields = '__all__'

    def create(self, validated_data):

        tipo = validated_data['tipo']
        monto = validated_data['monto']
        cuenta = validated_data['cuenta']

        if tipo not in ('ingreso', 'egreso'):
            raise ValidationError("El tipo de movimiento debe ser 'ingreso' o 'egreso'.")


        cuenta = Cuenta.objects.select_for_update().get(pk=cuenta.pk)



        if tipo == 'ingreso':
            cuenta.saldo += monto
        elif tipo == 'egreso':
            if cuenta.saldo >= monto:
                cuenta.saldo -= monto
            else:
                raise ValidationError("Saldo insuficiente para el egreso.")


        cuenta.save()


        movimiento = Movimiento.objects.create(**validated_data)
        return movimiento


class MovimientoViewSet(viewsets.ModelViewSet):
    queryset = Movimiento.objects.all()
    serializer_class = MovimientoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        user = self.request.user
        cuentas_del_usuario = Cuenta.objects.filter(usuario=user)
        return Movimiento.objects.filter(cuenta__in=cuentas_del_usuario)
