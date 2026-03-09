from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import logging
import csv
import io
from app.database import get_db
from app.services.tarefa_service import TarefaService
from app.models.tarefa import TarefaCreate, TarefaUpdate, TarefaResponse, TarefaStatusUpdate, TarefaObservacaoUpdate, TarefaDelete
from pydantic import BaseModel

# Configurar logger
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Kanban"],
    responses={404: {"description": "Não encontrado"}},
)

# Modelos adicionais para as requisições
class TarefaStatusUpdateRequest(BaseModel):
    status: str
    observacao: str = None

class TarefaObservacaoUpdateRequest(BaseModel):
    observacao: str

@router.post("/tarefas/upload", response_model=List[TarefaResponse])
async def upload_tarefas_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Faz upload de um arquivo CSV e cria tarefas em massa
    
    Formato esperado do CSV:
    title,imei,unidade,prazo,perfil,priority,observacao,numero_chamado,status
    
    Campos obrigatórios: title, imei, unidade, prazo, perfil
    """
    logger.info(f"Recebido upload do arquivo: {file.filename}")
    
    # Verificar se é um arquivo CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos CSV são permitidos"
        )
    
    try:
        # Ler conteúdo do arquivo
        contents = await file.read()
        csv_content = contents.decode('utf-8')
        
        # Processar CSV
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        tarefas_data = []
        
        # Mapeamento de colunas (case insensitive)
        field_mapping = {
            'title': ['title', 'titulo', 'título'],
            'imei': ['imei', 'serial'],
            'unidade': ['unidade', 'unit', 'loja'],
            'prazo': ['prazo', 'deadline', 'data_prazo'],
            'perfil': ['perfil', 'profile', 'responsavel'],
            'priority': ['priority', 'prioridade'],
            'observacao': ['observacao', 'observação', 'obs', 'notes'],
            'numero_chamado': ['numero_chamado', 'chamado', 'ticket'],
            'status': ['status', 'situacao']
        }
        
        for row_num, row in enumerate(csv_reader, start=2):  # começa em 2 por causa do header
            try:
                # Normalizar nomes das colunas
                normalized_row = {}
                for key, value in row.items():
                    if key.strip().lower():
                        # Encontrar o campo correspondente
                        for field, possible_names in field_mapping.items():
                            if key.strip().lower() in [name.lower() for name in possible_names]:
                                normalized_row[field] = value.strip()
                                break
                
                # Validar campos obrigatórios
                required_fields = ['title', 'imei', 'unidade', 'prazo', 'perfil']
                missing_fields = [field for field in required_fields if not normalized_row.get(field)]
                
                if missing_fields:
                    logger.warning(f"Linha {row_num}: Campos obrigatórios faltando: {missing_fields}")
                    continue
                
                # Criar TarefaCreate
                tarefa_create = TarefaCreate(
                    title=normalized_row['title'],
                    imei=normalized_row['imei'],
                    unidade=normalized_row['unidade'],
                    prazo=normalized_row['prazo'],
                    perfil=normalized_row['perfil'],
                    priority=normalized_row.get('priority', 'media'),
                    observacao=normalized_row.get('observacao'),
                    numero_chamado=normalized_row.get('numero_chamado'),
                    status=normalized_row.get('status', 'demanda')
                )
                
                tarefas_data.append(tarefa_create)
                
            except Exception as e:
                logger.error(f"Erro ao processar linha {row_num}: {str(e)}")
                continue
        
        if not tarefas_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nenhuma tarefa válida encontrada no CSV"
            )
        
        # Criar tarefas em massa
        service = TarefaService(db)
        tarefas_criadas = service.create_tarefas_bulk(tarefas_data)
        
        logger.info(f"Criadas {len(tarefas_criadas)} tarefas com sucesso")
        return tarefas_criadas
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao decodificar arquivo. Use codificação UTF-8."
        )
    except Exception as e:
        logger.error(f"Erro ao processar upload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )

@router.get("/tarefas", response_model=List[TarefaResponse])
async def get_tarefas(db: Session = Depends(get_db)):
    """
    Retorna todas as tarefas do Kanban
    """
    logger.info("Recebida requisição para listar todas as tarefas")
    try:
        service = TarefaService(db)
        tarefas = service.get_all_tarefas()
        logger.info(f"Retornando {len(tarefas)} tarefas")
        return tarefas
    except Exception as e:
        logger.error(f"Erro ao buscar tarefas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar tarefas: {str(e)}"
        )

@router.get("/tarefas/status/{status}", response_model=List[TarefaResponse])
async def get_tarefas_by_status(status: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por status
    Status válidos: demanda, a-fazer, em-andamento, erro, feito
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_status(status)
    return tarefas

@router.get("/tarefas/imei/{imei}", response_model=List[TarefaResponse])
async def get_tarefas_by_imei(imei: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por IMEI
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_imei(imei)
    return tarefas

@router.get("/tarefas/perfil/{perfil}", response_model=List[TarefaResponse])
async def get_tarefas_by_perfil(perfil: str, db: Session = Depends(get_db)):
    """
    Retorna tarefas filtradas por perfil
    """
    service = TarefaService(db)
    tarefas = service.get_tarefas_by_perfil(perfil)
    return tarefas

@router.get("/tarefas/{tarefa_id}", response_model=TarefaResponse)
async def get_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    """
    Retorna uma tarefa específica pelo ID
    """
    service = TarefaService(db)
    tarefa = service.get_tarefa_by_id(tarefa_id)
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    return tarefa

@router.post("/tarefas", response_model=TarefaResponse, status_code=status.HTTP_201_CREATED)
async def create_tarefa(tarefa_data: TarefaCreate, db: Session = Depends(get_db)):
    """
    Cria uma nova tarefa no Kanban
    """
    service = TarefaService(db)
    
    # Validação básica dos campos obrigatórios
    if not tarefa_data.title or not tarefa_data.imei or not tarefa_data.unidade or not tarefa_data.prazo or not tarefa_data.perfil:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campos obrigatórios: title, imei, unidade, prazo, perfil"
        )
    
    # Validação da prioridade
    if tarefa_data.priority not in ["baixa", "media", "alta"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prioridade inválida. Valores aceitos: baixa, media, alta"
        )
    
    # Validação do status inicial
    if tarefa_data.status not in ["demanda", "a-fazer", "em-andamento", "erro", "feito"]:
        tarefa_data.status = "demanda"  # Status padrão
    
    tarefa = service.create_tarefa(tarefa_data)
    return tarefa

@router.put("/tarefas/{tarefa_id}", response_model=TarefaResponse)
async def update_tarefa(tarefa_id: int, tarefa_data: TarefaUpdate, db: Session = Depends(get_db)):
    """
    Atualiza uma tarefa existente
    """
    service = TarefaService(db)
    tarefa = service.update_tarefa(tarefa_id, tarefa_data)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return tarefa

@router.patch("/tarefas/{tarefa_id}/status", response_model=TarefaResponse)
async def update_tarefa_status(tarefa_id: int, status_data: TarefaStatusUpdateRequest, db: Session = Depends(get_db)):
    """
    Atualiza apenas o status de uma tarefa (usado no drag and drop)
    """
    service = TarefaService(db)
    
    # Validação do status
    status_validos = ["demanda", "a-fazer", "em-andamento", "erro", "feito"]
    if status_data.status not in status_validos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status inválido. Valores aceitos: {', '.join(status_validos)}"
        )
    
    status_update = TarefaStatusUpdate(
        status=status_data.status,
        observacao=status_data.observacao
    )
    
    tarefa = service.update_tarefa_status(tarefa_id, status_update)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return tarefa

@router.patch("/tarefas/{tarefa_id}/observacao", response_model=TarefaResponse)
async def update_tarefa_observacao(tarefa_id: int, obs_data: TarefaObservacaoUpdateRequest, db: Session = Depends(get_db)):
    """
    Atualiza apenas a observação de uma tarefa
    """
    service = TarefaService(db)
    tarefa = service.get_tarefa_by_id(tarefa_id)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    tarefa.observacao = obs_data.observacao
    tarefa.data_atualizacao = datetime.utcnow()
    
    db.commit()
    db.refresh(tarefa)
    
    return tarefa

@router.put("/tarefas/{tarefa_id}/observacao", response_model=TarefaResponse)
async def update_observacao(tarefa_id: int, observacao_data: TarefaObservacaoUpdate, db: Session = Depends(get_db)):
    """
    Atualiza apenas a observação de uma tarefa
    """
    service = TarefaService(db)
    tarefa = service.update_observacao(tarefa_id, observacao_data)
    
    if not tarefa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return tarefa

@router.delete("/tarefas/{tarefa_id}")
async def delete_tarefa(tarefa_id: int, db: Session = Depends(get_db)):
    """
    Deleta uma tarefa
    """
    service = TarefaService(db)
    sucesso = service.delete_tarefa(tarefa_id)
    
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarefa com ID {tarefa_id} não encontrada"
        )
    
    return {"message": f"Tarefa {tarefa_id} deletada com sucesso"}

@router.get("/kanban/summary")
async def get_kanban_summary(db: Session = Depends(get_db)):
    """
    Retorna um resumo do Kanban com contagem de tarefas por status
    """
    service = TarefaService(db)
    
    summary = {
        "demanda": len(service.get_tarefas_by_status("demanda")),
        "a-fazer": len(service.get_tarefas_by_status("a-fazer")),
        "em-andamento": len(service.get_tarefas_by_status("em-andamento")),
        "erro": len(service.get_tarefas_by_status("erro")),
        "feito": len(service.get_tarefas_by_status("feito")),
        "total": len(service.get_all_tarefas())
    }
    
    return summary
