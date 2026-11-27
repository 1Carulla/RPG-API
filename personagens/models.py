from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Campanha(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = "campanha"
        verbose_name_plural = "campanhas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Personagem(models.Model):
    nome = models.CharField(max_length=100)
    classe = models.CharField(max_length=50)
    nivel = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    pontos_vida_max = models.PositiveIntegerField(
        "pontos de vida máximos", validators=[MinValueValidator(1)]
    )
    pontos_vida_atual = models.PositiveIntegerField("pontos de vida atuais")
    vivo = models.BooleanField(default=True)
    # Anotação temporária de combate: fica vazia fora do combate
    iniciativa = models.PositiveIntegerField(null=True, blank=True)
    # Posição do personagem na lista (menor aparece primeiro)
    ordem = models.PositiveIntegerField(default=0)
    campanha = models.ForeignKey(
        Campanha,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="personagens",
    )

    class Meta:
        verbose_name = "personagem"
        verbose_name_plural = "personagens"
        ordering = ["ordem", "id"]

    def clean(self):
        # Usado pelo admin: os PV atuais não podem passar dos máximos
        if (
            self.pontos_vida_atual is not None
            and self.pontos_vida_max is not None
            and self.pontos_vida_atual > self.pontos_vida_max
        ):
            raise ValidationError(
                {"pontos_vida_atual": "Não pode ser maior que os pontos de vida máximos."}
            )

    def __str__(self):
        return f"{self.nome} ({self.classe}, nível {self.nivel})"
