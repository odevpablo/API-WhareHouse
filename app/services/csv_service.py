import csv
import io
import logging
from typing import Dict, List, Tuple

# Configura o logger
logger = logging.getLogger(__name__)

class CsvService:
    @staticmethod
    def process_csv_file(file_content: bytes) -> Tuple[Dict[str, List[Dict]], List[str]]:
        """
        Processa o conteúdo de um arquivo CSV e agrupa os dados pelo IMEI.
        
        Args:
            file_content: Conteúdo binário do arquivo CSV
            
        Returns:
            Tuple contendo:
                - Dicionário com IMEIs como chaves e lista de registros como valores
                - Lista de cabeçalhos do CSV
                
        Raises:
            ValueError: Se o arquivo estiver vazio, mal formatado ou não contiver a coluna IMEI
            UnicodeDecodeError: Se não for possível decodificar o arquivo como UTF-8
        """
        logger.info("Iniciando processamento de arquivo CSV")
        
        if not file_content:
            error_msg = "O arquivo está vazio"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            # Tenta decodificar com UTF-8 primeiro, depois tenta com latin-1 como fallback
            try:
                logger.debug("Tentando decodificar o arquivo com UTF-8")
                content = file_content.decode('utf-8')
                logger.debug("Arquivo decodificado com sucesso usando UTF-8")
            except UnicodeDecodeError as e:
                logger.warning("Falha ao decodificar com UTF-8, tentando latin-1", exc_info=True)
                try:
                    content = file_content.decode('latin-1')
                    logger.debug("Arquivo decodificado com sucesso usando latin-1")
                except Exception as e:
                    error_msg = f"Falha ao decodificar o arquivo: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    raise ValueError(error_msg) from e
                
            # Remove BOM se presente
            if content.startswith('\ufeff'):
                content = content[1:]
                
            # Cria o leitor CSV
            csv_reader = csv.DictReader(io.StringIO(content))
            
            # Verifica se o arquivo tem cabeçalhos
            logger.debug(f"Cabeçalhos encontrados: {csv_reader.fieldnames}")
            if csv_reader.fieldnames is None:
                error_msg = "O arquivo CSV não contém cabeçalhos válidos"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Verifica se a coluna IMEI existe (case insensitive)
            fieldnames = [name.strip().upper() for name in csv_reader.fieldnames]
            if not fieldnames:
                raise ValueError("O arquivo CSV está vazio ou não contém cabeçalhos")
                
            if 'IMEI' not in fieldnames:
                error_msg = f"O arquivo CSV deve conter uma coluna chamada 'IMEI'. Cabeçalhos encontrados: {fieldnames}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Agrupa os registros por IMEI
            imei_groups = {}
            line_number = 1  # Começa em 1 porque o cabeçalho é a linha 1
            
            for line_number, row in enumerate(csv_reader, start=2):  # +1 para o cabeçalho
                if not any(row.values()):  # Pula linhas vazias
                    continue
                    
                try:
                    # Remove espaços em branco extras dos nomes das colunas e valores,
                    # ignora chaves None e normaliza nomes de colunas para MAIÚSCULAS
                    cleaned_row = {
                        k.strip().upper(): (v.strip() if isinstance(v, str) else v)
                        for k, v in row.items() if isinstance(k, str)
                    }
                    imei_raw = cleaned_row.get('IMEI')
                    imei = imei_raw.strip() if isinstance(imei_raw, str) else ''
                    
                    if not imei:
                        continue  # Pula linhas sem IMEI
                        
                    if imei not in imei_groups:
                        imei_groups[imei] = []
                    
                    imei_groups[imei].append(cleaned_row)
                except Exception as e:
                    raise ValueError(f"Erro na linha {line_number}: {str(e)}")
            
            if not imei_groups:
                error_msg = "Nenhum IMEI válido encontrado no arquivo"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            logger.info(f"Processamento concluído com sucesso. {len(imei_groups)} IMEIs únicos encontrados.")
            return imei_groups, fieldnames
            
        except csv.Error as e:
            error_msg = f"Erro ao processar o arquivo CSV na linha {getattr(e, 'line_number', 'desconhecida')}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e
        except Exception as e:
            error_msg = f"Erro inesperado ao processar o arquivo: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e

    @staticmethod
    def process_csv_stream(text_stream: io.TextIOBase) -> Tuple[Dict[str, List[Dict]], List[str]]:
        """
        Processa um CSV a partir de um stream de texto (streaming), agrupando por IMEI sem carregar o arquivo inteiro em memória.
        Extrai as colunas IMEI, MODELO, STATUS e OBS (ou OBSERVAÇÃO) do arquivo CSV.

        Args:
            text_stream: Stream de texto já configurado com o encoding correto (ex.: TextIOWrapper)

        Returns:
            Tuple contendo o dicionário de grupos por IMEI e a lista de cabeçalhos (em maiúsculas)

        Raises:
            ValueError: Se o arquivo estiver vazio, mal formatado ou não contiver a coluna IMEI
        """
        logger.info("Iniciando processamento de arquivo CSV via stream")

        # Cria o leitor CSV diretamente do stream
        csv_reader = csv.DictReader(text_stream)

        # Verifica cabeçalhos
        logger.debug(f"Cabeçalhos encontrados: {csv_reader.fieldnames}")
        if csv_reader.fieldnames is None:
            error_msg = "O arquivo CSV não contém cabeçalhos válidos"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Normaliza cabeçalhos (remove espaços e converte para maiúsculas)
        fieldnames = [name.strip().upper() for name in csv_reader.fieldnames]
        if not fieldnames:
            raise ValueError("O arquivo CSV está vazio ou não contém cabeçalhos")

        # Verifica se a coluna IMEI está presente
        if 'IMEI' not in fieldnames:
            error_msg = f"O arquivo CSV deve conter uma coluna chamada 'IMEI'. Cabeçalhos encontrados: {fieldnames}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Mapeia os nomes das colunas para nomes padronizados
        column_mapping = {
            # Mapeamento para o formato exato do CSV
            'IMEI': 'imei',
            'MODELO': 'modelo',
            'STATUS': 'status',
            'OBS': 'observacao',
            # Mapeamentos alternativos para compatibilidade
            'OBSERVAÇÃO': 'observacao',
            'OBSERVACAO': 'observacao',
            'FABRICANTE': 'fabricante',
            'TIPO ATIVO': 'tipo_ativo',
            'EMPRESA': 'empresa',
            'NUMERO CHAMADO': 'numero_chamado',
            'CHAMADO': 'numero_chamado',
            'LOCALIZAÇÃO': 'localizacao',
            'LOCAL': 'localizacao'
        }

        imei_groups: Dict[str, List[Dict]] = {}

        for line_number, row in enumerate(csv_reader, start=2):
            if not any(row.values()):
                continue
                
            try:
                # Limpa os dados da linha
                cleaned_row = {}
                for k, v in row.items():
                    if not isinstance(k, str):
                        continue
                    # Remove espaços extras e converte para maiúsculas
                    clean_key = k.strip().upper()
                    # Aplica o mapeamento de nomes de colunas
                    mapped_key = column_mapping.get(clean_key, clean_key.lower())
                    # Limpa o valor (remove espaços extras e converte para string)
                    if v is None:
                        clean_value = ''
                    else:
                        clean_value = str(v).strip()
                    cleaned_row[mapped_key] = clean_value
                
                # Obtém o IMEI (já em maiúsculas devido ao mapeamento)
                imei = cleaned_row.get('imei', '')
                if not imei:
                    continue
                
                # Log para verificar o conteúdo completo da linha processada
                print(f"\n[CSV_DEBUG] Linha processada:", cleaned_row)
                
                # Garante que o status tenha um valor padrão se estiver vazio
                status = (cleaned_row.get('status') or '').strip()
                print(f"[CSV_DEBUG] Status extraído: '{status}'")
                
                if not status:
                    status = 'DESCONHECIDO'
                    print("[CSV_DEBUG] Status vazio, definido como 'DESCONHECIDO'")
                    
                # Cria um dicionário com os dados do IMEI
                imei_data = {
                    'imei': imei,
                    'modelo': cleaned_row.get('modelo'),
                    'status': status,
                    'observacao': cleaned_row.get('observacao'),
                    'fabricante': cleaned_row.get('fabricante'),
                    'tipo_ativo': cleaned_row.get('tipo_ativo'),
                    'empresa': cleaned_row.get('empresa'),
                    'numero_chamado': cleaned_row.get('numero_chamado'),
                    'localizacao': cleaned_row.get('localizacao'),
                    'dados_brutos': cleaned_row  # Mantém todos os dados originais
                }
                
                # Log do objeto final que será retornado
                print(f"[CSV_DEBUG] Dados do IMEI a serem retornados: {imei_data}")
                print("-" * 50)
                
                # Adiciona ao dicionário de grupos
                if imei not in imei_groups:
                    imei_groups[imei] = []
                imei_groups[imei].append(imei_data)
                
            except Exception as e:
                raise ValueError(f"Erro na linha {line_number}: {str(e)}")

        if not imei_groups:
            error_msg = "Nenhum IMEI válido encontrado no arquivo"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Processamento (stream) concluído com sucesso. {len(imei_groups)} IMEIs únicos encontrados.")
        return imei_groups, fieldnames
