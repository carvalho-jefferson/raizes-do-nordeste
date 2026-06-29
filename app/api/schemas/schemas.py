from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.domain.enums import (
    CanalPedido, FormaPagamento, PerfilUsuario,
    StatusPagamento, StatusPedido, TipoUnidade
)


class ErroDetalhe(BaseModel):
    field: Optional[str] = None
    issue: str


class ErroResponse(BaseModel):
    error: str
    message: str
    details: List[ErroDetalhe] = []
    timestamp: datetime = datetime.utcnow()
    path: Optional[str] = None


# Auth
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class CadastroRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    perfil: PerfilUsuario = PerfilUsuario.CLIENTE
    consentimento_lgpd: bool

    @field_validator("senha")
    @classmethod
    def senha_minima(cls, v):
        if len(v) < 6:
            raise ValueError("A senha deve ter no mínimo 6 caracteres.")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict


# Unidades
class UnidadeResponse(BaseModel):
    id: UUID
    nome: str
    cidade: str
    estado: str
    tipo: TipoUnidade
    ativa: bool

    class Config:
        from_attributes = True


# Produtos / Cardápio
class ProdutoResponse(BaseModel):
    id: UUID
    nome: str
    descricao: Optional[str]
    preco: Decimal
    categoria: str
    disponivel: bool

    class Config:
        from_attributes = True


# Estoque
class EstoqueResponse(BaseModel):
    produto_id: UUID
    unidade_id: UUID
    quantidade: int
    atualizado_em: Optional[datetime]

    class Config:
        from_attributes = True


class MovimentacaoEstoqueRequest(BaseModel):
    produto_id: UUID
    quantidade: int

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        return v


# Pedidos
class ItemPedidoRequest(BaseModel):
    produto_id: UUID
    quantidade: int

    @field_validator("quantidade")
    @classmethod
    def quantidade_positiva(cls, v):
        if v <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        return v


class CriarPedidoRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    unidade_id: UUID
    canal_pedido: CanalPedido = Field(..., validation_alias="canalPedido")
    itens: List[ItemPedidoRequest]
    forma_pagamento: FormaPagamento


class AtualizarStatusRequest(BaseModel):
    status: StatusPedido


class ItemPedidoResponse(BaseModel):
    produto_id: UUID
    quantidade: int
    preco_unitario: Decimal

    class Config:
        from_attributes = True


class PagamentoResponse(BaseModel):
    id: UUID
    status: StatusPagamento
    gateway_referencia: Optional[str]
    valor: Decimal
    processado_em: Optional[datetime]

    class Config:
        from_attributes = True


class PedidoResponse(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

    id: UUID
    unidade_id: UUID
    canal_pedido: CanalPedido = Field(
        validation_alias="canalPedido",
        serialization_alias="canalPedido"
    )
    status: StatusPedido
    total: Decimal
    itens: List[ItemPedidoResponse]
    pagamento: Optional[PagamentoResponse]
    criado_em: datetime


# Programa de fidelidade
class FidelidadeResponse(BaseModel):
    pontos_saldo: int
    atualizado_em: Optional[datetime]

    class Config:
        from_attributes = True
