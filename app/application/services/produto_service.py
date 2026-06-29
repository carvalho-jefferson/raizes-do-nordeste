from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.models import Produto, CardapioUnidade, Estoque
from app.application.services.auditoria_service import registrar_acao


def listar_produtos(db: Session, categoria: Optional[str] = None) -> List[Produto]:
    query = db.query(Produto).filter(Produto.ativo == True)
    if categoria:
        query = query.filter(Produto.categoria == categoria)
    return query.all()


def buscar_produto_por_id(db: Session, produto_id: UUID) -> Produto:
    produto = db.query(Produto).filter(Produto.id == produto_id).first()
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PRODUTO_NAO_ENCONTRADO", "message": "Produto não encontrado."},
        )
    return produto


def criar_produto(
    db: Session,
    nome: str,
    descricao: Optional[str],
    preco: float,
    categoria: str,
    usuario_id: UUID,
) -> Produto:
    produto = Produto(
        nome=nome,
        descricao=descricao,
        preco=preco,
        categoria=categoria,
    )
    db.add(produto)
    db.flush()

    registrar_acao(
        db=db,
        acao="CRIACAO_PRODUTO",
        entidade="produtos",
        entidade_id=produto.id,
        usuario_id=usuario_id,
        payload={"nome": nome, "preco": str(preco), "categoria": categoria},
    )

    db.commit()
    db.refresh(produto)
    return produto


def atualizar_produto(
    db: Session,
    produto_id: UUID,
    usuario_id: UUID,
    nome: Optional[str] = None,
    descricao: Optional[str] = None,
    preco: Optional[float] = None,
    categoria: Optional[str] = None,
) -> Produto:
    produto = buscar_produto_por_id(db, produto_id)

    if nome:
        produto.nome = nome
    if descricao is not None:
        produto.descricao = descricao
    if preco is not None:
        produto.preco = preco
    if categoria:
        produto.categoria = categoria

    registrar_acao(
        db=db,
        acao="ATUALIZACAO_PRODUTO",
        entidade="produtos",
        entidade_id=produto_id,
        usuario_id=usuario_id,
        payload={"nome": nome, "preco": str(preco), "categoria": categoria},
    )

    db.commit()
    db.refresh(produto)
    return produto


def desativar_produto(db: Session, produto_id: UUID, usuario_id: UUID) -> dict:
    produto = buscar_produto_por_id(db, produto_id)
    produto.ativo = False

    registrar_acao(
        db=db,
        acao="DESATIVACAO_PRODUTO",
        entidade="produtos",
        entidade_id=produto_id,
        usuario_id=usuario_id,
    )

    db.commit()
    return {"message": f"Produto '{produto.nome}' desativado com sucesso."}


def vincular_produto_unidade(
    db: Session,
    unidade_id: UUID,
    produto_id: UUID,
    periodo_sazonalidade: Optional[str],
    usuario_id: UUID,
) -> dict:
    buscar_produto_por_id(db, produto_id)

    existente = db.query(CardapioUnidade).filter(
        CardapioUnidade.unidade_id == unidade_id,
        CardapioUnidade.produto_id == produto_id,
    ).first()

    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "PRODUTO_JA_VINCULADO", "message": "Produto já está no cardápio desta unidade."},
        )

    cardapio = CardapioUnidade(
        unidade_id=unidade_id,
        produto_id=produto_id,
        disponivel=True,
        periodo_sazonalidade=periodo_sazonalidade,
    )
    db.add(cardapio)

    estoque_existente = db.query(Estoque).filter(
        Estoque.unidade_id == unidade_id,
        Estoque.produto_id == produto_id,
    ).first()

    if not estoque_existente:
        db.add(Estoque(unidade_id=unidade_id, produto_id=produto_id, quantidade=0))

    registrar_acao(
        db=db,
        acao="VINCULO_PRODUTO_UNIDADE",
        entidade="cardapio_unidade",
        usuario_id=usuario_id,
        payload={"unidade_id": str(unidade_id), "produto_id": str(produto_id)},
    )

    db.commit()
    return {"message": "Produto vinculado ao cardápio da unidade com sucesso."}
