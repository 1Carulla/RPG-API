import json

from django.db.models import Count, Max
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Campanha, Personagem

CAMPOS_OBRIGATORIOS = ["nome", "classe", "nivel", "pontos_vida_max"]

# Valor mínimo de cada campo numérico (nenhum aceita número negativo)
MINIMOS = {
    "nivel": 1,
    "pontos_vida_max": 1,
    "pontos_vida_atual": 0,
    "iniciativa": 0,
    "ordem": 0,
}


# ---------- Funções auxiliares ----------

def erro(mensagem, status=400):
    return JsonResponse({"erro": mensagem}, status=status)


def ler_json(request):
    """Devolve (dados, None) ou (None, resposta de erro)."""
    try:
        dados = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, erro("JSON inválido.")
    if not isinstance(dados, dict):
        return None, erro("JSON inválido.")
    return dados, None


def e_inteiro(valor):
    # bool é subclasse de int no Python, então precisa ser excluído à parte
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_numeros(dados):
    """Devolve uma mensagem de erro se algum campo numérico for inválido."""
    for campo, minimo in MINIMOS.items():
        if campo not in dados:
            continue
        valor = dados[campo]
        if campo == "iniciativa" and valor is None:
            continue  # iniciativa vazia = fora de combate
        if not e_inteiro(valor):
            return f"O campo {campo} deve ser um número inteiro."
        if valor < minimo:
            return f"O campo {campo} não pode ser menor que {minimo}."
    return None


def validar_textos(dados, campos):
    """Os campos de texto enviados não podem ser vazios."""
    for campo in campos:
        if campo not in dados:
            continue
        valor = dados[campo]
        if not isinstance(valor, str) or not valor.strip():
            return f"O campo {campo} não pode ficar vazio."
    return None


def buscar_campanha(valor):
    """Converte o id enviado em uma Campanha. Devolve (campanha, mensagem_erro)."""
    if valor is None or valor == "":
        return None, None
    if not e_inteiro(valor):
        return None, "O campo campanha deve ser o id de uma campanha."
    try:
        return Campanha.objects.get(id=valor), None
    except Campanha.DoesNotExist:
        return None, "Campanha não encontrada."


def personagem_para_dict(personagem):
    return {
        "id": personagem.id,
        "nome": personagem.nome,
        "classe": personagem.classe,
        "nivel": personagem.nivel,
        "pontos_vida_atual": personagem.pontos_vida_atual,
        "pontos_vida_max": personagem.pontos_vida_max,
        "vivo": personagem.vivo,
        "iniciativa": personagem.iniciativa,
        "ordem": personagem.ordem,
        "campanha": personagem.campanha_id,
        "campanha_nome": personagem.campanha.nome if personagem.campanha else None,
    }


def campanha_para_dict(campanha, total=None):
    if total is None:
        total = campanha.personagens.count()
    return {
        "id": campanha.id,
        "nome": campanha.nome,
        "descricao": campanha.descricao,
        "total_personagens": total,
    }


# ---------- Personagens ----------

@csrf_exempt
def personagens(request):
    if request.method == "GET":
        consulta = Personagem.objects.select_related("campanha").order_by("ordem", "id")

        # Filtro opcional: /api/personagens/?campanha=1 ou ?campanha=nenhuma
        filtro = request.GET.get("campanha")
        if filtro == "nenhuma":
            consulta = consulta.filter(campanha__isnull=True)
        elif filtro:
            if not filtro.isdigit():
                return erro("O filtro campanha deve ser um id ou 'nenhuma'.")
            consulta = consulta.filter(campanha_id=int(filtro))

        lista = []
        for personagem in consulta:
            lista.append(personagem_para_dict(personagem))
        return JsonResponse({"personagens": lista})

    if request.method == "POST":
        dados, resposta_erro = ler_json(request)
        if resposta_erro:
            return resposta_erro

        for campo in CAMPOS_OBRIGATORIOS:
            # 0 não é "faltando"; só None e texto vazio contam
            valor = dados.get(campo)
            if valor is None or (isinstance(valor, str) and not valor.strip()):
                return erro(f"O campo {campo} é obrigatório.")

        mensagem = validar_textos(dados, ["nome", "classe"]) or validar_numeros(dados)
        if mensagem:
            return erro(mensagem)

        pv_max = dados["pontos_vida_max"]
        pv_atual = dados.get("pontos_vida_atual")
        if pv_atual is None:
            pv_atual = pv_max  # personagem novo começa com a vida cheia
        if pv_atual > pv_max:
            return erro("Os pontos de vida atuais não podem passar dos máximos.")

        vivo = dados.get("vivo", True)
        if not isinstance(vivo, bool):
            return erro("O campo vivo deve ser true ou false.")

        campanha, mensagem = buscar_campanha(dados.get("campanha"))
        if mensagem:
            return erro(mensagem)

        # Personagem novo vai para o fim da lista
        ultima = Personagem.objects.aggregate(Max("ordem"))["ordem__max"] or 0

        personagem = Personagem.objects.create(
            nome=dados["nome"].strip(),
            classe=dados["classe"].strip(),
            nivel=dados["nivel"],
            pontos_vida_max=pv_max,
            pontos_vida_atual=pv_atual,
            vivo=vivo,
            iniciativa=dados.get("iniciativa"),
            ordem=ultima + 1,
            campanha=campanha,
        )
        return JsonResponse(personagem_para_dict(personagem), status=201)

    return erro("Método não permitido.", 405)


