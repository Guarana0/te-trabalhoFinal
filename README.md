# Finanboard

Dashboard financeiro feito com Django e páginas HTML, CSS e JavaScript.
O cadastro e o login de usuários são reais. O dashboard e os módulos de
receitas, despesas e carteira usam dados vinculados à conta autenticada.
Investimentos também exibe preços de referência da B3 consultados pela BrAPI.

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
No primeiro acesso, responda ao questionário de renda, despesas, investimentos
e objetivo financeiro. O dashboard usa essas estimativas; elas podem ser
atualizadas pelo botão “Editar meu perfil”. Também é possível abrir
`/login/login.html`, `/login/registro.html`, `/receitas.html`, `/despesas.html`
e `/investimentos.html`.

O projeto usa o arquivo `db.sqlite3` por padrão, então não precisa de um
servidor MySQL para iniciar.

Na página de investimentos, a lista da BrAPI traz preços de fechamento de
PETR4, VALE3, ITUB4, B3SA3, BOVA11 e HGLG11. A consulta é atualizada a cada
cinco minutos; o botão da página força uma nova consulta. Não precisa criar
conta nem configurar token. As cotações podem estar atrasadas e não são uma
oferta ou recomendação de investimento.

Na página de despesas, cada conta pode registrar, consultar, editar e excluir
seus próprios lançamentos. O painel atualiza os totais, categorias e gráfico
conforme o período selecionado. O orçamento usado na comparação vem da
estimativa informada no questionário; não é um dado bancário.

Na página de receitas, cada conta pode registrar, consultar, editar e excluir
suas entradas. O fluxo líquido considera as receitas e despesas registradas no
período. Na carteira, é possível cadastrar, consultar, editar e remover ativos
e acompanhar os valores aplicado e atual. O valor atual da carteira é informado
manualmente; as cotações da BrAPI são apenas referências e não alteram esses
registros.

## Como o código está organizado

- `manage.py`: comando usado para iniciar o Django e executar tarefas do projeto.
- `config/`: configurações, URLs e pontos de entrada do servidor web.
- `model/`: modelos de dados e migrações do Django.
- `view/`: páginas HTML e arquivos estáticos em `assets/`.
- `database/`: cópia SQL relacionada ao banco MySQL original.
- `db.sqlite3`: banco SQLite usado localmente.

## O que os modelos representam

- `Usuario`: nome, e-mail e senha protegida por hash.
- `Receita`: descrição, categoria, valor e data de uma entrada de dinheiro, associada à conta autenticada.
- `Despesa`: descrição, categoria, valor, data e situação de uma saída, associada à conta autenticada.
- `Investimento`: ativo, tipo, valores aplicado/atual e rentabilidade calculada, associado à conta autenticada.
- `PerfilFinanceiro`: estimativas do questionário, salvas por usuário.

O painel inicial usa as estimativas do questionário e, quando há ativos
cadastrados, mostra o valor atual da carteira. Receitas, despesas e ativos da
carteira são registros independentes por conta.
