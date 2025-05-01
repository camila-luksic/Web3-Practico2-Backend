from decimal import Decimal

from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from banco.apis import UserSerializer, CuentaSerializer
from banco.models import Transferencia, Movimiento
from banco.models.cuenta import Cuenta



class TransferenciaSerializer(serializers.ModelSerializer):
    emisor = (CuentaSerializer(read_only=True))  # Serializa la cuenta completa del emisor
    receptor = CuentaSerializer(read_only=True)  # Serializa la cuenta completa del receptor
    emisor_id = serializers.PrimaryKeyRelatedField(  # Para la creación/actualización
        queryset=Cuenta.objects.all(),
        source='emisor',  # Establece la fuente correctamente
        write_only=True,
        required=True
    )
    receptor_id = serializers.PrimaryKeyRelatedField(  # Para la creación/actualización
        queryset=Cuenta.objects.all(),
        source='receptor',  # Establece la fuente correctamente
        write_only=True,
        required=True
    )

    class Meta:
        model = Transferencia
        fields = '__all__'


class TransferenciaViewSet(viewsets.ModelViewSet):
    queryset = Transferencia.objects.all()
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated]  # Añade esta línea para requerir autenticación

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emisor_id = serializer.validated_data['emisor'].id
        receptor_id = serializer.validated_data['receptor'].id
        monto_str = serializer.validated_data['monto']  # Obtén el monto como string

        try:
            monto = Decimal(monto_str)  # Intenta convertir a Decimal
        except (TypeError, ValueError):
            return Response({'error': 'El monto debe ser un número válido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. Obtener las cuentas
                emisor = Cuenta.objects.select_for_update().get(id=emisor_id)
                receptor = Cuenta.objects.select_for_update().get(id=receptor_id)

                if emisor.usuario != request.user:
                    raise serializers.ValidationError(
                        "No tienes permiso para realizar esta transferencia desde esta cuenta.")

                # 2. Validar el saldo
                if emisor.saldo < monto:
                    raise serializers.ValidationError("Saldo insuficiente para la transferencia.")

                # 3. Crear la transferencia
                transferencia = Transferencia.objects.create(
                    emisor=emisor,
                    receptor=receptor,
                    monto=monto,
                )

                # 4. Crear los movimientos
                Movimiento.objects.create(
                    tipo='egreso',
                    cuenta=emisor,
                    monto=monto,
                )
                emisor.saldo -= monto
                emisor.save()

                Movimiento.objects.create(
                    tipo='ingreso',
                    cuenta=receptor,
                    monto=monto,
                )
                receptor.saldo += monto
                receptor.save()

                # 5. Devolver la respuesta
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ocurrió un error inesperado al realizar la transferencia: ' + str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

