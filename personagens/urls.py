from django.urls import path

from . import views

urlpatterns = [
    path("", views.pagina),
    path("api/personagens/", views.personagens),
    path("api/personagens/<int:id>/", views.personagem_detalhe),
    path("api/campanhas/", views.campanhas),
    path("api/campanhas/<int:id>/", views.campanha_detalhe),
]
