# Gerado por robot_rest a partir do esquema do banco.
# Reescrito a cada execucao: coloque customizacoes em outro modulo.
from rest_framework import viewsets

from .models import (
    AlbumTrack,
    Artist,
)
from .serializers import (
    AlbumTrackSerializer,
    ArtistSerializer,
)


class AlbumTrackViewSet(viewsets.ModelViewSet):
    # order_by explicito: paginar queryset sem ordenacao devolve paginas
    # inconsistentes (UnorderedObjectListWarning do DRF).
    queryset = AlbumTrack.objects.all().order_by("pk")
    serializer_class = AlbumTrackSerializer


class ArtistViewSet(viewsets.ModelViewSet):
    # order_by explicito: paginar queryset sem ordenacao devolve paginas
    # inconsistentes (UnorderedObjectListWarning do DRF).
    queryset = Artist.objects.all().order_by("pk")
    serializer_class = ArtistSerializer

