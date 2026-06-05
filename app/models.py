import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    chunk_count = Column(Integer, default=0)
    total_chars = Column(Integer, default=0)
    vector_collection = Column(String(100), nullable=False, unique=True)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

class QARecord(Base):
    __tablename__ = "qa_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ResumeRecord(Base):
    __tablename__ = 'resume_records'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    original_text = Column(Text, nullable=False)
    optimized_text = Column(Text, nullable=True)
    optimize_target = Column(String(50), default='')
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)