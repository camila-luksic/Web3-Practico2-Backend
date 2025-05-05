from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from banco.apis import UserSerializer, CuentaSerializer
from banco.models import Beneficiario
from banco.models.cuenta import Cuenta


class BeneficiarioSerializer(serializers.ModelSerializer):
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='usuario',
        write_only=True
    )
    usuario = UserSerializer(
        read_only=True,
        many=False
    )

    cuenta_beneficiaria_id = serializers.PrimaryKeyRelatedField(
        queryset=Cuenta.objects.all(),
        source='cuenta_beneficiaria',
        write_only=True,
        required=True
    )
    cuenta_beneficiaria = CuentaSerializer(
        read_only=True,
        many=False
    )

    cuenta_propia_id = serializers.CharField(
        write_only=True,
        required=True
    )
    cuenta_propia = CuentaSerializer(
        read_only=True,
        many=False
    )

    class Meta:
        model = Beneficiario
        fields = '__all__'

    def validate(self, data):
        cuenta_beneficiaria_id = self.initial_data.get('cuenta_beneficiaria_id')

        cuenta_propia_nro = data.get('cuenta_propia_id')

        print(f"Validando - cuenta_beneficiaria_id: {cuenta_beneficiaria_id}, cuenta_propia_nro: {cuenta_propia_nro}")

        cuenta_beneficiaria = None
        if cuenta_beneficiaria_id:
            try:
                cuenta_beneficiaria = Cuenta.objects.get(id=cuenta_beneficiaria_id)
                data['cuenta_beneficiaria'] = cuenta_beneficiaria
                print(f"Validación - Cuenta beneficiaria encontrada: {cuenta_beneficiaria}")
            except Cuenta.DoesNotExist:
                raise ValidationError({'cuenta_beneficiaria_id': ['Cuenta beneficiaria inválida.']})

        cuenta_propia = None
        if cuenta_propia_nro:
            try:
                cuenta_propia = Cuenta.objects.get(nroCuenta=cuenta_propia_nro)
                data['cuenta_propia'] = cuenta_propia
                print(f"Validación - Cuenta propia encontrada: {cuenta_propia}")
            except Cuenta.DoesNotExist:
                raise ValidationError({'cuenta_propia_id': ['No existe una cuenta con este número.']})
        else:
            raise ValidationError({'cuenta_propia_id': ['Este campo es requerido.']})

        print(f"Validación - Data después de validación: {data}")
        return data

    def create(self, validated_data):
        print(f"Creando beneficiario con data validada: {validated_data}")
        usuario = validated_data.pop('usuario')
        cuenta_beneficiaria = validated_data.pop('cuenta_beneficiaria')
        cuenta_propia = validated_data.pop('cuenta_propia')

        print(f"Creando beneficiario con cuenta_beneficiaria: {cuenta_beneficiaria}, cuenta_propia: {cuenta_propia}")
        print(f"cuenta_beneficiaria ID: {cuenta_beneficiaria.id if hasattr(cuenta_beneficiaria, 'id') else None}")
        print(f"cuenta_propia ID: {cuenta_propia.id if hasattr(cuenta_propia, 'id') else None}")

        beneficiario = Beneficiario.objects.create(
            nombreCompleto=validated_data['nombreCompleto'],
            usuario=usuario,
            cuenta_beneficiaria=cuenta_beneficiaria,
            cuenta_propia=cuenta_propia,
        )
        return beneficiario




class BeneficiarioViewSet(viewsets.ModelViewSet):
    queryset = Beneficiario.objects.all()
    serializer_class = BeneficiarioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        print("Usuario autenticado:")
        print(self.request.user)
        print("Consulta a la base de datos:")
        print(Beneficiario.objects.filter(usuario=self.request.user).query)

        user = self.request.user
        return Beneficiario.objects.filter(usuario=user)



    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


