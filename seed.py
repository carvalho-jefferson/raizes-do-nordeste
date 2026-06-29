"""
Seed inicial — popula o banco com dados de exemplo para testes.
Execute com: python seed.py
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.infrastructure.database import SessionLocal
from app.domain.models.models import (
    Usuario, Unidade, Produto, CardapioUnidade, Estoque
)
from app.domain.enums import PerfilUsuario, TipoUnidade
from app.infrastructure.security import hash_senha

db = SessionLocal()

try:
    # Usuários
    admin = Usuario(
        nome="Admin Raízes",
        email="admin@raizes.com",
        senha_hash=hash_senha("Admin@123"),
        perfil=PerfilUsuario.ADMIN,
        consentimento_lgpd=True,
        consentimento_em=datetime.utcnow(),
    )
    cliente = Usuario(
        nome="João Silva",
        email="joao@cliente.com",
        senha_hash=hash_senha("Cliente@123"),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True,
        consentimento_em=datetime.utcnow(),
    )
    cozinha = Usuario(
        nome="Maria Cozinha",
        email="cozinha@raizes.com",
        senha_hash=hash_senha("Cozinha@123"),
        perfil=PerfilUsuario.COZINHA,
        consentimento_lgpd=True,
        consentimento_em=datetime.utcnow(),
    )
    db.add_all([admin, cliente, cozinha])
    db.flush()

    # Unidades
    unidade_recife = Unidade(
        nome="Raízes Boa Viagem",
        cidade="Recife",
        estado="PE",
        tipo=TipoUnidade.COMPLETA,
    )
    unidade_fortaleza = Unidade(
        nome="Raízes Meireles",
        cidade="Fortaleza",
        estado="CE",
        tipo=TipoUnidade.REDUZIDA,
    )
    db.add_all([unidade_recife, unidade_fortaleza])
    db.flush()

    # Produtos
    tapioca = Produto(nome="Tapioca Nordestina", descricao="Tapioca recheada com queijo coalho e carne de sol", preco=18.90, categoria="Salgados")
    cuscuz = Produto(nome="Cuscuz com Ovo", descricao="Cuscuz de milho com ovo estrelado e manteiga de garrafa", preco=12.50, categoria="Salgados")
    suco_umbu = Produto(nome="Suco de Umbu", descricao="Suco natural de umbu", preco=9.00, categoria="Bebidas")
    cafe = Produto(nome="Café Nordestino", descricao="Café coado com canela", preco=6.00, categoria="Bebidas")
    bolo_macaxeira = Produto(nome="Bolo de Macaxeira", descricao="Bolo úmido de mandioca com coco", preco=8.00, categoria="Doces")
    db.add_all([tapioca, cuscuz, suco_umbu, cafe, bolo_macaxeira])
    db.flush()

    # Cardápio da unidade Recife (todos os produtos)
    for produto in [tapioca, cuscuz, suco_umbu, cafe, bolo_macaxeira]:
        db.add(CardapioUnidade(unidade_id=unidade_recife.id, produto_id=produto.id, disponivel=True))
        db.add(Estoque(unidade_id=unidade_recife.id, produto_id=produto.id, quantidade=50))

    # Cardápio da unidade Fortaleza (sem bolo de macaxeira)
    for produto in [tapioca, cuscuz, suco_umbu, cafe]:
        db.add(CardapioUnidade(unidade_id=unidade_fortaleza.id, produto_id=produto.id, disponivel=True))
        db.add(Estoque(unidade_id=unidade_fortaleza.id, produto_id=produto.id, quantidade=30))

    db.commit()
    print("Seed aplicado com sucesso!")
    print("\nCredenciais para teste:")
    print("  Admin:    admin@raizes.com / Admin@123")
    print("  Cliente:  joao@cliente.com / Cliente@123")
    print("  Cozinha:  cozinha@raizes.com / Cozinha@123")

except Exception as e:
    db.rollback()
    print(f"Erro ao aplicar seed: {e}")
    raise
finally:
    db.close()
