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
    emisor = (CuentaSerializer(read_only=True))
    receptor = CuentaSerializer(read_only=True)
    emisor_id = serializers.PrimaryKeyRelatedField(
        queryset=Cuenta.objects.all(),
        source='emisor',
        write_only=True,
        required=True
    )
    receptor_id = serializers.PrimaryKeyRelatedField(
        queryset=Cuenta.objects.all(),
        source='receptor',
        write_only=True,
        required=True
    )

    class Meta:
        model = Transferencia
        fields = '__all__'


class TransferenciaViewSet(viewsets.ModelViewSet):
    queryset = Transferencia.objects.all()
    serializer_class = TransferenciaSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        emisor_id = serializer.validated_data['emisor'].id
        receptor_id = serializer.validated_data['receptor'].id
        monto_str = serializer.validated_data['monto']

        try:
            monto = Decimal(monto_str)
        except (TypeError, ValueError):
            return Response({'error': 'El monto debe ser un número válido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                emisor = Cuenta.objects.select_for_update().get(id=emisor_id)
                receptor = Cuenta.objects.select_for_update().get(id=receptor_id)

                if emisor.usuario != request.user:
                    raise serializers.ValidationError(
                        "No tienes permiso para realizar esta transferencia desde esta cuenta.")


                if emisor.saldo < monto:
                    raise serializers.ValidationError("Saldo insuficiente para la transferencia.")


                transferencia = Transferencia.objects.create(
                    emisor=emisor,
                    receptor=receptor,
                    monto=monto,
                )


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

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Ocurrió un error inesperado al realizar la transferencia: ' + str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

