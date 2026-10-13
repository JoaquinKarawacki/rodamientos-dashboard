import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

url_base_de_datos = os.getenv("URL_BASE_DE_DATOS")

# Forzamos el driver psycopg2 explicitamente. Desde SQLAlchemy 2.1 el
# driver por defecto de "postgresql://" es psycopg (v3), que no instalamos;
# fijar "+psycopg2" usa el driver que si esta en requirements, sin depender
# de la version de SQLAlchemy que resuelva el build.
if url_base_de_datos and url_base_de_datos.startswith("postgresql://"):
    url_base_de_datos = url_base_de_datos.replace(
        "postgresql://", "postgresql+psycopg2://", 1
    )
elif url_base_de_datos and url_base_de_datos.startswith("postgres://"):
    url_base_de_datos = url_base_de_datos.replace(
        "postgres://", "postgresql+psycopg2://", 1
    )

motor = create_engine(url_base_de_datos)

FabricaSesion = sessionmaker(bind=motor)

class Base(DeclarativeBase):
    pass