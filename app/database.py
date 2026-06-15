import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

url_base_de_datos = os.getenv("URL_BASE_DE_DATOS")

motor = create_engine(url_base_de_datos)

FabricaSesion = sessionmaker(bind=motor)

class Base(DeclarativeBase):
    pass