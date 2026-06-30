# Raízes do Nordeste — API Back-end

API REST desenvolvida em **Python + FastAPI** como projeto acadêmico da disciplina de Projeto Multidisciplinar — Trilha Back-end.

O sistema atende a rede de lanchonetes Raízes do Nordeste, suportando múltiplos canais de venda (APP, TOTEM, BALCAO, PICKUP e WEB), gestão de pedidos com controle de estoque por unidade, integração com gateway de pagamento via mock e programa de fidelização com conformidade à LGPD.

---

## Tecnologias utilizadas

| Camada | Tecnologia |
|---|---|
| Framework | FastAPI 0.111 |
| Banco de dados | PostgreSQL 15+ |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Autenticação | JWT (python-jose) + bcrypt (passlib) |
| Validação | Pydantic v2 |
| Documentação | Swagger/OpenAPI — gerado automaticamente pelo FastAPI |
| Testes | Postman |

---

## Pré-requisitos

- Python 3.11+
- PostgreSQL 15+ instalado e rodando localmente
- pip

---

## Configuração e execução

### 1. Clone o repositório

```bash
git clone https://github.com/carvalho-jefferson/raizes-do-nordeste.git
cd raizes-do-nordeste
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/raizes_db
SECRET_KEY=uma-chave-secreta-longa-e-aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 5. Crie o banco de dados

No terminal do PostgreSQL (psql) ou no pgAdmin:

```sql
CREATE DATABASE raizes_db;
```

Ou via terminal:

```bash
psql -U postgres -c "CREATE DATABASE raizes_db;"
```

### 6. Execute as migrations

```bash
alembic upgrade head
```

Isso cria todas as tabelas no banco conforme o modelo de dados.

### 7. Popule o banco com dados iniciais (seed)

```bash
python seed.py
```

Saída esperada:

```
Seed aplicado com sucesso!

Credenciais para teste:
  Admin:    admin@raizes.com / Admin@123
  Cliente:  joao@cliente.com / Cliente@123
  Cozinha:  cozinha@raizes.com / Cozinha@123
```

O seed cria: 2 unidades, 5 produtos, cardápio, estoque inicial e os usuários de teste.

**Execute o seed apenas uma vez. Caso precise recomeçar, recrie o banco de dados.**
### 8. Inicie a API

```bash
uvicorn main:app --reload
```

A API estará disponível em: **http://localhost:8000**

---

## Documentação (Swagger/OpenAPI)

Acesse no navegador após iniciar a API:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc ou http://localhost:8000/openapi.json

A documentação é gerada automaticamente pelo FastAPI e reflete todos os endpoints implementados com exemplos de request/response.

---

## Coleção de testes Postman

O arquivo `raizes_postman_collection.json` está na raiz do repositório.

**Como importar:**
1. Abra o Postman
2. Clique em **Import**
3. Selecione o arquivo `raizes_postman_collection.json`
4. Execute os testes **na ordem** — T01 e T02 salvam os tokens automaticamente para os demais

**Sequência recomendada de execução:**
1. T01 — Login admin (salva token_admin)
2. T02 — Login cliente (salva token_cliente)
3. T06 — Criar produto (salva produto_id)
4. T08 — Listar unidades (salva unidade_id)
5. T09 — Criar pedido (salva pedido_id)
6. Demais testes em qualquer ordem

---

## Endpoints principais

| Método | Rota | Perfil | Descrição |
|---|---|---|---|
| POST | `/auth/login` | Público | Login e geração de token JWT |
| POST | `/auth/cadastro` | Público | Cadastro de novo usuário |
| GET | `/usuarios` | ADMIN/GERENTE | Listar usuários |
| GET | `/usuarios/me` | Autenticado | Dados do usuário logado |
| PATCH | `/usuarios/{id}` | Autenticado | Atualizar usuário |
| PATCH | `/usuarios/{id}/desativar` | ADMIN | Desativar usuário |
| GET | `/unidades` | Autenticado | Listar unidades da rede |
| GET | `/unidades/{id}/cardapio` | Autenticado | Cardápio disponível da unidade |
| GET | `/produtos` | Autenticado | Listar produtos |
| POST | `/produtos` | ADMIN/GERENTE | Criar produto |
| PATCH | `/produtos/{id}` | ADMIN/GERENTE | Atualizar produto |
| PATCH | `/produtos/{id}/desativar` | ADMIN/GERENTE | Desativar produto |
| GET | `/estoque/{unidade_id}` | ADMIN/GERENTE/ATENDENTE | Estoque por unidade |
| POST | `/estoque/{unidade_id}/entrada` | ADMIN/GERENTE | Entrada de estoque |
| POST | `/pedidos` | CLIENTE/ATENDENTE | Criar pedido (fluxo crítico) |
| GET | `/pedidos` | ADMIN/GERENTE/ATENDENTE/COZINHA | Listar pedidos com filtros |
| GET | `/pedidos/meus` | Autenticado | Meus pedidos |
| GET | `/pedidos/{id}` | Autenticado | Consultar pedido por ID |
| PATCH | `/pedidos/{id}/status` | COZINHA/ATENDENTE/GERENTE/ADMIN | Atualizar status |
| GET | `/fidelidade/saldo` | Autenticado | Saldo de pontos do cliente |

---

## Canais de pedido (canalPedido)

O campo `canalPedido` é obrigatório em todo pedido criado e aceita os seguintes valores:

| Valor | Descrição |
|---|---|
| `APP` | Pedido realizado pelo aplicativo oficial da rede |
| `TOTEM` | Pedido realizado no totem de autoatendimento da loja |
| `BALCAO` | Pedido feito presencialmente com atendente no balcão |
| `PICKUP` | Pedido feito remotamente (app/web) com retirada rápida na loja |
| `WEB` | Pedido realizado pelo portal web da rede |

---

## Fluxo crítico — Pedido → Pagamento → Status

```
1. POST /auth/login          → obter token JWT
2. POST /pedidos             → criar pedido com canalPedido obrigatório
                               → valida cardápio e estoque da unidade
                               → desconta estoque
                               → chama pagamento mock
                               → APROVADO: status = EM_PREPARO, credita pontos
                               → RECUSADO: status = PAGAMENTO_RECUSADO, reverte estoque
