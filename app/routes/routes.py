from fastapi import APIRouter, HTTPException, status
from typing import List
from datetime import datetime

from app.models.produto import Produto, ProdutoCreate
from app.config.database import produtos_db, ProdutoQuery

app_router = APIRouter()

def get_next_id() -> int:
    """Gera o próximo ID disponível"""
    docs = produtos_db.all()
    if not docs:
        return 1
    return max(doc.get('id', 0) for doc in docs) + 1

@app_router.get("/", tags=["Home"])
async def home():
    return {"message": "Bem-vindo à API de Estoque com JSON Database"}

@app_router.post("/produtos/", response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Produtos"])
async def criar_produto(produto: ProdutoCreate):
    """Cria um novo produto"""
    produto_dict = produto.dict()
    produto_dict['id'] = get_next_id()
    produto_dict['data_criacao'] = datetime.now().isoformat()
    produto_dict['data_atualizacao'] = datetime.now().isoformat()
    
    produtos_db.insert(produto_dict)
    return {"message": "Produto criado com sucesso", "id": produto_dict['id']}

@app_router.get("/produtos/", response_model=List[dict], tags=["Produtos"])
async def listar_produtos(skip: int = 0, limit: int = 10):
    """Lista todos os produtos com paginação"""
    all_products = produtos_db.all()
    return all_products[skip:skip + limit]

@app_router.get("/produtos/{produto_id}", response_model=dict, tags=["Produtos"])
async def buscar_produto(produto_id: int):
    """Busca um produto pelo ID"""
    produto = produtos_db.get(ProdutoQuery.id == produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    return produto

@app_router.put("/produtos/{produto_id}", response_model=dict, tags=["Produtos"])
async def atualizar_produto(produto_id: int, produto_update: ProdutoCreate):
    """Atualiza um produto existente"""
    produto = produtos_db.get(ProdutoQuery.id == produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    update_data = produto_update.dict()
    update_data['data_atualizacao'] = datetime.now().isoformat()
    update_data['id'] = produto_id  # Garante que o ID não seja alterado
    
    produtos_db.update(update_data, ProdutoQuery.id == produto_id)
    return {"message": "Produto atualizado com sucesso"}

@app_router.delete("/produtos/{produto_id}", response_model=dict, tags=["Produtos"])
async def deletar_produto(produto_id: int):
    """Remove um produto"""
    produto = produtos_db.get(ProdutoQuery.id == produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    produtos_db.remove(ProdutoQuery.id == produto_id)
    return {"message": "Produto removido com sucesso"}
