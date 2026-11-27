import json

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Campanha, Personagem

JSON = "application/json"


class ApiPersonagensTest(TestCase):
    def setUp(self):
        self.campanha = Campanha.objects.create(nome="A Mina Perdida")
        self.p = Personagem.objects.create(
            nome="Elara", classe="Maga", nivel=4,
            pontos_vida_max=24, pontos_vida_atual=20, campanha=self.campanha, ordem=1,
        )

    def post(self, url, dados):
        return self.client.post(url, json.dumps(dados), content_type=JSON)

    def put(self, url, dados):
        return self.client.put(url, json.dumps(dados), content_type=JSON)

    # GET
    def test_lista(self):
        r = self.client.get("/api/personagens/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["personagens"][0]["pontos_vida_atual"], 20)

    def test_filtro_campanha(self):
        Personagem.objects.create(nome="X", classe="Y", nivel=1, pontos_vida_max=5, pontos_vida_atual=5)
        r = self.client.get(f"/api/personagens/?campanha={self.campanha.id}")
        self.assertEqual(len(r.json()["personagens"]), 1)
        r = self.client.get("/api/personagens/?campanha=nenhuma")
        self.assertEqual(r.json()["personagens"][0]["nome"], "X")

    def test_busca_e_404(self):
        self.assertEqual(self.client.get(f"/api/personagens/{self.p.id}/").status_code, 200)
        r = self.client.get("/api/personagens/999/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("erro", r.json())

    # POST
    def test_cadastro(self):
        r = self.post("/api/personagens/", {
            "nome": "Grom", "classe": "Bárbaro", "nivel": 3,
            "pontos_vida_max": 35, "campanha": self.campanha.id,
        })
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["pontos_vida_atual"], 35)  # começa com vida cheia
        self.assertEqual(r.json()["campanha_nome"], "A Mina Perdida")

    def test_cadastro_sem_campo(self):
        r = self.post("/api/personagens/", {"nome": "", "classe": "X", "nivel": 1, "pontos_vida_max": 5})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["erro"], "O campo nome é obrigatório.")

    def test_cadastro_negativo(self):
        for campo in ["nivel", "pontos_vida_max"]:
            dados = {"nome": "A", "classe": "B", "nivel": 1, "pontos_vida_max": 5}
            dados[campo] = -3
            self.assertEqual(self.post("/api/personagens/", dados).status_code, 400)

    def test_cadastro_json_invalido(self):
        r = self.client.post("/api/personagens/", "{x", content_type=JSON)
        self.assertEqual(r.status_code, 400)

    # PUT
    def test_altera_pv(self):
        r = self.put(f"/api/personagens/{self.p.id}/", {"pontos_vida_atual": 10, "pontos_vida_max": 30})
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["pontos_vida_atual"], r.json()["pontos_vida_max"]), (10, 30))

    def test_pv_atual_nao_passa_do_maximo(self):
        r = self.put(f"/api/personagens/{self.p.id}/", {"pontos_vida_atual": 99})
        self.assertEqual(r.status_code, 400)

    def test_diminuir_maximo_ajusta_atual(self):
        r = self.put(f"/api/personagens/{self.p.id}/", {"pontos_vida_max": 10})
        self.assertEqual(r.json()["pontos_vida_atual"], 10)

    def test_put_negativos(self):
        for campo in ["nivel", "pontos_vida_max", "pontos_vida_atual", "iniciativa", "ordem"]:
            r = self.put(f"/api/personagens/{self.p.id}/", {campo: -1})
            self.assertEqual(r.status_code, 400, campo)

    def test_iniciativa_e_limpar(self):
        r = self.put(f"/api/personagens/{self.p.id}/", {"iniciativa": 17})
        self.assertEqual(r.json()["iniciativa"], 17)
        r = self.put(f"/api/personagens/{self.p.id}/", {"iniciativa": None})
        self.assertIsNone(r.json()["iniciativa"])

    def test_tirar_da_campanha(self):
        r = self.put(f"/api/personagens/{self.p.id}/", {"campanha": None})
        self.assertIsNone(r.json()["campanha"])

    def test_put_404(self):
        self.assertEqual(self.put("/api/personagens/999/", {"vivo": False}).status_code, 404)

    # DELETE
    def test_delete_sem_login_403(self):
        r = self.client.delete(f"/api/personagens/{self.p.id}/")
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Personagem.objects.filter(id=self.p.id).exists())

    def test_delete_admin(self):
        User.objects.create_superuser("mestre", password="senha-teste-123")
        self.client.login(username="mestre", password="senha-teste-123")
        self.assertEqual(self.client.delete(f"/api/personagens/{self.p.id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/personagens/{self.p.id}/").status_code, 404)

    def test_delete_inexistente_404_mesmo_sem_login(self):
        self.assertEqual(self.client.delete("/api/personagens/999/").status_code, 404)

    def test_metodo_nao_permitido(self):
        self.assertEqual(self.client.delete("/api/personagens/").status_code, 405)


class ApiCampanhasTest(TestCase):
    def test_crud_campanha(self):
        r = self.client.post("/api/campanhas/", json.dumps({"nome": "Brumas"}), content_type=JSON)
        self.assertEqual(r.status_code, 201)
        cid = r.json()["id"]
        self.assertEqual(self.client.get("/api/campanhas/").json()["campanhas"][0]["nome"], "Brumas")
        r = self.client.put(f"/api/campanhas/{cid}/", json.dumps({"descricao": "Névoa"}), content_type=JSON)
        self.assertEqual(r.json()["descricao"], "Névoa")
        self.assertEqual(self.client.delete(f"/api/campanhas/{cid}/").status_code, 403)

    def test_campanha_sem_nome(self):
        r = self.client.post("/api/campanhas/", json.dumps({"nome": " "}), content_type=JSON)
        self.assertEqual(r.status_code, 400)

    def test_excluir_campanha_mantem_personagens(self):
        c = Campanha.objects.create(nome="C")
        p = Personagem.objects.create(nome="A", classe="B", nivel=1, pontos_vida_max=5, pontos_vida_atual=5, campanha=c)
        User.objects.create_superuser("mestre", password="senha-teste-123")
        self.client.login(username="mestre", password="senha-teste-123")
        self.assertEqual(self.client.delete(f"/api/campanhas/{c.id}/").status_code, 204)
        p.refresh_from_db()
        self.assertIsNone(p.campanha)


class PaginaTest(TestCase):
    def test_jogador_nao_ve_excluir(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'data-mestre="0"')
        self.assertContains(r, "Entrar como mestre")

    def test_mestre(self):
        User.objects.create_superuser("mestre", password="senha-teste-123")
        self.client.login(username="mestre", password="senha-teste-123")
        self.assertContains(self.client.get("/"), 'data-mestre="1"')
