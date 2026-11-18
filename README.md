# Finanboard

Dashboard financeiro feito com Django e páginas HTML, CSS e JavaScript.
O cadastro e o login de usuários são reais. A página de investimentos consulta
preços de ações e fundos na BrAPI, sem exigir token. Os outros valores ainda
são exemplos e não representam os dados pessoais da conta.

## Rodar localmente

Requer Python 3.10 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abra <http://127.0.0.1:8000/> e crie uma conta ou entre com seu e-mail e senha.
Depois do login, você terá acesso ao dashboard. Também é possível abrir
`/login/login.html`, `/login/registro.html`, `/receitas.html`, `/despesas.html`
e `/investimentos.html`.

O projeto usa o arquivo `db.sqlite3` por padrão, então não precisa de um
servidor MySQL para iniciar.

Na página de investimentos, a lista da BrAPI traz preços de fechamento de
PETR4, VALE3, ITUB4, B3SA3, BOVA11 e HGLG11. A consulta é atualizada a cada
cinco minutos; o botão da página força uma nova consulta. Não precisa criar
conta nem configurar token. As cotações podem estar atrasadas e não são uma
oferta ou recomendação de investimento.

## Como o código está organizado

- `manage.py`: comando usado para iniciar o Django e executar tarefas do projeto.
- `config/`: configurações, URLs e pontos de entrada do servidor web.
- `model/`: modelos de dados e migrações do Django.
- `view/`: páginas HTML e arquivos estáticos em `assets/`.
- `database/`: cópia SQL relacionada ao banco MySQL original.
- `db.sqlite3`: banco SQLite usado localmente.

## O que os modelos representam

- `Usuario`: nome, e-mail e senha protegida por hash.
- `Receita`: descrição, categoria, valor e data de uma entrada de dinheiro.
- `Despesa`: descrição, categoria, valor, data e situação de uma saída.
- `Investimento`: ativo, tipo, valores aplicado/atual e rentabilidade calculada.

Os modelos de receitas, despesas e investimentos se relacionam com um usuário.
O dashboard e as telas de receitas e despesas ainda usam conteúdo de
demonstração; a gravação e consulta de transações ainda não foram implementadas.
