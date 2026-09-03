# Varões Efraim — Setor 46

Sistema de cadastro de membros, atas de reuniões e eventos para os Varões Efraim
(Assembleia de Deus Ministério do Belém — Setor 46). Feito em **Python + Django**.

- **Site público** (`/`, `/eventos/`, `/atas/`): qualquer pessoa pode ver os eventos e
  atas publicados, sem precisar de login.
- **Painel administrativo** (`/admin/`): acesso restrito por login e senha.
  - **Admin geral**: vê e gerencia todas as congregações, membros, atas e eventos, e
    também cria os logins dos administradores de cada congregação.
  - **Admin de congregação**: só vê e gerencia os dados da sua própria congregação.

## Como rodar no seu computador

Pré-requisito: Python 3.12+ instalado (já está, se você seguiu os passos até aqui).

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

1. No painel, vá em **Congregações → Adicionar** e cadastre cada congregação
   (ex: Sede, Congregação X, Congregação Y...).
2. Vá em **Usuários → Adicionar** e crie um usuário para cada administrador de
   congregação (ex: Isaac, Yuri). Marque a opção **"Membro da equipe" (is_staff)**.
3. Ainda na tela do usuário, role até **"Escopo de acesso"** e selecione a
   congregação daquele administrador. Isso faz com que ele só veja e edite os
   dados da própria congregação.
4. Adicione esse usuário ao grupo **"Admin de Congregação"** (na seção de grupos,
   dentro da mesma tela) — é esse grupo que dá permissão de gerenciar membros,
   atas e eventos.
5. Para um administrador com acesso geral (como você e o Kauan), marque
   **"Membro da equipe"** e **"Superusuário"**, e deixe o campo de congregação em
   branco.

## Cadastro de membros

Cada membro tem: nome completo, data de nascimento e cargo (Membro, Cooperador,
Diácono, Presbítero, Evangelista ou Pastor). Um administrador de congregação só
cadastra membros na sua própria congregação; o administrador geral pode cadastrar
em qualquer uma.

## Atas e eventos

Em **Atas de reuniões** e **Eventos**, cada registro pode ser vinculado a uma
congregação específica ou deixado em branco (aparece como "Setor 46", geral para
todos). Marque **"Publicada"/"Publicado"** para que apareça no site público — se
desmarcar, fica visível só no painel administrativo.

## Colocando o site no ar (produção)

Este projeto está pronto para ser publicado em qualquer serviço de hospedagem
Python (ex: Railway, Render, PythonAnywhere). Passos gerais:

1. Crie uma conta no serviço escolhido (isso você faz diretamente, por segurança
   eu não crio contas em nome de terceiros).
2. Configure as variáveis de ambiente do `.env.example` (gere uma
   `DJANGO_SECRET_KEY` nova e forte, coloque `DJANGO_DEBUG=False` e o domínio do
   site em `DJANGO_ALLOWED_HOSTS`).
3. Rode `python manage.py migrate` e `python manage.py collectstatic` no
   servidor.
4. Suba a aplicação com `gunicorn config.wsgi` (já incluso no
   `requirements.txt`).
5. Fotos de eventos e PDFs de atas ficam salvos na pasta `media/` — verifique se
   o serviço escolhido mantém essa pasta entre deploys (alguns exigem um "disco
   persistente" ou um serviço de armazenamento externo).

## Estrutura do projeto

```
config/     configurações do Django (settings, urls)
core/       models, admin, views do sistema (congregações, membros, atas, eventos)
templates/  páginas HTML (site público + personalização do painel admin)
static/     CSS do site público
media/      arquivos enviados pelos administradores (criado ao rodar)
```
