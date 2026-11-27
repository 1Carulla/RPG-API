import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Personagem

CAMPOS_OBRIGATORIOS = ["nome", "classe", "nivel", "pontos_vida"]


def personagem_para_dict(personagem):
    return {
        "id": personagem.id,
        "nome": personagem.nome,
        "classe": personagem.classe,
        "nivel": personagem.nivel,
        "pontos_vida": personagem.pontos_vida,
        "vivo": personagem.vivo,
    }


def e_inteiro(valor):
    # bool é subclasse de int no Python, então precisa ser excluído à parte
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_numeros(dados):
    """Devolve uma mensagem de erro se nivel/pontos_vida não forem inteiros."""
    for campo in ["nivel", "pontos_vida"]:
        if campo in dados and not e_inteiro(dados[campo]):
            return f"O campo {campo} deve ser um número inteiro."
    return None


@csrf_exempt
def personagens(request):
    if request.method == "GET":
        lista = []
        for personagem in Personagem.objects.all().order_by("nome"):
            lista.append(personagem_para_dict(personagem))
        return JsonResponse({"personagens": lista})

    if request.method == "POST":
        try:
            dados = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"erro": "JSON inválido."}, status=400)

        if not isinstance(dados, dict):
            return JsonResponse({"erro": "JSON inválido."}, status=400)

        for campo in CAMPOS_OBRIGATORIOS:
            # 0 é um valor válido (ex.: 0 pontos de vida), então só
            # None e texto vazio contam como "faltando"
            if dados.get(campo) in (None, ""):
                return JsonResponse(
                    {"erro": f"O campo {campo} é obrigatório."}, status=400
                )

        erro = validar_numeros(dados)
        if erro:
            return JsonResponse({"erro": erro}, status=400)

        personagem = Personagem.objects.create(
            nome=dados["nome"],
            classe=dados["classe"],
            nivel=dados["nivel"],
            pontos_vida=dados["pontos_vida"],
        )
        return JsonResponse(personagem_para_dict(personagem), status=201)

    return JsonResponse({"erro": "Método não permitido."}, status=405)


@csrf_exempt
def personagem_detalhe(request, id):
    try:
        personagem = Personagem.objects.get(id=id)
    except Personagem.DoesNotExist:
        return JsonResponse({"erro": "Personagem não encontrado."}, status=404)

    if request.method == "GET":
        return JsonResponse(personagem_para_dict(personagem))

    if request.method == "PUT":
        try:
            dados = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"erro": "JSON inválido."}, status=400)

        if not isinstance(dados, dict):
            return JsonResponse({"erro": "JSON inválido."}, status=400)

        for campo in ["nome", "classe"]:
            if campo in dados and dados[campo] in (None, ""):
                return JsonResponse(
                    {"erro": f"O campo {campo} não pode ficar vazio."}, status=400
                )

        erro = validar_numeros(dados)
        if erro:
            return JsonResponse({"erro": erro}, status=400)

        if "vivo" in dados and not isinstance(dados["vivo"], bool):
            return JsonResponse(
                {"erro": "O campo vivo deve ser true ou false."}, status=400
            )

        personagem.nome = dados.get("nome", personagem.nome)
        personagem.classe = dados.get("classe", personagem.classe)
        personagem.nivel = dados.get("nivel", personagem.nivel)
        personagem.pontos_vida = dados.get("pontos_vida", personagem.pontos_vida)
        personagem.vivo = dados.get("vivo", personagem.vivo)
        personagem.save()
        return JsonResponse(personagem_para_dict(personagem))

    if request.method == "DELETE":
        personagem.delete()
        return HttpResponse(status=204)

    return JsonResponse({"erro": "Método não permitido."}, status=405)


def pagina(request):
    return render(request, "personagens/index.html")
