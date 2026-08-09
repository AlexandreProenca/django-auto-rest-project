# Gerado por robot_rest a partir do esquema do banco.
# Reescrito a cada execucao: coloque customizacoes em outro modulo.
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
]
