import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.infrastructure.database import Base
from app.domain.enums import (
    PerfilUsuario, CanalPedido, StatusPedido,
    StatusPagamento, FormaPagamento,
    TipoMovimentacaoFidelidade, TipoUnidade
)


def gerar_uuid():
    return str(uuid.uuid4())


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(Enum(PerfilUsuario), nullable=False, default=PerfilUsuario.CLIENTE)
    ativo = Column(Boolean, default=True, nullable=False)
    consentimento_lgpd = Column(Boolean, default=False, nullable=False)
    consentimento_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    pedidos = relationship("Pedido", back_populates="cliente")
    fidelidade = relationship("Fidelidade", back_populates="cliente", uselist=False)
    logs = relationship("AuditoriaLog", back_populates="usuario")


class Unidade(Base):
    __tablename__ = "unidades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    cidade = Column(String(80), nullable=False)
    estado = Column(String(2), nullable=False)
    tipo = Column(Enum(TipoUnidade), default=TipoUnidade.COMPLETA, nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)

    pedidos = relationship("Pedido", back_populates="unidade")
    cardapio = relationship("CardapioUnidade", back_populates="unidade")
    estoque = relationship("Estoque", back_populates="unidade")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Numeric(10, 2), nullable=False)
    categoria = Column(String(60), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    cardapio = relationship("CardapioUnidade", back_populates="produto")
    estoque = relationship("Estoque", back_populates="produto")
    itens_pedido = relationship("ItemPedido", back_populates="produto")


class CardapioUnidade(Base):
    __tablename__ = "cardapio_unidade"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)
    disponivel = Column(Boolean, default=True, nullable=False)
    periodo_sazonalidade = Column(String(60), nullable=True)

    unidade = relationship("Unidade", back_populates="cardapio")
    produto = relationship("Produto", back_populates="cardapio")


class Estoque(Base):
    __tablename__ = "estoque"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=0, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    unidade = relationship("Unidade", back_populates="estoque")
    produto = relationship("Produto", back_populates="estoque")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    unidade_id = Column(UUID(as_uuid=True), ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(Enum(CanalPedido), nullable=False)
    status = Column(Enum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Usuario", back_populates="pedidos")
    unidade = relationship("Unidade", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamento = relationship("Pagamento", back_populates="pedido", uselist=False)
    historico_fidelidade = relationship("FidelidadeHistorico", back_populates="pedido")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(UUID(as_uuid=True), ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(10, 2), nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto", back_populates="itens_pedido")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), unique=True, nullable=False)
    forma_pagamento = Column(Enum(FormaPagamento), nullable=False)
    status = Column(Enum(StatusPagamento), default=StatusPagamento.PENDENTE, nullable=False)
    gateway_referencia = Column(String(120), nullable=True)
    valor = Column(Numeric(10, 2), nullable=False)
    processado_em = Column(DateTime, nullable=True)

    pedido = relationship("Pedido", back_populates="pagamento")


class Fidelidade(Base):
    __tablename__ = "fidelidade"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    pontos_saldo = Column(Integer, default=0, nullable=False)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cliente = relationship("Usuario", back_populates="fidelidade")
    historico = relationship("FidelidadeHistorico", back_populates="fidelidade")


class FidelidadeHistorico(Base):
    __tablename__ = "fidelidade_historico"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fidelidade_id = Column(UUID(as_uuid=True), ForeignKey("fidelidade.id"), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedidos.id"), nullable=True)
    tipo = Column(Enum(TipoMovimentacaoFidelidade), nullable=False)
    pontos = Column(Integer, nullable=False)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    fidelidade = relationship("Fidelidade", back_populates="historico")
    pedido = relationship("Pedido", back_populates="historico_fidelidade")


class AuditoriaLog(Base):
    __tablename__ = "auditoria_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String(100), nullable=False)
    entidade = Column(String(60), nullable=False)
    entidade_id = Column(UUID(as_uuid=True), nullable=True)
    payload = Column(JSON, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="logs")
