from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.api.dependencies import exigir_perfis, obter_usuario_atual
from app.api.schemas.schemas import (
    AtualizarStatusRequest, CriarPedidoRequest, PedidoResponse
)
from app.application.services.pedido_service import (
    atualizar_status_pedido, criar_pedido
)
from app.domain.enums import CanalPedido, PerfilUsuario, StatusPedido
from app.domain.models.models import Pedido, Usuario

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("", response_model=PedidoResponse, status_code=201, summary="Criar pedido")
def novo_pedido(
    payload: CriarPedidoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.CLIENTE, PerfilUsuario.ATENDENTE, PerfilUsuario.ADMIN)
    ),
):
    return criar_pedido(
        db=db,
        cliente_id=usuario.id,
        unidade_id=payload.unidade_id,
        canal_pedido=payload.canal_pedido,
        itens=[i.model_dump() for i in payload.itens],
        forma_pagamento=payload.forma_pagamento,
    )


@router.get("", response_model=List[PedidoResponse], summary="Listar pedidos")
def listar_pedidos(
    canal_pedido: Optional[CanalPedido] = Query(None),
    status: Optional[StatusPedido] = Query(None),
    unidade_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(
            PerfilUsuario.GERENTE, PerfilUsuario.ADMIN,
            PerfilUsuario.ATENDENTE, PerfilUsuario.COZINHA
        )
    ),
):
    query = db.query(Pedido)
    if canal_pedido:
        query = query.filter(Pedido.canal_pedido == canal_pedido)
    if status:
        query = query.filter(Pedido.status == status)
    if unidade_id:
        query = query.filter(Pedido.unidade_id == unidade_id)
    offset = (page - 1) * limit
    return query.order_by(Pedido.criado_em.desc()).offset(offset).limit(limit).all()


@router.get("/meus", response_model=List[PedidoResponse], summary="Meus pedidos")
def meus_pedidos(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
):
    offset = (page - 1) * limit
    return (
        db.query(Pedido)
        .filter(Pedido.cliente_id == usuario.id)
        .order_by(Pedido.criado_em.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/{pedido_id}", response_model=PedidoResponse, summary="Consultar pedido")
def consultar_pedido(
    pedido_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obter_usuario_atual),
):
    from fastapi import HTTPException, status as http_status
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail={"error": "PEDIDO_NAO_ENCONTRADO", "message": "Pedido não encontrado."},
        )
    if usuario.perfil == PerfilUsuario.CLIENTE and pedido.cliente_id != usuario.id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail={"error": "ACESSO_NEGADO", "message": "Você não tem acesso a este pedido."},
        )
    return pedido


@router.patch("/{pedido_id}/status", response_model=PedidoResponse, summary="Atualizar status")
def atualizar_status(
    pedido_id: UUID,
    payload: AtualizarStatusRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(
            PerfilUsuario.COZINHA, PerfilUsuario.ATENDENTE,
            PerfilUsuario.GERENTE, PerfilUsuario.ADMIN
        )
    ),
):
    return atualizar_status_pedido(db, pedido_id, payload.status, usuario.id)
