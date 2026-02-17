import io
import json
import qrcode
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from app.services.cluster_service import ClusterService
from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.consultar_imei import ConsultaImeiService
from app.services.cluster_service import ClusterService
from app.services.csv_service import CsvService
from app.models.dispositivos import DispositivoConsulta
from app.models.cluster import ClusterCreate, ClusterResponse
import zipfile

router = APIRouter(
    tags=["IMEI"],
    responses={404: {"description": "Não encontrado"}},
)

# Configuração
USUARIO_IMEI = "214741"
SENHA_IMEI = "214741"

# Inicializa os serviços
imei_service = ConsultaImeiService(USUARIO_IMEI, SENHA_IMEI)

@router.get("/", response_model=Dict[str, Any])
def root():
    """
    Rota raiz da API
    
    Retorna:
        dict: Dicionário com os endpoints disponíveis e seus detalhes
    """
    return {
        "message": "Bem-vindo à API de Consulta de IMEI",
        "endpoints": {
            "consultar_imeis": {
                "method": "POST",
                "path": "/consultar",
                "description": "Consulta um ou mais IMEIs no sistema de inventário"
            },
            "processar_csv": {
                "method": "POST",
                "path": "/processar-csv",
                "description": "Processa um arquivo CSV com IMEIs e opcionalmente cria um cluster",
                "parameters": [
                    {
                        "name": "file",
                        "type": "file",
                        "required": True,
                        "description": "Arquivo CSV contendo a coluna IMEI"
                    },
                    {
                        "name": "criar_cluster_automatico",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "description": "Se True, cria automaticamente um cluster com os IMEIs encontrados"
                    },
                    {
                        "name": "nome_cluster",
                        "type": "string",
                        "required": False,
                        "default": "Cluster gerado a partir de CSV",
                        "description": "Nome do cluster a ser criado"
                    },
                    {
                        "name": "descricao_cluster",
                        "type": "string",
                        "required": False,
                        "default": "",
                        "description": "Descrição opcional para o cluster"
                    }
                ]
            },
            "criar_cluster": {
                "method": "POST",
                "path": "/clusters",
                "description": "Cria um novo cluster de IMEIs"
            },
            "listar_clusters": {
                "method": "GET",
                "path": "/clusters",
                "description": "Lista todos os clusters criados"
            },
            "obter_cluster": {
                "method": "GET",
                "path": "/clusters/{cluster_id}",
                "description": "Obtém os dados de um cluster específico"
            },
            "qrcode_imei": {
                "method": "GET",
                "path": "/qrcode/{imei}",
                "description": "Gera um QR Code com os dados do IMEI consultado"
            },
            "qrcode_cluster": {
                "method": "GET",
                "path": "/clusters/{cluster_id}/qrcode",
                "description": "Gera um QR Code com os dados do cluster"
            }
        }
    }

@router.post("/consultar", response_model=Dict[str, Any])
def consultar_imei(consulta: DispositivoConsulta):
    """
    Consulta um ou mais IMEIs no sistema de inventário
    
    - **imeis**: Lista de números IMEI para consulta
    """
    try:
        resultados = imei_service.consultar_multiplos_imeis(consulta.imeis)
        return {
            "status": "sucesso",
            "total_consultas": len(consulta.imeis),
            "resultados": resultados
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar IMEIs: {str(e)}"
        )

