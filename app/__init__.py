from .database import engine, Base
from .models.dispositivos import DispositivoDB

# Cria as tabelas no banco de dados
def init_db():
    Base.metadata.create_all(bind=engine)

# Inicializa o banco de dados
init_db()
