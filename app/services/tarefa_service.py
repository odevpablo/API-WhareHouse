from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.models.tarefa import TarefaDB, TarefaCreate, TarefaUpdate, TarefaStatusUpdate, TarefaResponse
from datetime import datetime

class TarefaService:
    def __init__(self, db: Session):
        self.db = db

    def create_tarefa(self, tarefa_data: TarefaCreate) -> TarefaResponse:
        """Cria uma nova tarefa"""
        tarefa = TarefaDB(**tarefa_data.dict())
        self.db.add(tarefa)
        self.db.commit()
        self.db.refresh(tarefa)
        return TarefaResponse.from_orm(tarefa)

    def get_all_tarefas(self) -> List[TarefaResponse]:
        """Retorna todas as tarefas ordenadas por data de criação"""
        tarefas_db = self.db.query(TarefaDB).order_by(desc(TarefaDB.data_criacao)).all()
        return [TarefaResponse.from_orm(tarefa) for tarefa in tarefas_db]

    def get_tarefa_by_id(self, tarefa_id: int) -> Optional[TarefaResponse]:
        """Retorna uma tarefa pelo ID"""
        tarefa = self.db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
        return TarefaResponse.from_orm(tarefa) if tarefa else None

    def update_tarefa(self, tarefa_id: int, tarefa_data: TarefaUpdate) -> Optional[TarefaResponse]:
        """Atualiza uma tarefa"""
        tarefa = self.db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
        if not tarefa:
            return None
        
        update_data = tarefa_data.dict(exclude_unset=True)
        update_data['data_atualizacao'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(tarefa, field, value)
        
        self.db.commit()
        self.db.refresh(tarefa)
        return TarefaResponse.from_orm(tarefa)

    def update_tarefa_status(self, tarefa_id: int, status_data: TarefaStatusUpdate) -> Optional[TarefaResponse]:
        """Atualiza apenas o status e observação de uma tarefa"""
        tarefa = self.db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
        if not tarefa:
            return None
        
        tarefa.status = status_data.status
        tarefa.data_atualizacao = datetime.utcnow()
        
        if status_data.observacao is not None:
            tarefa.observacao = status_data.observacao
        
        self.db.commit()
        self.db.refresh(tarefa)
        return TarefaResponse.from_orm(tarefa)

    def delete_tarefa(self, tarefa_id: int) -> bool:
        """Deleta uma tarefa"""
        tarefa = self.db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
        if not tarefa:
            return False
        
        self.db.delete(tarefa)
        self.db.commit()
        return True

    def get_tarefas_by_status(self, status: str) -> List[TarefaResponse]:
        """Retorna tarefas por status"""
        tarefas_db = self.db.query(TarefaDB).filter(TarefaDB.status == status).order_by(desc(TarefaDB.data_criacao)).all()
        return [TarefaResponse.from_orm(tarefa) for tarefa in tarefas_db]

    def get_tarefas_by_imei(self, imei: str) -> List[TarefaResponse]:
        """Retorna tarefas por IMEI"""
        tarefas_db = self.db.query(TarefaDB).filter(TarefaDB.imei == imei).order_by(desc(TarefaDB.data_criacao)).all()
        return [TarefaResponse.from_orm(tarefa) for tarefa in tarefas_db]

    def get_tarefas_by_perfil(self, perfil: str) -> List[TarefaResponse]:
        """Retorna tarefas por perfil"""
        tarefas_db = self.db.query(TarefaDB).filter(TarefaDB.perfil == perfil).order_by(desc(TarefaDB.data_criacao)).all()
        return [TarefaResponse.from_orm(tarefa) for tarefa in tarefas_db]
