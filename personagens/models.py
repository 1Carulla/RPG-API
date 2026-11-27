from django.db import models


class Personagem(models.Model):
    nome = models.CharField(max_length=100)
    classe = models.CharField(max_length=50)
    nivel = models.IntegerField()
    pontos_vida = models.IntegerField()
    vivo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "personagem"
        verbose_name_plural = "personagens"

    def __str__(self):
        return f"{self.nome} ({self.classe}, nível {self.nivel})"
