from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.models import Usuario
from app.domain.enums import PerfilUsuario
from app.application.services.auditoria_service import registrar_acao


def listar_usuarios(db: Session) -> List[Usuario]:
    return db.query(Usuario).filter(Usuario.ativo == True).all()


def buscar_usuario_por_id(db: Session, usuario_id: UUID) -> Usuario:
    usuario = db.query(Usuario).filter(
        Usuario.id == usuario_id, Usuario.ativo == True
    ).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "USUARIO_NAO_ENCONTRADO", "message": "Usuário não encontrado."},
        )
    return usuario


def atualizar_usuario(
    db: Session,
    usuario_id: UUID,
    solicitante: Usuario,
    nome: Optional[str] = None,
    perfil: Optional[PerfilUsuario] = None,
) -> Usuario:
    usuario = buscar_usuario_por_id(db, usuario_id)

    # O cliente só pode atualizar o próprio perfil
    if solicitante.perfil == PerfilUsuario.CLIENTE and solicitante.id != usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACESSO_NEGADO", "message": "Você só pode atualizar seus próprios dados."},
        )

    # Apenas ADMIN pode alterar perfil
    if perfil and solicitante.perfil != PerfilUsuario.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "ACESSO_NEGADO", "message": "Apenas administradores podem alterar perfis."},
        )

    if nome:
        usuario.nome = nome
    if perfil:
        usuario.perfil = perfil

    registrar_acao(
        db=db,
        acao="ATUALIZACAO_USUARIO",
        entidade="usuarios",
        entidade_id=usuario_id,
        usuario_id=solicitante.id,
        payload={"nome": nome, "perfil": perfil.value if perfil else None},
    )

    db.commit()
    db.refresh(usuario)
    return usuario


def desativar_usuario(db: Session, usuario_id: UUID, solicitante_id: UUID) -> dict:
    usuario = buscar_usuario_por_id(db, usuario_id)

    if usuario.id == solicitante_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "OPERACAO_INVALIDA", "message": "Você não pode desativar sua própria conta."},
        )

    usuario.ativo = False

    registrar_acao(
        db=db,
        acao="DESATIVACAO_USUARIO",
        entidade="usuarios",
        entidade_id=usuario_id,
        usuario_id=solicitante_id,
    )

    db.commit()
    return {"message": f"Usuário '{usuario.nome}' desativado com sucesso."}
