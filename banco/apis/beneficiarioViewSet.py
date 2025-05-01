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

    cuenta_beneficiaria_id = serializers.PrimaryKeyRelatedField(  # Nuevo campo para la cuenta beneficiaria
        queryset=Cuenta.objects.all(),
        source='cuenta_beneficiaria',
        write_only=True,
        required=True  # Asegúrate de que este campo sea requerido
    )
    cuenta_beneficiaria = CuentaSerializer(
        read_only=True,
        many=False
    )

    cuenta_propia_id = serializers.PrimaryKeyRelatedField(  # Nuevo campo para la cuenta propia
        queryset=Cuenta.objects.all(),
        source='cuenta_propia',
        write_only=True,
        required=True  # Asegúrate de que este campo sea requerido
    )
    cuenta_propia = CuentaSerializer(
        read_only=True,
        many=False
    )

    class Meta:
        model = Beneficiario
        fields = '__all__'


def validate(self, data):
    """
    Verifica que el usuario y las cuentas existan.  Ahora busca el usuario por nombreCompleto.
    """
    nombreCompleto = data.get('nombreCompleto')
    cuenta_beneficiaria_id = data.get('cuenta_beneficiaria')
    cuenta_propia_id = data.get('cuenta_propia')

    if not nombreCompleto:
        raise ValidationError({'nombreCompleto': ['Este campo es requerido.']})

    try:
        usuario = User.objects.get(username=nombreCompleto)  # Busca por username
        data['usuario'] = usuario  # Añade el usuario al validated_data
    except User.DoesNotExist:
        raise ValidationError({'nombreCompleto': ['No existe un usuario con este nombre.']})

    if cuenta_beneficiaria_id and not Cuenta.objects.filter(id=cuenta_beneficiaria_id.id).exists():
        raise ValidationError({'cuenta_beneficiaria_id': ['Cuenta beneficiaria inválida.']})

    if cuenta_propia_id and not Cuenta.objects.filter(id=cuenta_propia_id.id).exists():
        raise ValidationError({'cuenta_propia_id': ['Cuenta propia inválida.']})

    if cuenta_propia_id:
        try:
            cuenta_propia = Cuenta.objects.get(id=cuenta_propia_id.id)
            if cuenta_propia.usuario != usuario:
                raise ValidationError({'cuenta_propia_id': ['La cuenta propia no pertenece al usuario.']})
        except Cuenta.DoesNotExist:
            raise ValidationError({'cuenta_propia_id': ['Cuenta propia inválida.']})

    return data

    # Si todo está bien, devuelve los datos validados.
    return data


def create(self, validated_data):
    """
    Override create para manejar la creación del beneficiario.
    """
    usuario = validated_data.pop('usuario')
    cuenta_beneficiaria = validated_data.pop('cuenta_beneficiaria')
    cuenta_propia = validated_data.pop('cuenta_propia')

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
        """
        Devuelve todos los beneficiarios del usuario logueado.
        """
        print("Usuario autenticado:")
        print(self.request.user)
        print("Consulta a la base de datos:")
        print(Beneficiario.objects.filter(usuario=self.request.user).query)  # <-- Imprime la consulta SQL

        user = self.request.user
        return Beneficiario.objects.filter(usuario=user)

    # Aseguramos que solo usuarios autenticados puedan acceder

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)


