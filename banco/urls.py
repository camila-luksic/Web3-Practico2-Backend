from django.urls import path, include
from rest_framework import routers


from banco.apis import CuentaViewSet, BeneficiarioViewSet, MovimientoViewSet, UserViewSet, TransferenciaViewSet

router = routers.DefaultRouter()
router.register('cuentas', CuentaViewSet)
router.register('beneficiarios', BeneficiarioViewSet)
router.register('movimientos', MovimientoViewSet)
router.register('transferencias', TransferenciaViewSet)
router.register("auth", UserViewSet, basename='auth')
urlpatterns = [
    path('api/', include(router.urls)),
]