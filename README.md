# API de Personagens de RPG de Mesa

Projeto da disciplina Programação para Internet (UENP). Uma API em Django para registrar os personagens de mesas de RPG, separados por campanha, e uma página web com tema de taverna medieval que consome essa API com `fetch`.

Cada **personagem** tem: `nome`, `classe`, `nivel`, `pontos_vida_atual`, `pontos_vida_max`, `vivo`, `iniciativa`, `ordem` e `campanha`.
Cada **campanha** (grupo de aventureiros) tem: `nome` e `descricao`.

## Como rodar

Requisito: Python 3.12 ou mais novo (testado com Python 3.13 e Django 6.1).

1. python -m venv venv
2. venv\Scripts\activate  (Linux/macOS: `source venv/bin/activate`)
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py loaddata dados.json
6. python manage.py runserver

Depois acesse http://127.0.0.1:8000/ (página) ou http://127.0.0.1:8000/api/personagens/ (API).

Observação: se o PowerShell bloquear o `venv\Scripts\activate`, rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

Testes automáticos: `python manage.py test personagens`

## Admin

Endereço: http://127.0.0.1:8000/admin/

Usuário: admin
Senha: rpg12345

O admin é o **mestre** da mesa: só ele pode excluir personagens e campanhas (veja abaixo).

## Dados de teste

Os registros de teste (2 campanhas, 7 personagens e o usuário admin) estão no arquivo `dados.json`, gerado no formato do `dumpdata`. Eles são carregados pelo comando `python manage.py loaddata dados.json` (passo 5 acima). O arquivo `db.sqlite3` **não** foi enviado ao repositório.

## Rotas da API

### Personagens

| Método | URL                          | Descrição                  | Respostas          |
|--------|------------------------------|----------------------------|--------------------|
| GET    | `/api/personagens/`          | Lista os personagens       | 200                |
| POST   | `/api/personagens/`          | Cadastra um personagem     | 201, 400           |
| GET    | `/api/personagens/<id>/`     | Busca um personagem        | 200, 404           |
| PUT    | `/api/personagens/<id>/`     | Altera um personagem       | 200, 400, 404      |
| DELETE | `/api/personagens/<id>/`     | Exclui um personagem       | 204, 403, 404      |

### Campanhas

| Método | URL                          | Descrição                  | Respostas          |
|--------|------------------------------|----------------------------|--------------------|
| GET    | `/api/campanhas/`            | Lista as campanhas         | 200                |
| POST   | `/api/campanhas/`            | Cadastra uma campanha      | 201, 400           |
| GET    | `/api/campanhas/<id>/`       | Busca uma campanha         | 200, 404           |
| PUT    | `/api/campanhas/<id>/`       | Altera uma campanha        | 200, 400, 404      |
| DELETE | `/api/campanhas/<id>/`       | Exclui uma campanha        | 204, 403, 404      |

### Detalhes

- **Filtro por campanha:** `/api/personagens/?campanha=1` lista só os personagens da campanha 1; `?campanha=nenhuma` lista os que não estão em nenhuma.
- **POST de personagem:** `nome`, `classe`, `nivel` e `pontos_vida_max` são obrigatórios. `pontos_vida_atual` é opcional (se não vier, o personagem começa com a vida cheia) e `campanha` é o id de uma campanha (opcional).

  ```json
  {"nome": "Elara", "classe": "Maga", "nivel": 4, "pontos_vida_max": 24, "campanha": 1}
  ```
- **PUT:** basta enviar os campos que se quer mudar, por exemplo `{"pontos_vida_atual": 10}`, `{"vivo": false}` ou `{"iniciativa": 17}`. Para tirar a iniciativa ou a campanha, envie `null`.
- **Sem números negativos:** `nivel` e `pontos_vida_max` precisam ser pelo menos 1; `pontos_vida_atual`, `iniciativa` e `ordem` pelo menos 0. Os PV atuais não podem passar dos máximos. Qualquer valor fora disso devolve **400** com a mensagem de erro.
- **DELETE só para o mestre:** quem não está logado como admin recebe **403** com mensagem em JSON. Para testar o DELETE pelo console do navegador, entre antes em http://127.0.0.1:8000/admin/ com o usuário acima (o `fetch` envia o login junto automaticamente). Um id que não existe devolve **404** para qualquer pessoa. Excluir uma campanha não apaga os personagens: eles ficam sem campanha.

## Página

A página em http://127.0.0.1:8000/ usa a API sem recarregar:

- **lista** os personagens em fichas, com abas para filtrar por campanha;
- **cadastra** personagens e campanhas por formulários (se faltar algum campo, mostra a mensagem de erro da API);
- **altera** os personagens:
  - pontos de vida no formato `atual/máximo` (ex.: 31/38), com barra de vida, botões **−** e **+** e campos editáveis;
  - **+ PV máx** e **+ Nível**;
  - **Derrotar/Reviver**;
  - campanha do personagem;
  - setas **◀ ▶** para mudar a ordem do grupo;
  - **iniciativa** de combate: anote o valor de cada um e clique em **Ordenar por iniciativa**; **Encerrar combate** apaga as iniciativas;
- **exclui** personagens e campanhas, apenas quando o mestre está logado (botão **Entrar como mestre** no topo). Jogadores não veem o botão de excluir.

## Estrutura do projeto

- `config/`: configurações do projeto Django (`settings.py`, `urls.py`)
- `personagens/`: app da API
  - `models.py`: models `Campanha` e `Personagem`
  - `admin.py`: registro dos models no admin
  - `views.py`: views da API (JSON) e da página
  - `urls.py`: rotas da página e da API
  - `tests.py`: testes automáticos da API e da página
  - `templates/personagens/index.html`: página que consome a API
  - `static/personagens/estilo.css`: visual da taverna
  - `static/personagens/app.js`: JavaScript com os `fetch`
- `dados.json`: registros de teste (gerados no formato do `dumpdata`)
