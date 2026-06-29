from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.api.dependencies import exigir_perfis, obter_usuario_atual
from app.api.schemas.schemas import ProdutoResponse
from app.api.schemas.schemas_extras import (
    AtualizarProdutoRequest, CriarProdutoRequest, VincularProdutoUnidadeRequest
)
from app.application.services.produto_service import (
    atualizar_produto, buscar_produto_por_id, criar_produto,
    desativar_produto, listar_produtos, vincular_produto_unidade
)
from app.domain.enums import PerfilUsuario
from app.domain.models.models import Usuario

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("", response_model=List[ProdutoResponse], summary="Listar produtos")
def listar(
    categoria: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: Usuario = Depends(obter_usuario_atual),
):
    produtos = listar_produtos(db, categoria)
    return [
        ProdutoResponse(
            id=p.id,
            nome=p.nome,
            descricao=p.descricao,
            preco=p.preco,
            categoria=p.categoria,
            disponivel=p.ativo,   # ← mapeamento manual aqui
        )
        for p in produtos
    ]


@router.get("/{produto_id}", response_model=ProdutoResponse, summary="Buscar produto por ID")
def buscar(
    produto_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(obter_usuario_atual),
):
    produto = buscar_produto_por_id(db, produto_id)
    return ProdutoResponse(
        id=produto.id,
        nome=produto.nome,
        descricao=produto.descricao,
        preco=produto.preco,
        categoria=produto.categoria,
        disponivel=produto.ativo,
    )


@router.post("", status_code=201, summary="Criar produto")
def criar(
    payload: CriarProdutoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    produto = criar_produto(
        db=db,
        nome=payload.nome,
        descricao=payload.descricao,
        preco=float(payload.preco),
        categoria=payload.categoria,
        usuario_id=usuario.id,
    )
    return {"id": str(produto.id), "nome": produto.nome, "preco": str(produto.preco)}


@router.patch("/{produto_id}", summary="Atualizar produto")
def atualizar(
    produto_id: UUID,
    payload: AtualizarProdutoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    return atualizar_produto(
        db=db,
        produto_id=produto_id,
        usuario_id=usuario.id,
        nome=payload.nome,
        descricao=payload.descricao,
        preco=float(payload.preco) if payload.preco else None,
        categoria=payload.categoria,
    )


@router.patch("/{produto_id}/desativar", summary="Desativar produto")
def desativar(
    produto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    return desativar_produto(db, produto_id, usuario.id)


@router.post(
    "/unidades/{unidade_id}/vincular",
    status_code=201,
    summary="Vincular produto ao cardápio de uma unidade",
)
def vincular(
    unidade_id: UUID,
    payload: VincularProdutoUnidadeRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    return vincular_produto_unidade(
        db=db,
        unidade_id=unidade_id,
        produto_id=payload.produto_id,
        periodo_sazonalidade=payload.periodo_sazonalidade,
        usuario_id=usuario.id,
    )
