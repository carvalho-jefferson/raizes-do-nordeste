from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.api.dependencies import exigir_perfis, obter_usuario_atual
from app.api.schemas.schemas_extras import AtualizarUsuarioRequest, UsuarioResponse
from app.application.services.usuario_service import (
    atualizar_usuario, buscar_usuario_por_id,
    desativar_usuario, listar_usuarios
)
from app.domain.enums import PerfilUsuario
from app.domain.models.models import Usuario

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.get("", response_model=List[UsuarioResponse], summary="Listar usuários")
def listar(
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    return listar_usuarios(db)


@router.get("/me", response_model=UsuarioResponse, summary="Meus dados")
def meu_perfil(usuario: Usuario = Depends(obter_usuario_atual)):
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioResponse, summary="Buscar usuário por ID")
def buscar(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    _: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN, PerfilUsuario.GERENTE)
    ),
):
    return buscar_usuario_por_id(db, usuario_id)


@router.patch("/{usuario_id}", response_model=UsuarioResponse, summary="Atualizar usuário")
def atualizar(
    usuario_id: UUID,
    payload: AtualizarUsuarioRequest,
    db: Session = Depends(get_db),
    solicitante: Usuario = Depends(obter_usuario_atual),
):
    return atualizar_usuario(
        db=db,
        usuario_id=usuario_id,
        solicitante=solicitante,
        nome=payload.nome,
        perfil=payload.perfil,
    )


@router.patch("/{usuario_id}/desativar", summary="Desativar usuário")
def desativar(
    usuario_id: UUID,
    db: Session = Depends(get_db),
    solicitante: Usuario = Depends(
        exigir_perfis(PerfilUsuario.ADMIN)
    ),
):
    return desativar_usuario(db, usuario_id, solicitante.id)
