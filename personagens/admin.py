from django.contrib import admin

from .models import Personagem


@admin.register(Personagem)
class PersonagemAdmin(admin.ModelAdmin):
    list_display = ("nome", "classe", "nivel", "pontos_vida", "vivo")
    list_filter = ("classe", "vivo")
    search_fields = ("nome", "classe")