def generate_qr_code(data: Dict, size: int = 10) -> bytes:
    """Gera um QR Code a partir de um dicionário de dados"""
    try:
        # Conta a quantidade de aparelhos por modelo
        modelos = {}
        for imei_info in data.get('imeis', []):
            modelo = imei_info.get('modelo', 'Desconhecido')
            imei = imei_info.get('imei', '')
            if modelo not in modelos:
                modelos[modelo] = {
                    'quantidade': 0,
                    'imeis': []
                }
            modelos[modelo]['quantidade'] += 1
            modelos[modelo]['imeis'].append(imei)
        
        # Limita a quantidade de IMEIs por modelo para não exceder o tamanho máximo
        for modelo in modelos:
            modelos[modelo]['imeis'] = modelos[modelo]['imeis'][:5]  # Limita a 5 IMEIs por modelo
        
        # Cria a estrutura de dados otimizada
        limited_data = {
            'id': data.get('id'),
            'nome': data.get('nome', '')[:50],  # Limita o tamanho do nome
            'total_imeis': len(data.get('imeis', [])),
            'data_criacao': data.get('data_criacao'),
            'modelos': modelos,
            'total_modelos': len(modelos)
        }
        
        # Converte para JSON compactado (sem espaços extras)
        json_data = json.dumps(limited_data, ensure_ascii=False, separators=(',', ':'))
        
        # Verifica se os dados ainda são muito grandes
        if len(json_data.encode('utf-8')) > 2953:  # Limite aproximado para versão 40 com correção L
            # Se for muito grande, remove a lista de IMEIs e mantém apenas a contagem
            for modelo in modelos:
                modelos[modelo].pop('imeis', None)
            
            limited_data['modelos'] = modelos
            limited_data['mensagem'] = 'Lista de IMEIs muito grande, exibindo apenas contagem'
            json_data = json.dumps(limited_data, ensure_ascii=False, separators=(',', ':'))
        
        # Cria o QR Code com versão fixa máxima e correção de erro alta
        qr = qrcode.QRCode(
            version=40,  # Versão máxima
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Máxima correção de erro
            box_size=size,
            border=4,
        )
        qr.add_data(json_data)
        qr.make(fit=False)  # Não ajustar, pois já definimos a versão máxima
        
        # Cria a imagem do QR Code
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salva a imagem em memória
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        return img_byte_arr.getvalue()
        
    except Exception as e:
        # Em caso de erro, gera um QR code com mensagem de erro
        error_qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        error_qr.add_data(f"Erro: {str(e)[:100]}")
        error_qr.make(fit=True)
        error_img = error_qr.make_image(fill_color="black", back_color="white")
        error_byte_arr = io.BytesIO()
        error_img.save(error_byte_arr, format='PNG')
        return error_byte_arr.getvalue()
    return img_byte_arr.getvalue()

@router.get("/qrcode/{imei}", response_class=Response)
def get_qrcode_imei(imei: str):
    """
    Gera um QR Code com os dados do IMEI consultado
    
    - **imei**: Número do IMEI para consulta
    """
    try:
        # Consulta o IMEI
        resultado = imei_service.consultar_imei(imei)
        
        # Gera o QR Code
        qr_code = generate_qr_code(resultado)
        
        # Retorna a imagem do QR Code
        return Response(
            content=qr_code,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=imei_{imei}_qrcode.png"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar QR Code: {str(e)}"
        )

class ProcessarCSVResponse(BaseModel):
    message: str
    total_imeis_unicos: int
    total_registros: int
    cluster_id: Optional[str] = None
    cluster_nome: Optional[str] = None
    

import logging

# Configura o logger para o módulo de rotas
logger = logging.getLogger(__name__)

