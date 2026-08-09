# Gerado por robot_rest a partir do esquema do banco.
# Reescrito a cada execucao: coloque customizacoes em outro modulo.
from rest_framework import serializers

from .models import (
    AlbumTrack,
    Artist,
)


class AlbumTrackSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlbumTrack
        fields = "__all__"


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = "__all__"

