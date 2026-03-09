from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# SQLAlchemy model
Base = declarative_base()

class TarefaDB(Base):
    __tablename__ = "tarefas"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    imei = Column(String, nullable=False)
    unidade = Column(String, nullable=False)
    prazo = Column(String, nullable=False)
    observacao = Column(Text, nullable=True)
    priority = Column(String, default="media")
    perfil = Column(String, nullable=False)
    numero_chamado = Column(String, nullable=True)
    status = Column(String, default="demanda")
    data_criacao = Column(DateTime, default=datetime.utcnow)
    data_atualizacao = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic schemas
class TarefaBase(BaseModel):
    title: str
    imei: str
    unidade: str
    prazo: str
    observacao: Optional[str] = None
    priority: str = "media"
    perfil: str
    numero_chamado: Optional[str] = None
    status: str = "demanda"

class TarefaCreate(TarefaBase):
    pass

class TarefaUpdate(BaseModel):
    title: Optional[str] = None
    imei: Optional[str] = None
    unidade: Optional[str] = None
    prazo: Optional[str] = None
    observacao: Optional[str] = None
    priority: Optional[str] = None
    perfil: Optional[str] = None
    numero_chamado: Optional[str] = None
    status: Optional[str] = None

class TarefaInDB(TarefaBase):
    id: int
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True

class TarefaResponse(BaseModel):
    id: int
    title: str
    imei: str
    unidade: str
    prazo: str
    observacao: Optional[str] = None
    priority: str
    perfil: str
    numero_chamado: Optional[str] = None
    status: str
    data_criacao: datetime
    data_atualizacao: datetime

    class Config:
        orm_mode = True

class TarefaStatusUpdate(BaseModel):
    status: str
    observacao: Optional[str] = None

class TarefaDelete(BaseModel):
    id: int