@router.post("/processar-csv", response_model=ProcessarCSVResponse)
async def processar_csv(
    file: UploadFile = File(...),
    criar_cluster_automatico: bool = Query(True, description="Criar cluster automaticamente com os IMEIs encontrados"),
    nome_cluster: str = Query("Cluster gerado a partir de CSV", description="Nome do cluster a ser criado"),
    descricao_cluster: str = Query("", description="Descrição opcional para o cluster"),
    db: Session = Depends(get_db)
):
    """
    Processa um arquivo CSV contendo IMEIs, agrupa os registros por IMEI e opcionalmente cria um cluster.
    
    O arquivo deve conter uma coluna chamada 'IMEI' (case insensitive).
    """
    logger.info(f"Iniciando processamento do arquivo: {file.filename}")
    logger.debug(f"Parâmetros - criar_cluster_automatico: {criar_cluster_automatico}, nome_cluster: {nome_cluster}")
    
    if not file.filename or not (file.filename.lower().endswith('.csv') or file.filename.lower().endswith('.zip')):
        error_msg = f"Tipo de arquivo inválido. Apenas arquivos CSV ou ZIP (contendo CSV) são aceitos. Arquivo recebido: {file.filename}"
        logger.error(error_msg)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # Processamento em streaming para CSV e suporte a ZIP
        logger.debug("Iniciando leitura do arquivo (stream)")

        if not file.filename:
            error_msg = "Arquivo não informado"
            logger.error(error_msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

        filename_lower = file.filename.lower()

        csv_service = CsvService()
        logger.debug(f"Detectando tipo de arquivo para: {file.filename}")

        # Garantir ponteiro no início
        try:
            file.file.seek(0)
        except Exception:
            pass

        if filename_lower.endswith('.zip'):
            logger.info("Arquivo ZIP recebido. Procurando CSV interno.")
            try:
                with zipfile.ZipFile(file.file) as zf:
                    # Escolhe o primeiro arquivo .csv dentro do ZIP
                    csv_names = [n for n in zf.namelist() if n.lower().endswith('.csv')]
                    if not csv_names:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="O arquivo ZIP não contém um CSV"
                        )
                    inner_name = csv_names[0]
                    logger.debug(f"Processando CSV interno: {inner_name}")
                    with zf.open(inner_name, 'r') as inner_bin:
                        # Primeiro tenta UTF-8 com BOM; se falhar, tenta latin-1
                        try:
                            text_stream = io.TextIOWrapper(inner_bin, encoding='utf-8-sig', newline='')
                            imei_groups, headers = csv_service.process_csv_stream(text_stream)
                        except UnicodeDecodeError:
                            inner_bin.seek(0)
                            text_stream = io.TextIOWrapper(inner_bin, encoding='latin-1', newline='')
                            imei_groups, headers = csv_service.process_csv_stream(text_stream)
            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Erro ao ler ZIP: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)
        else:
            # Trata como CSV puro, usando stream
            logger.info("Arquivo CSV recebido. Processando via stream.")
            try:
                # Usa UTF-8 com BOM como padrão, com fallback para latin-1
                try:
                    text_stream = io.TextIOWrapper(file.file, encoding='utf-8-sig', newline='')
                    imei_groups, headers = csv_service.process_csv_stream(text_stream)
                except UnicodeDecodeError:
                    try:
                        file.file.seek(0)
                    except Exception:
                        pass
                    text_stream = io.TextIOWrapper(file.file, encoding='latin-1', newline='')
                    imei_groups, headers = csv_service.process_csv_stream(text_stream)
            except Exception as e:
                error_msg = f"Erro inesperado ao processar o CSV: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)

        logger.debug(f"CSV processado com sucesso. {len(imei_groups)} IMEIs únicos encontrados")
        
        # Prepara a resposta
        total_imeis = len(imei_groups)
        total_registros = sum(len(registros) for registros in imei_groups.values())
        
        # Cria o cluster automaticamente se solicitado
        cluster_id = None
        cluster_nome = None

        imeis_para_cluster = []

        for imei, registros in imei_groups.items():

    # 🔹 Normaliza CSV
            dados_csv = registros[0] if isinstance(registros, list) and registros else registros
            if not isinstance(dados_csv, dict):
                dados_csv = {"imei": imei}

            try:
                # 🔹 Consulta API
                resposta_api = imei_service.consultar_por_imei(imei) or {}
                
                # Se a resposta contiver um erro, mantemos os dados do CSV
                if "erro" in resposta_api:
                    logger.warning(f"Erro na consulta do IMEI {imei}: {resposta_api.get('erro')}")
                    dados_finais = {**dados_csv, "erro_consulta": resposta_api.get("erro")}
                else:
                    # 🔹 MERGE CORRETO
                    dados_finais = {
                        **resposta_api,  # Dados formatados da API primeiro
                        **dados_csv      # Dados do CSV sobrescrevem
                    }
                    
                    # 🔹 Garante que os campos específicos da API sejam preservados
                    if "dados_brutos" in resposta_api:
                        dados_finais["dados_brutos"] = resposta_api["dados_brutos"]
                    if "resposta_completa" in resposta_api:
                        dados_finais["resposta_completa"] = resposta_api["resposta_completa"]
                    
                    # 🔹 Status do CSV prevalece se existir
                    if dados_csv.get("status"):
                        dados_finais["status"] = dados_csv["status"]

            except Exception as api_error:
                logger.error(f"Erro ao processar IMEI {imei}: {str(api_error)}")
                dados_finais = {**dados_csv, "erro_processamento": str(api_error)}

            imeis_para_cluster.append(dados_finais)

        print(f"[CSV_DEBUG] Enviando {len(imeis_para_cluster)} IMEIs completos para o cluster")
        
        if criar_cluster_automatico and imei_groups:
            # Cria um nome de cluster baseado no nome do arquivo se não for fornecido
            if not nome_cluster or nome_cluster == "Cluster gerado a partir de CSV":
                nome_cluster = f"Cluster do arquivo {file.filename}"
                
            # Cria o cluster
            cluster_service = ClusterService(db)
            cluster = cluster_service.create_cluster(
                nome=nome_cluster,
                imeis=imeis_para_cluster,  # <-- AQUI ESTÁ A CORREÇÃO
                descricao=descricao_cluster or f"Criado automaticamente a partir do arquivo {file.filename}"
            )
            cluster_id = cluster.get('id')
            cluster_nome = cluster.get('nome')
        
        # Prepara os detalhes da resposta
        return {
            "message": "Arquivo processado com sucesso" + (" e cluster criado" if criar_cluster_automatico and imei_groups else ""),
            "total_imeis_unicos": total_imeis,
            "total_registros": total_registros,
            "cluster_id": cluster_id,
            "cluster_nome": cluster_nome,
        }
        
    except Exception as e:
        error_msg = f"Erro ao processar a requisição: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    finally:
        logger.info("Processamento do arquivo finalizado")

