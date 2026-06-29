from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import PerfilUsuario


# Produtos
class CriarProdutoRequest(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco: Decimal
    categoria: str


class AtualizarProdutoRequest(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    preco: Optional[Decimal] = None
    categoria: Optional[str] = None


class VincularProdutoUnidadeRequest(BaseModel):
    produto_id: UUID
    periodo_sazonalidade: Optional[str] = None


# Usuários
class AtualizarUsuarioRequest(BaseModel):
    nome: Optional[str] = None
    perfil: Optional[PerfilUsuario] = None


class UsuarioResponse(BaseModel):
    id: UUID
    nome: str
    email: str
    perfil: PerfilUsuario
    ativo: bool
    consentimento_lgpd: bool

    class Config:
        from_attributes = True
