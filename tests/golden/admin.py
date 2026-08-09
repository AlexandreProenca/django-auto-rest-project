# Gerado por robot_rest a partir do esquema do banco.
# Reescrito a cada execucao: coloque customizacoes em outro modulo.
from django.contrib import admin

from .models import (
    AlbumTrack,
    Artist,
)


@admin.register(AlbumTrack)
class AlbumTrackAdmin(admin.ModelAdmin):
    pass


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    pass

