from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.api.schemas.schemas import CadastroRequest, LoginRequest, TokenResponse
from app.application.services.auth_service import autenticar_usuario, cadastrar_usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse, summary="Login do usuário")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    return autenticar_usuario(db, payload.email, payload.senha)


@router.post("/cadastro", status_code=201, summary="Cadastro de novo usuário")
def cadastro(payload: CadastroRequest, db: Session = Depends(get_db)):
    usuario = cadastrar_usuario(
        db=db,
        nome=payload.nome,
        email=payload.email,
        senha=payload.senha,
        perfil=payload.perfil,
        consentimento_lgpd=payload.consentimento_lgpd,
    )
    return {"id": str(usuario.id), "nome": usuario.nome, "perfil": usuario.perfil.value}
