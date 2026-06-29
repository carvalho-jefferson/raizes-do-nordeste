from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.models import Usuario
from app.domain.enums import PerfilUsuario
from app.infrastructure.security import hash_senha, verificar_senha, criar_token_acesso
from app.application.services.auditoria_service import registrar_acao


def cadastrar_usuario(
    db: Session,
    nome: str,
    email: str,
    senha: str,
    perfil: PerfilUsuario,
    consentimento_lgpd: bool,
) -> Usuario:
    existente = db.query(Usuario).filter(Usuario.email == email).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "EMAIL_JA_CADASTRADO", "message": "Este e-mail já está em uso."},
        )

    usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_senha(senha),
        perfil=perfil,
        consentimento_lgpd=consentimento_lgpd,
        consentimento_em=datetime.utcnow() if consentimento_lgpd else None,
    )
    db.add(usuario)
    db.flush()

    registrar_acao(
        db=db,
        acao="CADASTRO_USUARIO",
        entidade="usuarios",
        entidade_id=usuario.id,
        payload={"perfil": perfil.value, "email": email},
    )

    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar_usuario(db: Session, email: str, senha: str) -> dict:
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo == True).first()

    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "CREDENCIAIS_INVALIDAS", "message": "E-mail ou senha inválidos."},
        )

    token = criar_token_acesso({"sub": str(usuario.id), "perfil": usuario.perfil.value})

    registrar_acao(
        db=db,
        acao="LOGIN",
        entidade="usuarios",
        entidade_id=usuario.id,
        usuario_id=usuario.id,
    )
    db.commit()

    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "id": str(usuario.id),
            "nome": usuario.nome,
            "perfil": usuario.perfil.value,
        },
    }