@csrf_exempt
def personagem_detalhe(request, id):
    try:
        personagem = Personagem.objects.select_related("campanha").get(id=id)
    except Personagem.DoesNotExist:
        return erro("Personagem não encontrado.", 404)

    if request.method == "GET":
        return JsonResponse(personagem_para_dict(personagem))

    if request.method == "PUT":
        dados, resposta_erro = ler_json(request)
        if resposta_erro:
            return resposta_erro

        mensagem = validar_textos(dados, ["nome", "classe"]) or validar_numeros(dados)
        if mensagem:
            return erro(mensagem)

        if "vivo" in dados and not isinstance(dados["vivo"], bool):
            return erro("O campo vivo deve ser true ou false.")

        novo_max = dados.get("pontos_vida_max", personagem.pontos_vida_max)
        novo_atual = dados.get("pontos_vida_atual", personagem.pontos_vida_atual)
        if "pontos_vida_atual" in dados and novo_atual > novo_max:
            return erro("Os pontos de vida atuais não podem passar dos máximos.")
        # Se só o máximo diminuiu, a vida atual acompanha
        novo_atual = min(novo_atual, novo_max)

        if "campanha" in dados:
            campanha, mensagem = buscar_campanha(dados["campanha"])
            if mensagem:
                return erro(mensagem)
            personagem.campanha = campanha

        if "nome" in dados:
            personagem.nome = dados["nome"].strip()
        if "classe" in dados:
            personagem.classe = dados["classe"].strip()
        personagem.nivel = dados.get("nivel", personagem.nivel)
        personagem.pontos_vida_max = novo_max
        personagem.pontos_vida_atual = novo_atual
        personagem.vivo = dados.get("vivo", personagem.vivo)
        personagem.iniciativa = dados.get("iniciativa", personagem.iniciativa)
        personagem.ordem = dados.get("ordem", personagem.ordem)
        personagem.save()
        return JsonResponse(personagem_para_dict(personagem))

    if request.method == "DELETE":
        # Só o mestre (usuário do admin) pode apagar um personagem de vez
        if not request.user.is_staff:
            return erro(
                "Apenas o mestre (admin) pode excluir personagens. "
                "Entre em /admin/ primeiro.",
                403,
            )
        personagem.delete()
        return HttpResponse(status=204)

    return erro("Método não permitido.", 405)


# ---------- Campanhas ----------

@csrf_exempt
def campanhas(request):
    if request.method == "GET":
        lista = []
        consulta = Campanha.objects.annotate(total=Count("personagens")).order_by("nome")
        for campanha in consulta:
            lista.append(campanha_para_dict(campanha, campanha.total))
        return JsonResponse({"campanhas": lista})

    if request.method == "POST":
        dados, resposta_erro = ler_json(request)
        if resposta_erro:
            return resposta_erro

        nome = dados.get("nome")
        if not isinstance(nome, str) or not nome.strip():
            return erro("O campo nome é obrigatório.")
        descricao = dados.get("descricao") or ""
        if not isinstance(descricao, str):
            return erro("O campo descricao deve ser um texto.")

        campanha = Campanha.objects.create(nome=nome.strip(), descricao=descricao.strip())
        return JsonResponse(campanha_para_dict(campanha, 0), status=201)

    return erro("Método não permitido.", 405)


@csrf_exempt
def campanha_detalhe(request, id):
    try:
        campanha = Campanha.objects.get(id=id)
    except Campanha.DoesNotExist:
        return erro("Campanha não encontrada.", 404)

    if request.method == "GET":
        return JsonResponse(campanha_para_dict(campanha))

    if request.method == "PUT":
        dados, resposta_erro = ler_json(request)
        if resposta_erro:
            return resposta_erro

        mensagem = validar_textos(dados, ["nome"])
        if mensagem:
            return erro(mensagem)
        if "descricao" in dados and not isinstance(dados["descricao"], str):
            return erro("O campo descricao deve ser um texto.")

        if "nome" in dados:
            campanha.nome = dados["nome"].strip()
        if "descricao" in dados:
            campanha.descricao = dados["descricao"].strip()
        campanha.save()
        return JsonResponse(campanha_para_dict(campanha))

    if request.method == "DELETE":
        if not request.user.is_staff:
            return erro(
                "Apenas o mestre (admin) pode excluir campanhas. "
                "Entre em /admin/ primeiro.",
                403,
            )
        # Os personagens não são apagados: ficam sem campanha
        campanha.delete()
        return HttpResponse(status=204)

    return erro("Método não permitido.", 405)


# ---------- Página ----------

def pagina(request):
    return render(request, "personagens/index.html", {"mestre": request.user.is_staff})