3. PATCH /pedidos/{id}/status → cozinha atualiza: EM_PREPARO → PRONTO
4. PATCH /pedidos/{id}/status → atendente finaliza: PRONTO → ENTREGUE
```

---

## Arquitetura do projeto

O projeto adota uma arquitetura em quatro camadas com separação clara de responsabilidades:

```
raizes-backend/
├── main.py                              # Ponto de entrada da aplicação
├── seed.py                              # Dados iniciais para testes
├── requirements.txt                     # Dependências Python
├── .env.example                         # Modelo de variáveis de ambiente
├── alembic.ini                          # Configuração do Alembic
├── raizes_postman_collection.json       # Coleção de testes Postman
├── alembic/
│   ├── env.py                           # Configuração das migrations
│   └── versions/                        # Arquivos de migration gerados
└── app/
    ├── core_config.py                   # Configurações via pydantic-settings
    ├── domain/                          # Camada de domínio
    │   ├── enums.py                     # Enumerações do negócio
    │   └── models/
    │       └── models.py                # Entidades SQLAlchemy (11 tabelas)
    ├── application/                     # Camada de aplicação (casos de uso)
    │   └── services/
    │       ├── auth_service.py          # Cadastro e autenticação
    │       ├── pedido_service.py        # Fluxo crítico de pedidos
    │       ├── produto_service.py       # CRUD de produtos
    │       ├── usuario_service.py       # Gestão de usuários
    │       └── auditoria_service.py     # Registro de ações sensíveis (LGPD)
    ├── infrastructure/                  # Camada de infraestrutura
    │   ├── database.py                  # Configuração SQLAlchemy + sessão
    │   ├── security.py                  # JWT e bcrypt
    │   └── integrations/
    │       └── pagamento_mock.py        # Simulação do gateway de pagamento
    └── api/                             # Camada de interface (controllers)
        ├── dependencies.py              # Autenticação e controle de perfis
        ├── schemas/
        │   ├── schemas.py               # Contratos Pydantic principais
        │   └── schemas_extras.py        # Schemas de produtos e usuários
        └── routers/
            ├── auth_router.py           # Rotas de autenticação
            ├── pedidos_router.py        # Rotas de pedidos
            ├── produtos_router.py       # Rotas de produtos
            ├── usuarios_router.py       # Rotas de usuários
            └── outros_routers.py        # Unidades, estoque e fidelidade
```

---

## Segurança e LGPD

- Senhas armazenadas com **hash bcrypt** — nunca em texto puro
- Autenticação via **JWT** com expiração configurável
- Autorização por **perfil/role** em todos os endpoints protegidos
- Campo `consentimento_lgpd` obrigatório no cadastro, com registro da data
- Dados pessoais não expostos desnecessariamente nas respostas
- **Logs de auditoria** registrados para todas as ações sensíveis (criação de pedido, mudança de status, movimentação de estoque, login)

---

## Observação para o avaliador

- Link do repositório: https://github.com/carvalho-jefferson/raizes-do-nordeste.git
- Swagger local: http://localhost:8000/docs
- Coleção Postman: arquivo `raizes_postman_collection.json` na raiz do repositório
- Credenciais do seed estão documentadas na seção de configuração acima