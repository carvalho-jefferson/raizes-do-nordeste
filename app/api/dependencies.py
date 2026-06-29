from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.security import decodificar_token
from app.domain.models.models import Usuario
from app.domain.enums import PerfilUsuario

bearer_scheme = HTTPBearer()


def obter_usuario_atual(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decodificar_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "TOKEN_INVALIDO", "message": "Token inválido ou expirado."},
        )

    usuario = db.query(Usuario).filter(
        Usuario.id == UUID(payload["sub"]), Usuario.ativo == True
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "USUARIO_NAO_ENCONTRADO", "message": "Usuário não encontrado."},
        )
    return usuario


def exigir_perfis(*perfis: PerfilUsuario):
    def verificar(usuario: Usuario = Depends(obter_usuario_atual)):
        if usuario.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "ACESSO_NEGADO",
                    "message": f"Acesso restrito aos perfis: {[p.value for p in perfis]}.",
                },
            )
        return usuario
    return verificar
