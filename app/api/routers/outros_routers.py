from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.api.dependencies import exigir_perfis, obter_usuario_atual
from app.api.schemas.schemas import (
    EstoqueResponse, FidelidadeResponse,
    MovimentacaoEstoqueRequest, ProdutoResponse, UnidadeResponse
)
from app.application.services.auditoria_service import registrar_acao
from app.domain.enums import PerfilUsuario
from app.domain.models.models import (
    CardapioUnidade, Estoque, Fidelidade, Unidade
)


# Unidades da empresa

unidades_router = APIRouter(prefix="/unidades", tags=["Unidades"])


@unidades_router.get("", response_model=List[UnidadeResponse], summary="Listar unidades")
def listar_unidades(
    ativa: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    _: any = Depends(obter_usuario_atual),
):
    query = db.query(Unidade)
    if ativa is not None:
        query = query.filter(Unidade.ativa == ativa)
    return query.all()


@unidades_router.get("/{unidade_id}", response_model=UnidadeResponse, summary="Buscar unidade")
def buscar_unidade(
    unidade_id: UUID,
    db: Session = Depends(get_db),
    _: any = Depends(obter_usuario_atual),
):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "UNIDADE_NAO_ENCONTRADA", "message": "Unidade não encontrada."},
        )
    return unidade


# Cardápio / Produtos da unidade
cardapio_router = APIRouter(prefix="/unidades", tags=["Cardápio"])


@cardapio_router.get(
    "/{unidade_id}/cardapio",
    response_model=List[ProdutoResponse],
    summary="Cardápio da unidade",
)
def cardapio_da_unidade(
    unidade_id: UUID,
    db: Session = Depends(get_db),
    _: any = Depends(obter_usuario_atual),
):
    itens = (
        db.query(CardapioUnidade)
        .filter(
            CardapioUnidade.unidade_id == unidade_id,
            CardapioUnidade.disponivel == True,
        )
        .all()
    )
    return [
        ProdutoResponse(
            id=i.produto.id,
            nome=i.produto.nome,
            descricao=i.produto.descricao,
            preco=i.produto.preco,
            categoria=i.produto.categoria,
            disponivel=i.disponivel,
        )
        for i in itens
    ]


# Estoque
estoque_router = APIRouter(prefix="/estoque", tags=["Estoque"])


@estoque_router.get(
    "/{unidade_id}",
    response_model=List[EstoqueResponse],
    summary="Estoque por unidade",
)
def consultar_estoque(
    unidade_id: UUID,
    db: Session = Depends(get_db),
    _: any = Depends(
        exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN, PerfilUsuario.ATENDENTE)
    ),
):
    return db.query(Estoque).filter(Estoque.unidade_id == unidade_id).all()


@estoque_router.post(
    "/{unidade_id}/entrada",
    status_code=200,
    summary="Entrada de estoque",
)
def entrada_estoque(
    unidade_id: UUID,
    payload: MovimentacaoEstoqueRequest,
    db: Session = Depends(get_db),
    usuario: any = Depends(
        exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ADMIN)
    ),
):
    estoque = db.query(Estoque).filter(
        Estoque.unidade_id == unidade_id,
        Estoque.produto_id == payload.produto_id,
    ).first()

    if not estoque:
        estoque = Estoque(
            unidade_id=unidade_id,
            produto_id=payload.produto_id,
            quantidade=0,
        )
        db.add(estoque)

    estoque.quantidade += payload.quantidade
    registrar_acao(
        db=db,
        acao="ENTRADA_ESTOQUE",
        entidade="estoque",
        usuario_id=usuario.id,
        payload={"produto_id": str(payload.produto_id), "quantidade": payload.quantidade},
    )
    db.commit()
    db.refresh(estoque)
    return {"produto_id": str(estoque.produto_id), "quantidade_atual": estoque.quantidade}


# Programa de fidelidade
fidelidade_router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])


@fidelidade_router.get("/saldo", response_model=FidelidadeResponse, summary="Saldo de pontos")
def saldo_fidelidade(
    db: Session = Depends(get_db),
    usuario: any = Depends(obter_usuario_atual),
):
    fidelidade = db.query(Fidelidade).filter(Fidelidade.cliente_id == usuario.id).first()
    if not fidelidade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "FIDELIDADE_NAO_ENCONTRADA", "message": "Nenhum histórico de pontos encontrado."},
        )
    return fidelidade
