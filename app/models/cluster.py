from sqlalchemy import Column, String, JSON, DateTime, Integer, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Type
from datetime import datetime
import uuid

Base = declarative_base()

class ClusterDB(Base):
    """Tabela mestre que armazena metadados sobre os clusters"""
    __tablename__ = "clusters"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    nome = Column(String(255), nullable=False)
    descricao = Column(String(500), nullable=True)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    total_imeis = Column(Integer, default=0)
    
    # Método para criar uma tabela dinâmica para um cluster
    @classmethod
    def create_cluster_table(cls, cluster_id: str) -> Table:
        """Cria uma tabela para armazenar os IMEIs de um cluster específico"""
        table_name = f'cluster_{cluster_id.replace("-", "_")}'
        print(f"\n[TABLE_DEBUG] Criando tabela: {table_name}")
        
        # Define as colunas da tabela
        columns = [
            Column('id', String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
            Column('imei', String(20), unique=True, index=True, nullable=False, comment='Número do IMEI do dispositivo'),
            Column('modelo', String(100), nullable=True, comment='Modelo do dispositivo'),
            # Alterado para nullable=True para permitir valores nulos
            # e garantindo que o valor padrão seja aplicado corretamente
            Column('status', String(50), nullable=True, server_default='DESCONHECIDO', comment='Status do dispositivo (ex: ATIVO, INATIVO, QUEBRADO)'),
            Column('observacao', String(500), nullable=True, comment='Observações adicionais sobre o dispositivo'),
            Column('fabricante', String(100), nullable=True, comment='Fabricante do dispositivo'),
            Column('tipo_ativo', String(50), nullable=True, comment='Tipo de ativo (ex: SMARTPHONE, TABLET, ETC)'),
            Column('empresa', String(200), nullable=True, comment='Empresa proprietária do dispositivo'),
            Column('numero_chamado', String(50), nullable=True, comment='Número do chamado associado'),
            Column('localizacao', String(200), nullable=True, comment='Localização física do dispositivo'),
            Column('dados_brutos', JSON, nullable=True, comment='Dados brutos adicionais em formato JSON'),
            Column('data_inclusao', DateTime, default=datetime.utcnow, comment='Data de inclusão do registro'),
            Column('data_atualizacao', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='Data da última atualização')
        ]
        
        # Cria a tabela
        table = Table(
            table_name,
            MetaData(),
            *columns,
            extend_existing=True
        )
        
        # Log da estrutura da tabela
        print(f"[TABLE_DEBUG] Estrutura da tabela {table_name}:")
        for column in columns:
            print(f"  - {column.name}: {column.type} (nullable={column.nullable}, default={column.default})")
            
        return table

# Modelos Pydantic para validação de entrada/saída
class IMEIData(BaseModel):
    imei: str
    modelo: Optional[str] = None
    status: Optional[str] = None
    observacao: Optional[str] = Field(None, description="Campo para observações adicionais")
    fabricante: Optional[str] = None
    tipo_ativo: Optional[str] = None
    empresa: Optional[str] = None
    numero_chamado: Optional[str] = None
    localizacao: Optional[str] = None
    dados_brutos: Optional[Dict[str, Any]] = None

class ClusterCreate(BaseModel):
    nome: str = Field(..., description="Nome descritivo para o cluster")
    descricao: Optional[str] = Field(None, description="Descrição opcional do cluster")
    imeis: List[IMEIData] = Field(..., description="Lista de IMEIs com seus dados")

class ClusterResponse(ClusterCreate):
    id: str = Field(..., description="ID único do cluster")
    data_criacao: datetime = Field(..., description="Data de criação do cluster")
    total_imeis: int = Field(..., description="Total de IMEIs no cluster")
    
    class Config:
        from_attributes = True
