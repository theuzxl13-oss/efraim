# Varões Efraim — Setor 46

Sistema de cadastro de membros, atas de reuniões e eventos para os Varões Efraim
(Assembleia de Deus Ministério do Belém — Setor 46). Feito em **Python + Django**.

Site no ar: **https://varoesefraim.pythonanywhere.com**

- **Site público** (`/`, `/eventos/`, `/atas/`, `/aniversariantes/`): qualquer pessoa
  pode ver os eventos publicados, as atas de reuniões e os aniversariantes do mês,
  sem precisar de login.
- **Painel administrativo** (`/admin/`): acesso restrito por login e senha.
  - **Admin geral**: vê e gerencia todas as congregações e membros, cria os logins
    dos administradores de cada congregação, e é o único que gerencia atas de
    reuniões e eventos (inclusive a publicação deles no site público).
  - **Admin de congregação**: só cadastra, edita e exclui membros da própria
    congregação — não tem acesso a atas, eventos, outras congregações ou usuários.

## Cadastro de membros

Cada membro tem: nome completo, data de nascimento e cargo (Membro, Cooperador,
Diácono, Presbítero, Evangelista ou Pastor). Um administrador de congregação só
cadastra membros na sua própria congregação; o administrador geral pode cadastrar
em qualquer uma.

## Atas e eventos

Em **Atas de reuniões** e **Eventos**, cada registro pode ser vinculado a uma
congregação específica ou deixado em branco (aparece como "Setor 46", geral para
todos). Marque **"Publicada"/"Publicado"** para que apareça no site público — se
desmarcar, fica visível só no painel administrativo. Só o administrador geral tem
acesso a essas duas seções.

## Aniversariantes

A página pública `/aniversariantes/` mostra os membros que fazem aniversário no
mês selecionado (com destaque para quem faz aniversário hoje), com filtro por mês
e por congregação. Por privacidade, mostra só o dia e o mês — nunca o ano de
nascimento.

## Como rodar no seu computador

Pré-requisito: Python 3.12+ instalado.

```bash
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py createsuperuser
venv\Scripts\python manage.py runserver
```

O comando `createsuperuser` vai pedir para você escolher seu próprio usuário e senha —
esse será o seu login de **administrador geral** (acesso a tudo). Depois é só abrir
`http://localhost:8000/admin/` no navegador.

## Como criar as congregações e os outros logins

Logado como administrador geral:

1. No painel, vá em **Congregações → Adicionar** e cadastre cada congregação.
2. Vá em **Usuários → Adicionar** e crie um usuário para cada administrador de
   congregação. Marque a opção **"Membro da equipe" (is_staff)**.
3. Ainda na tela do usuário, role até **"Escopo de acesso"** e selecione a
   congregação daquele administrador. Isso faz com que ele só veja e edite os
   membros da própria congregação.
4. Adicione esse usuário ao grupo **"Admin de Congregação"** (na seção de grupos,
   dentro da mesma tela) — é esse grupo que dá permissão de cadastrar, editar e
   excluir membros. Ele não dá acesso a atas nem eventos.
5. Para um administrador com acesso geral, marque **"Membro da equipe"** e
   **"Superusuário"**, e deixe o campo de congregação em branco.

## Atualizando o site publicado (PythonAnywhere)

O site já está publicado em `varoesefraim.pythonanywhere.com`. Sempre que o
código deste repositório for atualizado, para refletir a mudança no site:

```bash
cd ~/efraim
git pull
venv/bin/python manage.py migrate
venv/bin/python manage.py collectstatic --noinput
```

E depois, na aba **Web** do painel do PythonAnywhere, clicar em **"Reload"**.

Contas gratuitas do PythonAnywhere precisam ser "renovadas" uma vez por mês (basta
entrar no painel e clicar em "Run until 1 month from today" na aba Web), senão o
site é pausado automaticamente.

## Estrutura do projeto

```
config/     configurações do Django (settings, urls)
core/       models, admin, views do sistema (congregações, membros, atas, eventos)
templates/  páginas HTML (site público + personalização do painel admin)
static/     CSS do site público e do painel admin
media/      arquivos enviados pelos administradores (fotos de eventos, PDFs de atas)
```
