# Sistema de Gerenciamento de Clusters de IMEI
 
API FastAPI para gerenciamento de clusters de dispositivos por IMEI e sistema Kanban de tarefas.
 
## Funcionalidades
 
- **Consulta de IMEIs**: Consulta informações de dispositivos através de IMEIs
- **Gerenciamento de Clusters**: Criação e gerenciamento de grupos de dispositivos
- **Sistema Kanban**: Gestão de tarefas com diferentes status (A Fazer, Fazendo, Feito)
- **Upload/Download CSV**: Importação e exportação de dados em lote
- **Geração de QR Codes**: Criação de QR codes para dispositivos
 
## Tecnologias
 
- **FastAPI**: Framework web moderno e rápido para Python
- **SQLAlchemy**: ORM para banco de dados
- **BeautifulSoup4**: Web scraping para consulta de IMEIs
- **QRCode**: Geração de códigos QR
- **Python-dotenv**: Gerenciamento de variáveis de ambiente
 
## Instalação
 
1. Clone o repositório:
```bash
git clone <repository-url>
cd estoquev2
```
 
2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```
 
3. Instale as dependências:
```bash
pip install -r requirements.txt
```
 
4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```
 
## Configuração
 
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
 
```
DATABASE_URL=sqlite:///./database.db
# Ou para PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/dbname
```
 
## Execução
 
Inicie o servidor de desenvolvimento:
```bash
python main.py
```
 
A API estará disponível em:
- **API**: http://localhost:8000
- **Documentação Swagger**: http://localhost:8000/docs
- **Documentação ReDoc**: http://localhost:8000/redoc
 
## Endpoints
 
### Raiz
- `GET /` - Informações básicas da API
 
### IMEI
- `POST /api/consultar` - Consultar um ou mais IMEIs
- `POST /api/consultar/csv` - Consultar IMEIs via upload CSV
- `GET /api/qrcode/{imei}` - Gerar QR code para um IMEI
- `GET /api/dispositivos` - Listar dispositivos consultados
- `GET /api/dispositivos/download` - Download CSV dos dispositivos
 
### Clusters
- `POST /api/clusters` - Criar novo cluster
- `GET /api/clusters` - Listar todos os clusters
- `GET /api/clusters/{cluster_id}` - Obter detalhes de um cluster
- `GET /api/clusters/{cluster_id}/imeis` - Listar IMEIs de um cluster
- `POST /api/clusters/{cluster_id}/add_imeis` - Adicionar IMEIs a um cluster
 
### Kanban
- `GET /api/tarefas` - Listar todas as tarefas
- `POST /api/tarefas` - Criar nova tarefa
- `PUT /api/tarefas/{tarefa_id}` - Atualizar tarefa
- `DELETE /api/tarefas/{tarefa_id}` - Excluir tarefa
- `PUT /api/tarefas/{tarefa_id}/status` - Atualizar status da tarefa
- `PUT /api/tarefas/{tarefa_id}/observacao` - Atualizar observação
- `POST /api/tarefas/upload` - Upload CSV de tarefas
- `GET /api/tarefas/download` - Download CSV de tarefas
 
## Exemplos de Uso
 
### Consultar IMEI
```javascript
const response = await fetch('http://localhost:8000/api/consultar', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ imeis: ['123456789012345'] })
});
const data = await response.json();
```
 
### Criar Cluster
```javascript
const response = await fetch('http://localhost:8000/api/clusters', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    nome: 'Cluster Teste',
    imeis: ['123456789012345', '987654321098765'],
    descricao: 'Cluster de teste'
  })
});
```
 
### Criar Tarefa
```javascript
const response = await fetch('http://localhost:8000/api/tarefas', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'Testar dispositivo',
    imei: '123456789012345',
    unidade: 'Unidade A',
    prazo: '2024-12-31',
    perfil: 'Técnico',
    priority: 'alta',
    status: 'A Fazer'
  })
});
```
 
## Estrutura do Projeto
 
```
estoquev2/
|-- app/
|   |-- models/          # Modelos de dados
|   |-- routes/          # Rotas da API
|   |-- services/        # Lógica de negócio
|   |-- database.py      # Configuração do banco
|-- main.py              # Aplicação principal
|-- requirements.txt     # Dependências
|-- .env                # Variáveis de ambiente
```
 
## Status das Tarefas
 
O sistema Kanban suporta os seguintes status:
- **A Fazer**: Tarefas pendentes
- **Fazendo**: Tarefas em andamento
- **Feito**: Tarefas concluídas
 
## Prioridades
 
- **baixa**: Baixa prioridade
- **média**: Média prioridade
- **alta**: Alta prioridade
 
## Licença
 
