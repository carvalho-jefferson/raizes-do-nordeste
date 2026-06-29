import random
import uuid
from datetime import datetime


def processar_pagamento_mock(valor: float, forma_pagamento: str) -> dict:
    """
    Simula a chamada para um gateway de pagamento externo.
    Retorna aprovado na maior parte dos casos; recusa em torno de 20% das tentativas nessa simulaçãoa.
    """
    aprovado = random.random() > 0.2

    return {
        "gateway_referencia": str(uuid.uuid4()),
        "aprovado": aprovado,
        "status": "APROVADO" if aprovado else "RECUSADO",
        "mensagem": "Pagamento autorizado." if aprovado else "Pagamento recusado pela operadora.",
        "valor_processado": valor,
        "forma_pagamento": forma_pagamento,
        "processado_em": datetime.utcnow().isoformat(),
    }
