from typing import List, Dict, Optional, Union, Any
import json
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Table, MetaData, select, text, and_
import uuid

from app.models.cluster import ClusterDB, IMEIData, ClusterCreate, ClusterResponse
from app.database import engine, Base
from app.services.consultar_imei import ConsultaImeiService

class ClusterService:
    def __init__(self, db: Session):
        self.db = db
        self.imei_service = ConsultaImeiService("214741", "214741")  # Credenciais padrão

    def _get_cluster_table(self, cluster_id: str) -> Table:
        """Retorna a tabela de um cluster específico"""
        return ClusterDB.create_cluster_table(cluster_id)

    def create_cluster(self, nome: str, imeis: List[Union[str, Dict[str, Any]]], descricao: str = "") -> ClusterResponse:
        """
        Cria um novo cluster com os IMEIs fornecidos
        
        Args:
            nome: Nome do cluster
            imeis: Lista de IMEIs (como strings) ou dicionários com dados do IMEI
            descricao: Descrição opcional do cluster
            
        Returns:
            ClusterResponse: Dados do cluster criado
        """
        print("\n[CLUSTER_DEBUG] Iniciando criação de cluster")
        print(f"[CLUSTER_DEBUG] Nome do cluster: {nome}")
        print(f"[CLUSTER_DEBUG] Total de IMEIs a processar: {len(imeis) if imeis else 0}")
        # Cria o registro do cluster na tabela mestre
        cluster = ClusterDB(
            nome=nome,
            descricao=descricao
        )
        
        # Adiciona ao banco para obter o ID
        self.db.add(cluster)
        self.db.commit()
        self.db.refresh(cluster)
        
        # Cria a tabela específica para este cluster
        cluster_table = self._get_cluster_table(str(cluster.id))
        cluster_table.create(bind=engine, checkfirst=True)
        
        # Obtém os dados dos IMEIs e prepara para inserção
        imeis_to_insert = []
        for imei_item in imeis:
            try:
                # Se for um dicionário, extrai os dados do IMEI
                if isinstance(imei_item, dict):
                    print("\n[CLUSTER_DEBUG] Processando IMEI:", imei_item)
                    imei = imei_item.get('imei', '').strip()
                    if not imei:
                        print("[CLUSTER_DEBUG] IMEI vazio, pulando...")
                        continue
                    
                    # Se já tiver dados do IMEI, usa-os, senão consulta o serviço
                    if any(key in imei_item for key in ['modelo', 'status', 'observacao', 'fabricante']):
                        print(f"\n[DEBUG] Processando imei_item:", imei_item)
                        
                        # Primeiro tenta pegar o status diretamente do item
                        status = imei_item.get('status')
                        print(f"[CLUSTER_DEBUG] Status direto do imei_item: {status}")
                        
                        # Log de todos os campos para debug
                        print("[CLUSTER_DEBUG] Campos disponíveis no imei_item:", list(imei_item.keys()))
                        if 'dados_brutos' in imei_item and isinstance(imei_item['dados_brutos'], dict):
                            print("[CLUSTER_DEBUG] Campos em dados_brutos:", list(imei_item['dados_brutos'].keys()))
                        
                        # Se não encontrou, tenta pegar dos dados brutos
                        if not status and 'dados_brutos' in imei_item:
                            print(f"[DEBUG] Procurando em dados_brutos:", imei_item.get('dados_brutos'))
                            if isinstance(imei_item['dados_brutos'], dict):
                                status = imei_item['dados_brutos'].get('status')
                                print(f"[DEBUG] Status encontrado em dados_brutos: {status}")
                        
                        # Se ainda não encontrou, verifica se há um campo 'status' em maiúsculas
                        if not status and 'dados_brutos' in imei_item and isinstance(imei_item['dados_brutos'], dict):
                            status = imei_item['dados_brutos'].get('STATUS')
                            print(f"[DEBUG] Procurando por 'STATUS' em maiúsculas: {status}")
                        
                        # Se ainda não tiver status, usa 'DESCONHECIDO'
                        status = status or 'DESCONHECIDO'
                        print(f"[CLUSTER_DEBUG] Status final a ser salvo: {status}")
                        
                        # Log do objeto final que será salvo
                        print("[CLUSTER_DEBUG] Dados completos a serem salvos:", {
                            'imei': imei,
                            'modelo': imei_item.get('modelo'),
                            'status': status,
                            'observacao': imei_item.get('observacao')
                        })
                        
                        # Garante que o status não seja nulo ou vazio
                        status_final = str(status).strip() if status else 'DESCONHECID'
                        print(f"[STATUS_DEBUG] Status final antes de salvar: '{status_final}'")
                        
                        # Prepara os dados para inserção
                        imei_data = {
                            'imei': imei,
                            'modelo': imei_item.get('modelo'),
                            'status': status_final,  # Usa o status já processado
                            'observacao': imei_item.get('observacao'),
                            'fabricante': imei_item.get('fabricante'),
                            'tipo_ativo': imei_item.get('tipo_ativo'),
                            'empresa': imei_item.get('empresa'),
                            'numero_chamado': imei_item.get('numero_chamado'),
                            'localizacao': imei_item.get('localizacao'),
                            'dados_brutos': imei_item.get('dados_brutos', imei_item),  # Mantém como dicionário, será convertido pelo SQLAlchemy
                            'data_inclusao': datetime.utcnow(),
                            'data_atualizacao': datetime.utcnow()
                        }
                        
                        # Log dos dados que serão salvos
                        print(f"[CLUSTER_SAVE] Salvando no banco: {imei_data}")
                    else:
                        # Se não tiver todos os dados, consulta o serviço
                        dados = self.imei_service.consultar_imei(imei)
                        
                        # Obtém o status, priorizando a fonte correta e garantindo que não seja nulo
                        status = str(imei_item.get('status') or (dados.get('status') if dados else None) or 'DESCONHECIDO').strip()
                        print(f"[STATUS_DEBUG] Status processado: '{status}'")
                        
                        imei_data = {
                            'imei': imei,
                            'modelo': imei_item.get('modelo', dados.get('modelo') if dados else None),
                            'status': status,  # Usa o status já processado
                            'observacao': imei_item.get('observacao'),
                            'fabricante': imei_item.get('fabricante', dados.get('fabricante') if dados else None),
                            'tipo_ativo': imei_item.get('tipo_ativo', dados.get('tipo_ativo') if dados else None),
                            'empresa': imei_item.get('empresa', dados.get('empresa') if dados else None),
                            'numero_chamado': imei_item.get('numero_chamado', dados.get('numero_chamado') if dados else None),
                            'localizacao': imei_item.get('localizacao', dados.get('localizacao') if dados else None),
                            'dados_brutos': {**dados, **imei_item} if dados else imei_item,  # Mantém como dicionário
                            'data_inclusao': datetime.utcnow(),
                            'data_atualizacao': datetime.utcnow()
                        }
                        
                        print(f"[CLUSTER_SAVE] Salvando com dados do serviço: {imei_data}")
                else:
                    # Se for apenas uma string (IMEI), consulta o serviço
                    imei = str(imei_item).strip()
                    if not imei:
                        continue
                        
                    dados = self.imei_service.consultar_imei(imei)
                    imei_data = {
                        'imei': imei,
                        'modelo': dados.get('modelo'),
                        'status': dados.get('status') or 'DESCONHECIDO',
                        'observacao': None,
                        'fabricante': dados.get('fabricante'),
                        'tipo_ativo': dados.get('tipo_ativo'),
                        'empresa': dados.get('empresa'),
                        'numero_chamado': dados.get('numero_chamado'),
                        'localizacao': dados.get('localizacao'),
                        'dados_brutos': dados,  # Mantém como dicionário
                        'data_inclusao': datetime.utcnow(),
                        'data_atualizacao': datetime.utcnow()
                    }
                
                imeis_to_insert.append(imei_data)
            except Exception as e:
                print(f"Erro ao processar IMEI {imei_item}: {str(e)}")
        
        # Insere os IMEIs na tabela do cluster
        if imeis_to_insert:
            print("\n[DB_DEBUG] Inserindo IMEIs no banco de dados")
            try:
                with engine.begin() as connection:
                    # Processa cada IMEI individualmente
                    for imei_data in imeis_to_insert:
                        # Remove o ID para que o banco de dados gere um novo
                        imei_data.pop('id', None)
                        
                        # Garante que dados_brutos seja um dicionário
                        if 'dados_brutos' in imei_data and isinstance(imei_data['dados_brutos'], str):
                            try:
                                # Tenta converter a string JSON de volta para dicionário
                                imei_data['dados_brutos'] = json.loads(imei_data['dados_brutos'])
                            except json.JSONDecodeError:
                                # Se não for um JSON válido, mantém o valor original
                                pass
                        
                        # Garante que o status não seja nulo
                        if 'status' not in imei_data or not imei_data['status']:
                            imei_data['status'] = 'DESCONHECIDO'
                        
                        # Prepara a declaração de inserção
                        stmt = cluster_table.insert().values(**imei_data)
                        
                        # Executa a inserção
                        result = connection.execute(stmt)
                        print(f"[DB_DEBUG] IMEI {imei_data.get('imei')} inserido com sucesso")
                        
                        # Verifica se os dados foram realmente inseridos
                        select_stmt = select(cluster_table).where(
                            cluster_table.c.imei == imei_data['imei']
                        )
                        inserted_data = connection.execute(select_stmt).mappings().fetchone()

                        if inserted_data:
                            print("[DB_DEBUG] Dados recuperados após inserção:", dict(inserted_data))
                        else:
                            print("[DB_DEBUG] Aviso: Não foi possível verificar a inserção do IMEI", imei_data.get('imei'))
            
            except Exception as e:
                print(f"[DB_DEBUG] Erro ao inserir no banco de dados: {str(e)}")
                raise
                
        # Atualiza a contagem total de IMEIs
        cluster.total_imeis = len(imeis_to_insert)
        try:
            self.db.commit()
            self.db.refresh(cluster)
            print("[DB_DEBUG] Cluster atualizado com sucesso no banco de dados")
        except Exception as e:
            print(f"[DB_DEBUG] Erro ao atualizar o cluster: {str(e)}")
            self.db.rollback()
            raise
        
        return self._to_cluster_response(cluster)

    def get_cluster(self, cluster_id: str) -> Optional[Dict]:
        """Obtém os dados de um cluster específico"""
        return self.get_cluster_with_imei_data(cluster_id, detalhado=False)

    def list_clusters(self) -> List[Dict]:
        """Lista todos os clusters"""
        clusters = self.db.query(ClusterDB).all()
        return [{
            "id": str(cluster.id),
            "nome": cluster.nome,
            "descricao": cluster.descricao,
            "data_criacao": cluster.data_criacao.isoformat(),
            "total_imeis": cluster.total_imeis or 0
        } for cluster in clusters]
    
    def get_imeis_from_cluster(self, cluster_id: str) -> List[Dict]:
        """Obtém todos os IMEIs de um cluster específico"""
        # Verifica se o cluster existe
        cluster = self.db.query(ClusterDB).filter(ClusterDB.id == cluster_id).first()
        if not cluster:
            return []
            
        # Obtém a tabela do cluster
        cluster_table = self._get_cluster_table(cluster_id)
        
        # Cria uma conexão e executa a consulta usando SQLAlchemy Core
        with engine.connect() as conn:
            # Usa select() corretamente
            stmt = select(
                cluster_table.c.imei, 
                cluster_table.c.modelo, 
                cluster_table.c.status, 
                cluster_table.c.fabricante
            )
            result = conn.execute(stmt)
            return [dict(row) for row in result.mappings()]

    def get_cluster_with_imei_data(self, cluster_id: str, detalhado: bool = False) -> Optional[Dict]:
        """
        Obtém os dados de um cluster incluindo os dados dos IMEIs usando uma única consulta SQL
        
        Args:
            cluster_id: ID do cluster a ser consultado
            detalhado: Se True, retorna todos os campos dos IMEIs
                
        Returns:
            Dict com os dados do cluster e informações dos IMEIs, ou None se não encontrado
        """
        try:
            # Primeiro, busca os metadados básicos do cluster
            cluster = self.db.query(
                ClusterDB.id,
                ClusterDB.nome,
                ClusterDB.descricao,
                ClusterDB.data_criacao,
                ClusterDB.total_imeis
            ).filter(ClusterDB.id == cluster_id).first()
            
            if not cluster:
                return None

            # Prepara a resposta base
            result = {
                "id": str(cluster.id),
                "nome": cluster.nome,
                "descricao": cluster.descricao or "",
                "data_criacao": cluster.data_criacao.isoformat(),
                "total_imeis": cluster.total_imeis or 0,
                "imeis": [],
                "detalhes_imeis": {}
            }

            # Se não houver IMEIs, retorna só os metadados
            if not cluster.total_imeis:
                return result

            # Monta o nome da tabela dinâmica
            table_name = f'cluster_{str(cluster.id).replace("-", "_")}'
            
            # Verifica se a tabela existe
            table_exists = self.db.execute(
                text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name)"),
                {"table_name": table_name}
            ).scalar()
            
            if not table_exists:
                logger.warning(f"Tabela {table_name} não encontrada para o cluster {cluster_id}")
                return result
            
            # Define os campos a serem buscados
            campos = ['imei', 'modelo', 'status', 'fabricante']
            
            if detalhado:
                campos.extend([
                    'tipo_ativo', 'empresa', 'numero_chamado', 
                    'localizacao', 'data_inclusao', 'data_atualizacao'
                ])
            
            # Monta e executa a consulta SQL com tratamento de erros
            campos_sql = ', '.join(campos)
            query = text(f'''
                SELECT {campos_sql} 
                FROM {table_name}
                WHERE imei IS NOT NULL
                ORDER BY data_inclusao DESC, imei
            ''')
            
            with self.db.connection() as conn:
                try:
                    imeis = conn.execute(query).fetchall()
                    
                    # Processa os resultados
                    for imei in imeis:
                        imei_dict = {
                            'imei': imei.imei,
                            'modelo': imei.modelo,
                            'status': imei.status,
                            'fabricante': imei.fabricante
                        }
                        
                        if detalhado:
                            imei_dict.update({
                                'tipo_ativo': imei.tipo_ativo,
                                'empresa': imei.empresa,
                                'numero_chamado': imei.numero_chamado,
                                'localizacao': imei.localizacao,
                                'data_inclusao': imei.data_inclusao.isoformat() if imei.data_inclusao else None,
                                'data_atualizacao': imei.data_atualizacao.isoformat() if imei.data_atualizacao else None
                            })
                        
                        result['detalhes_imeis'][imei.imei] = imei_dict
                        result['imeis'].append(imei.imei)
                    
                    # Atualiza a contagem real de IMEIs encontrados
                    result['total_imeis'] = len(result['imeis'])
                    
                except Exception as e:
                    logger.error(f"Erro ao buscar IMEIs do cluster {cluster_id}: {str(e)}", exc_info=True)
                    # Retorna os dados básicos mesmo em caso de erro na busca dos IMEIs
                    return result
            
            return result
            
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar dados do cluster {cluster_id}: {str(e)}", exc_info=True)
            return None

    def _to_cluster_response(self, cluster: ClusterDB) -> Dict:
        """Converte um ClusterDB para um dicionário de resposta"""
        return {
            "id": str(cluster.id),
            "nome": cluster.nome,
            "descricao": cluster.descricao,
            "data_criacao": cluster.data_criacao.isoformat(),
            "total_imeis": cluster.total_imeis or 0
        }