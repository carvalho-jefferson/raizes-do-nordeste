from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.models.models import (
    Pedido, ItemPedido, Pagamento, Estoque,
    CardapioUnidade, Produto, Fidelidade, FidelidadeHistorico
)
from app.domain.enums import (
    CanalPedido, StatusPedido, StatusPagamento,
    FormaPagamento, TipoMovimentacaoFidelidade
)
from app.infrastructure.integrations.pagamento_mock import processar_pagamento_mock
from app.application.services.auditoria_service import registrar_acao

PONTOS_POR_REAL = 1


def criar_pedido(
    db: Session,
    cliente_id: UUID,
    unidade_id: UUID,
    canal_pedido: CanalPedido,
    itens: list[dict],
    forma_pagamento: FormaPagamento,
) -> Pedido:
    total = 0.0
    itens_validados = []

    for item in itens:
        produto_id = item["produto_id"]
        quantidade = item["quantidade"]

        if quantidade <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "QUANTIDADE_INVALIDA", "message": f"Quantidade inválida para o produto {produto_id}."},
            )

        cardapio = (
            db.query(CardapioUnidade)
            .filter(
                CardapioUnidade.unidade_id == unidade_id,
                CardapioUnidade.produto_id == produto_id,
                CardapioUnidade.disponivel == True,
            )
            .first()
        )
        if not cardapio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "PRODUTO_NAO_DISPONIVEL",
                    "message": f"Produto {produto_id} não disponível nesta unidade.",
                },
            )

        estoque = (
            db.query(Estoque)
            .filter(Estoque.unidade_id == unidade_id, Estoque.produto_id == produto_id)
            .first()
        )
        if not estoque or estoque.quantidade < quantidade:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "ESTOQUE_INSUFICIENTE",
                    "message": f"Estoque insuficiente para o produto {produto_id}.",
                },
            )

        total += float(cardapio.produto.preco) * quantidade
        itens_validados.append(
            {"produto": cardapio.produto, "estoque": estoque, "quantidade": quantidade}
        )

    pedido = Pedido(
        cliente_id=cliente_id,
        unidade_id=unidade_id,
        canal_pedido=canal_pedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        total=round(total, 2),
    )
    db.add(pedido)
    db.flush()

    for iv in itens_validados:
        item_pedido = ItemPedido(
            pedido_id=pedido.id,
            produto_id=iv["produto"].id,
            quantidade=iv["quantidade"],
            preco_unitario=iv["produto"].preco,
        )
        db.add(item_pedido)
        iv["estoque"].quantidade -= iv["quantidade"]
        iv["estoque"].atualizado_em = datetime.utcnow()

    resultado_gateway = processar_pagamento_mock(total, forma_pagamento.value)

    novo_status_pagamento = (
        StatusPagamento.APROVADO if resultado_gateway["aprovado"] else StatusPagamento.RECUSADO
    )
    pagamento = Pagamento(
        pedido_id=pedido.id,
        forma_pagamento=forma_pagamento,
        status=novo_status_pagamento,
        gateway_referencia=resultado_gateway["gateway_referencia"],
        valor=round(total, 2),
        processado_em=datetime.utcnow(),
    )
    db.add(pagamento)

    if resultado_gateway["aprovado"]:
        pedido.status = StatusPedido.EM_PREPARO
        _creditar_pontos_fidelidade(db, cliente_id, pedido.id, total)
    else:
        pedido.status = StatusPedido.PAGAMENTO_RECUSADO
        for iv in itens_validados:
            iv["estoque"].quantidade += iv["quantidade"]

    registrar_acao(
        db=db,
        acao="CRIACAO_PEDIDO",
        entidade="pedidos",
        entidade_id=pedido.id,
        usuario_id=cliente_id,
        payload={
            "canal": canal_pedido.value,
            "total": round(total, 2),
            "status_pagamento": novo_status_pagamento.value,
        },
    )

    db.commit()
    db.refresh(pedido)
    return pedido


def atualizar_status_pedido(
    db: Session,
    pedido_id: UUID,
    novo_status: StatusPedido,
    usuario_id: UUID,
) -> Pedido:
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "PEDIDO_NAO_ENCONTRADO", "message": "Pedido não encontrado."},
        )

    transicoes_validas = {
        StatusPedido.EM_PREPARO: [StatusPedido.PRONTO, StatusPedido.CANCELADO],
        StatusPedido.PRONTO: [StatusPedido.ENTREGUE],
        StatusPedido.AGUARDANDO_PAGAMENTO: [StatusPedido.CANCELADO],
    }

    permitidos = transicoes_validas.get(pedido.status, [])
    if novo_status not in permitidos:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "TRANSICAO_INVALIDA",
                "message": f"Não é possível alterar de {pedido.status.value} para {novo_status.value}.",
            },
        )

    status_anterior = pedido.status.value
    pedido.status = novo_status

    registrar_acao(
        db=db,
        acao="ATUALIZACAO_STATUS_PEDIDO",
        entidade="pedidos",
        entidade_id=pedido_id,
        usuario_id=usuario_id,
        payload={"status_anterior": status_anterior, "novo_status": novo_status.value},
    )

    db.commit()
    db.refresh(pedido)
    return pedido


def _creditar_pontos_fidelidade(
    db: Session, cliente_id: UUID, pedido_id: UUID, total: float
) -> None:
    pontos_ganhos = int(total * PONTOS_POR_REAL)
    if pontos_ganhos <= 0:
        return

    fidelidade = db.query(Fidelidade).filter(Fidelidade.cliente_id == cliente_id).first()
    if not fidelidade:
        fidelidade = Fidelidade(cliente_id=cliente_id, pontos_saldo=0)
        db.add(fidelidade)
        db.flush()

    fidelidade.pontos_saldo += pontos_ganhos

    historico = FidelidadeHistorico(
        fidelidade_id=fidelidade.id,
        pedido_id=pedido_id,
        tipo=TipoMovimentacaoFidelidade.CREDITO,
        pontos=pontos_ganhos,
    )
    db.add(historico)
