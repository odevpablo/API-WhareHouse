# app/services/consultar_imei.py
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from fastapi import HTTPException, status

class ConsultaImeiService:
    BASE_URL = "https://console.nxt4insight.com"
    LOGIN_PAGE = f"{BASE_URL}/Account/Login"
    LOGIN_URL = f"{BASE_URL}/Account/Login"
    INVENTARIO_URL = f"{BASE_URL}/Movimentacao/LoadGridInventario"

    def __init__(self, usuario: str, senha: str):
        self.usuario = usuario
        self.senha = senha
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest"
        })
        self._autenticado = False

    def autenticar(self):
        if self._autenticado:
            return True

        try:
            # Acessa a página de login para obter o token CSRF
            resp = self.session.get(self.LOGIN_PAGE)
            if resp.status_code != 200:
                raise Exception(f"Falha ao acessar página de login: {resp.status_code}")

            soup = BeautifulSoup(resp.text, "html.parser")
            token_input = soup.find("input", {"name": "__RequestVerificationToken"})
            if not token_input or not token_input.get("value"):
                raise Exception("Não foi possível encontrar o token antiforgery.")

            token = token_input["value"]
            payload = {
                "loginViewModel.Login": self.usuario,
                "loginViewModel.Password": self.senha,
                "__RequestVerificationToken": token
            }

            # Envia o formulário de login
            resp = self.session.post(
                self.LOGIN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if resp.status_code not in (200, 302):
                raise Exception(f"Falha no login (HTTP {resp.status_code})")

            # Verifica se o cookie de autenticação foi definido
            if ".AspNetCore.Cookies" not in str(self.session.cookies):
                raise Exception("❌ Login falhou — nenhum cookie de autenticação encontrado.")
            
            self._autenticado = True
            return True

        except Exception as e:
            self.session.close()
            self._autenticado = False
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Falha na autenticação: {str(e)}"
            )

    def consultar_por_imei(self, imei: str) -> Dict:
        """
        Alias para consultar_imei para manter compatibilidade com código existente.
        Consulta um IMEI no sistema NXT4 e retorna os dados formatados.
        
        Args:
            imei: Número do IMEI a ser consultado
            
        Returns:
            Dict: Dados do IMEI formatados
        """
        return self.consultar_imei(imei)
        
    def consultar_imei(self, imei: str) -> Dict:
        try:
            self.autenticar()
            
            params = {
                "skip": 0,
                "take": 20,
                "requireTotalCount": "true",
                "filter": f'["IdAtivo","contains","{imei}"]',
                "totalSummary": "[]",
                "_": "1760386284308"
            }

            # Faz a requisição
            resp = self.session.get(
                self.INVENTARIO_URL,
                params=params
            )

            if resp.status_code != 200:
                return {
                    "imei": imei,
                    "erro": f"Erro na consulta (HTTP {resp.status_code})"
                }

            data = resp.json()
            if isinstance(data, dict) and "data" in data and len(data["data"]) > 0:
                item = data["data"][0]
                # Cria um dicionário com os dados formatados
                dados_formatados = {
                    "imei": imei,
                    "imei2": item.get("IMEI2") or item.get("Imei2") or item.get("imei2") or item.get("Imei 2") or item.get("IMEI 2"),
                    "serial": item.get("Serial") or item.get("NumeroSerie") or item.get("NumeroSerial") or item.get("numero_serie") or item.get("serial") or item.get("NroSerie") or item.get("NroSerial"),
                    "modelo": item.get("Modelo") or item.get("modelo"),
                    "status": item.get("Status") or item.get("status"),
                    "fabricante": item.get("Fabrica") or item.get("fabrica") or item.get("marca"),
                    "tipo_ativo": item.get("TipoAtivo") or item.get("tipoativo"),
                    "empresa": item.get("Empresa") or item.get("empresa"),
                    "numero_chamado": item.get("NumeroChamado") or item.get("numero_chamado"),
                    "data_inicio": item.get("DataInicio") or item.get("data_inicio"),
                    "localizacao": item.get("Organograma") or item.get("organograma") or item.get("vinculadoha"),
                    "detalhes": item,  # Mantém todos os dados originais para referência
                    "dados_brutos": item  # Garante que os dados brutos estejam disponíveis
                }
                
                # Adiciona a resposta completa da API se disponível
                if isinstance(data, dict):
                    dados_formatados["resposta_completa"] = data
                    
                return dados_formatados
            else:
                return {
                    "imei": imei,
                    "erro": "Nenhum dado encontrado para este IMEI"
                }

        except Exception as e:
            return {
                "imei": imei,
                "erro": f"Erro ao processar consulta: {str(e)}"
            }

    def consultar_multiplos_imeis(self, imeis: List[str]) -> Dict[str, Dict]:
        try:
            resultados = {}
            for imei in imeis:
                resultado = self.consultar_imei(imei)
                resultados[imei] = resultado
            return resultados
        finally:
            # Fecha a sessão após o uso
            self.session.close()