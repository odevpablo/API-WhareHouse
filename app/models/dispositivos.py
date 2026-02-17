from sqlalchemy import Column, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# SQLAlchemy model
Base = declarative_base()

class DispositivoDB(Base):
    __tablename__ = "dispositivos"
    
    id = Column(String, primary_key=True, index=True)
    imei = Column(String, unique=True, index=True, nullable=False)
    modelo = Column(String, nullable=True)
    status = Column(String, nullable=True)
    dados_brutos = Column(JSON, nullable=True)
    data_criacao = Column(String, default=datetime.utcnow)
    data_atualizacao = Column(String, default=datetime.utcnow, onupdate=datetime.utcnow)

# Pydantic schemas
class DispositivoBase(BaseModel):
    imei: str
    modelo: Optional[str] = None
    status: Optional[str] = None
    dados_brutos: Optional[Dict[str, Any]] = None

class DispositivoCreate(DispositivoBase):
    pass

class DispositivoUpdate(DispositivoBase):
    pass

class DispositivoInDB(DispositivoBase):
    id: str
    data_criacao: str
    data_atualizacao: str

    class Config:
        from_attributes = True

class DispositivoConsulta(BaseModel):
    imeis: list[str]