# Rotas de Cluster
@router.post("/clusters", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
def criar_cluster(cluster_data: ClusterCreate, db: Session = Depends(get_db)):
    """
    Cria um novo cluster de IMEIs
    
    - **nome**: Nome descritivo para o cluster
    - **imeis**: Lista de IMEIs que farão parte do cluster
    - **descricao**: Descrição opcional do cluster
    """
    try:
        cluster = ClusterService(db).create_cluster(
            nome=cluster_data.nome,
            imeis=cluster_data.imeis,
            descricao=cluster_data.descricao or ""
        )
        return cluster
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao criar cluster: {str(e)}"
        )

@router.get("/clusters", response_model=List[Dict])
def listar_clusters(db: Session = Depends(get_db)):
    """Lista todos os clusters criados"""
    try:
        return ClusterService(db).list_clusters()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar clusters: {str(e)}"
        )

@router.get("/clusters/{cluster_id}", response_model=Dict)
def obter_cluster(
    cluster_id: str, 
    incluir_dados: bool = Query(False, description="Incluir dados completos dos IMEIs"),
    db: Session = Depends(get_db)
):
    """
    Obtém os dados de um cluster específico
    
    - **cluster_id**: ID do cluster
    - **incluir_dados**: Se verdadeiro, inclui os dados completos de cada IMEI
    """
    try:
        if incluir_dados:
            cluster = ClusterService(db).get_cluster_with_imei_data(cluster_id)
        else:
            cluster = ClusterService(db).get_cluster(cluster_id)
            
        if not cluster:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cluster não encontrado"
            )
            
        return cluster
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter cluster: {str(e)}"
        )

