from datetime import date
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict


class StoreProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    loja: str
    nome: str
    preco: Decimal
    imagem: Optional[str] = None
    link_afiliado: str
    data_cadastro: date
    ativo: bool


OrdemVitrine = Literal["chegada", "baratos", "caros"]
