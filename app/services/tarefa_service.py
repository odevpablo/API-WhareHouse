from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from app.models.tarefa import TarefaDB, TarefaCreate, TarefaUpdate, TarefaStatusUpdate
from datetime import datetime

class TarefaService:
    def __init__(self, db: Session):
        self.db = db

    def create_tarefa(self, tarefa_data: TarefaCreate) -> TarefaDB:
        """Cria uma nova tarefa"""
        tarefa = TarefaDB(**tarefa_data.dict())
        self.db.add(tarefa)
        self.db.commit()
        self.db.refresh(tarefa)
        return tarefa

    def get_all_tarefas(self) -> List[TarefaDB]:
        """Retorna todas as tarefas ordenadas por data de criação"""
        return self.db.query(TarefaDB).order_by(desc(TarefaDB.data_criacao)).all()

    def get_tarefa_by_id(self, tarefa_id: int) -> Optional[TarefaDB]:
        """Retorna uma tarefa pelo ID"""
        return self.db.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()

    def update_tarefa(self, tarefa_id: int, tarefa_data: TarefaUpdate) -> Optional[TarefaDB]:
        """Atualiza uma tarefa"""
        tarefa = self.get_tarefa_by_id(tarefa_id)
        if not tarefa:
            return None
        
        update_data = tarefa_data.dict(exclude_unset=True)
        update_data['data_atualizacao'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(tarefa, field, value)
        
        self.db.commit()
        self.db.refresh(tarefa)
        return tarefa

    def update_tarefa_status(self, tarefa_id: int, status_data: TarefaStatusUpdate) -> Optional[TarefaDB]:
        """Atualiza apenas o status e observação de uma tarefa"""
        tarefa = self.get_tarefa_by_id(tarefa_id)
        if not tarefa:
            return None
        
        tarefa.status = status_data.status
        tarefa.data_atualizacao = datetime.utcnow()
        
        if status_data.observacao is not None:
            tarefa.observacao = status_data.observacao
        
        self.db.commit()
        self.db.refresh(tarefa)
        return tarefa

    def delete_tarefa(self, tarefa_id: int) -> bool:
        """Deleta uma tarefa"""
        tarefa = self.get_tarefa_by_id(tarefa_id)
        if not tarefa:
            return False
        
        self.db.delete(tarefa)
        self.db.commit()
        return True

    def get_tarefas_by_status(self, status: str) -> List[TarefaDB]:
        """Retorna tarefas por status"""
        return self.db.query(TarefaDB).filter(TarefaDB.status == status).order_by(desc(TarefaDB.data_criacao)).all()

    def get_tarefas_by_imei(self, imei: str) -> List[TarefaDB]:
        """Retorna tarefas por IMEI"""
        return self.db.query(TarefaDB).filter(TarefaDB.imei == imei).order_by(desc(TarefaDB.data_criacao)).all()

    def get_tarefas_by_perfil(self, perfil: str) -> List[TarefaDB]:
        """Retorna tarefas por perfil"""
        return self.db.query(TarefaDB).filter(TarefaDB.perfil == perfil).order_by(desc(TarefaDB.data_criacao)).all()