@router.get("/clusters/{cluster_id}/qrcode", response_class=Response)
def get_qrcode_cluster(cluster_id: str, db: Session = Depends(get_db)):
    """
    Gera um QR Code com os dados do cluster, incluindo informações detalhadas dos IMEIs.
    Os dados são buscados diretamente da tabela específica do cluster.
    
    Aceita o ID do cluster em vários formatos:
    - Com ou sem o prefixo 'cluster_'
    - Com hífens ou underscores
    - Com ou sem o formato UUID
    """
    try:
        logger.info(f"Solicitada geração de QR Code para o cluster: {cluster_id}")
        
        # Tenta encontrar o cluster com o ID original primeiro
        cluster_service = ClusterService(db)
        cluster = cluster_service.get_cluster_with_imei_data(cluster_id, detalhado=True)
        
        # Se não encontrou, tenta normalizar o ID
        if not cluster:
            logger.debug(f"Cluster não encontrado com ID original. Tentando normalizar o ID: {cluster_id}")
            
            # Remove prefixo 'cluster_' se existir
            clean_id = cluster_id.replace('cluster_', '')
            
            # Tenta com hífens (formato UUID)
            if '_' in clean_id:
                clean_id = clean_id.replace('_', '-')
                logger.debug(f"Tentando com ID normalizado: {clean_id}")
                cluster = cluster_service.get_cluster_with_imei_data(clean_id, detalhado=True)
            
            # Se ainda não encontrou, tenta sem hífens
            if not cluster and '-' in clean_id:
                clean_id = clean_id.replace('-', '')
                logger.debug(f"Tentando com ID sem hífens: {clean_id}")
                cluster = cluster_service.get_cluster_with_imei_data(clean_id, detalhado=True)
        
        if not cluster:
            # Lista os clusters disponíveis para depuração
            clusters = cluster_service.list_clusters()
            cluster_ids = [str(c["id"]) for c in clusters]  # Ajustado para o formato retornado por list_clusters()
            logger.warning(f"Cluster não encontrado. Clusters disponíveis: {cluster_ids}")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "Cluster não encontrado",
                    "tentou_ids": [cluster_id, clean_id] if 'clean_id' in locals() else [cluster_id],
                    "clusters_disponiveis": cluster_ids
                }
            )
        
        logger.info(f"Cluster encontrado: {cluster['nome']} (ID: {cluster['id']}) com {cluster['total_imeis']} IMEIs")
        
        # Prepara a estrutura de dados para o QR Code
        qr_data = {
            "tipo": "cluster_imei",
            "id": cluster["id"],
            "nome": cluster["nome"],
            "descricao": cluster.get("descricao", ""),
            "data_criacao": cluster["data_criacao"],
            "total_imeis": cluster["total_imeis"],
            "imeis": [],
            "detalhes_imeis": {}
        }

        # Processa cada IMEI do cluster
        for imei, dados in cluster.get("dados_imeis", {}).items():
            # Informações básicas do IMEI
            imei_info = {
                "imei": imei,
                "modelo": dados.get("modelo"),
                "status": dados.get("status"),
                "fabricante": dados.get("fabricante"),
                "tipo_ativo": dados.get("tipo_ativo"),
                "empresa": dados.get("empresa"),
                "numero_chamado": dados.get("numero_chamado"),
                "localizacao": dados.get("localizacao"),
                "data_inclusao": dados.get("data_inclusao"),
                "data_atualizacao": dados.get("data_atualizacao")
            }
            qr_data["imeis"].append(imei)
            qr_data["detalhes_imeis"][imei] = imei_info

        logger.debug(f"Dados do QR code preparados para o cluster {cluster['id']}")

        try:
            # Converte os dados para JSON formatado
            json_data = json.dumps(qr_data, ensure_ascii=False, indent=2, default=str)

            # Gera o QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # Alta correção de erro
                box_size=10,
                border=4,
            )

            qr.add_data(json_data)
            qr.make(fit=True)

            # Cria a imagem do QR code
            img = qr.make_image(fill_color="black", back_color="white")

            # Converte para bytes
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            logger.info(f"QR Code gerado com sucesso para o cluster {cluster['id']}")

            return Response(
                content=img_byte_arr.getvalue(),
                media_type="image/png",
                headers={
                    "Content-Disposition": f"inline; filename=cluster_{cluster['id']}_qrcode.png",
                    "X-Cluster-ID": str(cluster['id']),
                    "X-Cluster-Nome": cluster['nome'],
                    "X-Total-IMEIs": str(cluster['total_imeis'])
                }
            )

        except Exception as e:
            logger.error(f"Erro ao gerar a imagem do QR code: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao gerar a imagem do QR code: {str(e)}"
            )

    except HTTPException as he:
        # Re-lança exceções HTTP
        logger.warning(f"Erro HTTP ao processar requisição: {str(he.detail)}")
        raise he

    except Exception as e:
        error_msg = f"Erro inesperado ao processar a requisição: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )