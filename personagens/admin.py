from django.contrib import admin

from .models import Campanha, Personagem


class PersonagemInline(admin.TabularInline):
    model = Personagem
    fields = ("nome", "classe", "nivel", "pontos_vida_atual", "pontos_vida_max", "vivo", "ordem")
    extra = 0


@admin.register(Campanha)
class CampanhaAdmin(admin.ModelAdmin):
    list_display = ("nome", "total_personagens")
    search_fields = ("nome",)
    inlines = [PersonagemInline]

    @admin.display(description="personagens")
    def total_personagens(self, campanha):
        return campanha.personagens.count()


@admin.register(Personagem)
class PersonagemAdmin(admin.ModelAdmin):
    list_display = (
        "nome",
        "classe",
        "nivel",
        "pontos_vida",
        "vivo",
        "campanha",
        "iniciativa",
        "ordem",
    )
    list_filter = ("campanha", "classe", "vivo")
    search_fields = ("nome", "classe")

    @admin.display(description="PV")
    def pontos_vida(self, personagem):
        return f"{personagem.pontos_vida_atual}/{personagem.pontos_vida_max}"
