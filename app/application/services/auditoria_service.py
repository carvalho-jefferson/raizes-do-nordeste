from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.models.models import AuditoriaLog


def registrar_acao(
    db: Session,
    acao: str,
    entidade: str,
    entidade_id: Optional[UUID] = None,
    usuario_id: Optional[UUID] = None,
    payload: Optional[dict] = None,
) -> None:
    log = AuditoriaLog(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        payload=payload,
    )
    db.add(log)
    db.flush()
