from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime
from tinydb import TinyDB, Query
import os

# Configuração do banco de dados
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'db.json')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
produtos_db = TinyDB(db_path)
ProdutoQuery = Query()

app_router = APIRouter()

def get_next_id() -> int:
    """Gera o próximo ID disponível"""
    docs = produtos_db.all()
    if not docs:
        return 1
    return max(doc.get('id', 0) for doc in docs) + 1

@app_router.get("/", tags=["Home"])
async def home():
    return {"message": "Bem-vindo à API de Estoque"}

@app_router.get("/produtos/", response_model=List[Dict[str, Any]], tags=["Produtos"])
async def listar_produtos(skip: int = 0, limit: int = 10):
    """Lista todos os produtos com paginação"""
    all_products = produtos_db.all()
    return all_products[skip:skip + limit]

@app_router.get("/produtos/{produto_id}", response_model=Dict[str, Any], tags=["Produtos"])
async def buscar_produto(produto_id: int):
    """Busca um produto pelo ID"""
    produto = produtos_db.get(ProdutoQuery.id == produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    return produto

@app_router.post("/produtos/", status_code=status.HTTP_201_CREATED, tags=["Produtos"])
async def criar_produto(produto: Dict[str, Any]):
    """Cria um novo produto"""
    produto_id = get_next_id()
    produto['id'] = produto_id
    produto['data_criacao'] = datetime.now().isoformat()
    produto['data_atualizacao'] = datetime.now().isoformat()
    
    produtos_db.insert(produto)
    return {"message": "Produto criado com sucesso", "id": produto_id}

@app_router.put("/produtos/{produto_id}", tags=["Produtos"])
async def atualizar_produto(produto_id: int, produto_update: Dict[str, Any]):
    """Atualiza um produto existente"""
    produto = produtos_db.get(ProdutoQuery.id == produto_id)
    if not produto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado"
        )
    
    update_data = {**produto, **produto_update}
    update_data['data_atualizacao'] = datetime.now().isoformat()
    
    produtos_db.update(update_data, ProdutoQuery.id == produto_id)
    return {"message": "Produto atualizado com sucesso"}

@app_router.delete("/produtos/{produto_id}", tags=["Produtos"])
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