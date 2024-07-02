from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
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
    status_id = Column(Integer, ForeignKey('vacancy_status.id'))

    status = relationship("VacancyStatus", back_populates="vacancies")


class VacancyStatus(Base):
    __tablename__ = 'vacancy_status'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, unique=True)

    vacancies = relationship("Vacancy", back_populates="status")


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
