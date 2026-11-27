# API de Personagens de RPG de Mesa

Projeto da disciplina Programação para Internet (UENP). Uma API em Django para cadastrar os personagens de uma mesa de RPG, e uma página web que consome essa API com `fetch`.

Cada personagem tem: `nome`, `classe`, `nivel`, `pontos_vida` e `vivo`.

## Como rodar

Requisito: Python 3.12 ou mais novo (testado com Python 3.13 e Django 6.1).

1. python -m venv venv
2. venv\Scripts\activate  (Linux/macOS: `source venv/bin/activate`)
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py loaddata dados.json
6. python manage.py runserver

Depois acesse http://127.0.0.1:8000/ (página) ou http://127.0.0.1:8000/api/personagens/ (API).

Observação: se o PowerShell bloquear o `venv\Scripts\activate`, rode antes `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` (vale só para aquele terminal).

## Estrutura do projeto

- `config/`: configurações do projeto Django (`settings.py`, `urls.py`)
- `personagens/`: app da API
  - `models.py`: model `Personagem`
  - `admin.py`: registro do model no admin
  - `views.py`: views da API (JSON) e da página
  - `urls.py`: rotas `/`, `/api/personagens/` e `/api/personagens/<id>/`
  - `templates/personagens/index.html`: página que consome a API com `fetch`
- `dados.json`: registros de teste (gerados no formato do `dumpdata`)

## Página

A página em http://127.0.0.1:8000/ usa a API sem recarregar:

- lista os personagens do grupo;
- cadastra um personagem pelo formulário (se faltar algum campo, mostra a mensagem de erro da API);
- altera um personagem: botão **Derrotar/Reviver** (campo `vivo`) e botão **Subir de nível** (campo `nivel`);
- exclui um personagem.

## Admin

Endereço: http://127.0.0.1:8000/admin/

Usuário: admin
Senha: rpg12345

## Dados de teste

Os registros de teste (4 personagens e o usuário admin) estão no arquivo `dados.json`, gerado no formato do `dumpdata`. Eles são carregados pelo comando `python manage.py loaddata dados.json` (passo 5 acima). O arquivo `db.sqlite3` **não** foi enviado ao repositório.

## Rotas da API

| Método | URL                        | Descrição                  | Respostas     |
|--------|----------------------------|----------------------------|---------------|
| GET    | `/api/personagens/`          | Lista os personagens       | 200           |
| POST   | `/api/personagens/`          | Cadastra um personagem     | 201, 400      |
| GET    | `/api/personagens/<id>/`     | Busca um personagem        | 200, 404      |
| PUT    | `/api/personagens/<id>/`     | Altera um personagem       | 200, 400, 404 |
| DELETE | `/api/personagens/<id>/`     | Exclui um personagem       | 204, 404      |

Exemplo de corpo para o POST (`nome`, `classe`, `nivel` e `pontos_vida` são obrigatórios; `nivel` e `pontos_vida` devem ser inteiros):

```json
{"nome": "Elara", "classe": "Maga", "nivel": 4, "pontos_vida": 24}
```

No PUT, basta enviar os campos que se quer mudar, por exemplo `{"vivo": false}`.
