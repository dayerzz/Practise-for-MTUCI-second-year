from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

Base = declarative_base()


class Vacancy(Base):
    __tablename__ = 'vacancies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    employer = Column(String)
    salary_from = Column(Integer, nullable=True)
    salary_to = Column(Integer, nullable=True)
    currency = Column(String, nullable=True)
    url = Column(String)
    city = Column(String)
    skills = Column(Text, nullable=True)


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
