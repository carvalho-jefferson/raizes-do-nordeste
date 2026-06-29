from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core_config import settings
from app.infrastructure.database import Base, engine
from app.api.routers.auth_router import router as auth_router
from app.api.routers.pedidos_router import router as pedidos_router
from app.api.routers.outros_routers import (
    unidades_router, cardapio_router, estoque_router, fidelidade_router
)
from app.api.routers.produtos_router import router as produtos_router
from app.api.routers.usuarios_router import router as usuarios_router

import app.domain.models.models  # garante que os models são registrados no metadata

app = FastAPI(  
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "API back-end da rede de lanchonetes Raízes do Nordeste. "
        "Suporta múltiplos canais (APP, TOTEM, BALCÃO, PICKUP, WEB), "
        "gestão de pedidos, controle de estoque por unidade, "
        "programa de fidelização e integração com gateway de pagamento."
    ),
    contact={"name": "Raízes do Nordeste"},
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(Exception)
async def handler_generico(request: Request, exc: Exception):
    from datetime import datetime
    return JSONResponse(
        status_code=500,
        content={
            "error": "ERRO_INTERNO",
            "message": "Ocorreu um erro inesperado. Tente novamente.",
            "details": [],
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path),
        },
    )


app.include_router(auth_router)
app.include_router(pedidos_router)
app.include_router(unidades_router)
app.include_router(cardapio_router)
app.include_router(estoque_router)
app.include_router(fidelidade_router)
app.include_router(produtos_router)
app.include_router(usuarios_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_TITLE, "version": settings.APP_VERSION}