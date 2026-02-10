from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid
import shutil

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

app = FastAPI()

#Creating SQLite Database(Switch to PostGres later)
DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread" : False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True, index = True)
    name = Column(String, index = True)
    email = Column(String, unique = True, index = True)
    password = Column(String, index = True)

class PDF(Base):
    __tablename__ = "pdfs"
    id = Column(Integer, primary_key = True, index = True)
    user_id = Column(Integer, index = True)
    fileName = Column(String)
    storage_path = Column(String)

    summaries = relationship("Summary", back_populates="pdf")

class Summary(Base):
    __tablename__ = "summaries"
    id = Column(Integer, primary_key = True, index = True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"))
    summarize_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    pdf = relationship("PDF", back_populates="summaries")
    #Create a model used var as well



Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Creating SQLite Database(Switch to PostGres later)

#User Data Contracts
class UserCreate(BaseModel):
    name : str
    email : str
    password : str

class UserResponse(BaseModel):
    id : int
    name : str
    email : str

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None



#Create new user
@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db:Session = Depends(get_db)):
    db_user = User(name = user.name, email = user.email, password = user.password)
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return db_user

#Return list of all users
@app.get("/users", response_model=list[UserResponse])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

#Return certain user by ID
@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id : int, db : Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not Found")
    
    return user

#Update certain users information
@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not Found")
    db_user.name = user.name if user.name is not None else db_user.name
    db_user.email = user.email if user.email is not None else db_user.email
    db_user.password = user.password if user.password is not None else db_user.password
    db.commit()
    db.refresh(db_user)
    return db_user

#Delete certain users
@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not Found")
    db.delete(db_user)
    db.commit()
    return db_user

#PDF Data Contracts
class PDFResponse(BaseModel):
    id : int
    fileName : str
    
    model_config = ConfigDict(from_attributes=True)

#Upload new PDF into Database
@app.post("/pdf/upload", response_model=PDFResponse)
def create_pdf(file : UploadFile = File(...), db: Session = Depends(get_db)):
    file_id = str(uuid.uuid4())
    path = f"storage/{file_id}.pdf"

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    pdf = PDF(fileName = file.filename, storage_path = path, user_id = 1)

    db.add(pdf)
    db.commit()
    db.refresh(pdf)
    return pdf

#Return list of all PDFS(metadata)
@app.get("/pdf/", response_model=List[PDFResponse])
def read_pdfs(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    pdfs = db.query(PDF).offset(skip).limit(limit).all()
    return pdfs

#Return certain PDF data with ID(metadata)
@app.get("/pdf/{id}", response_model=PDFResponse)
def read_pdf(id : int, db : Session = Depends(get_db)):
    pdf = db.query(PDF).filter(PDF.id == id).first()
    if pdf is None:
        raise HTTPException(status_code=404, detail="PDF not Found")
    
    return pdf

#Return the actual file as a download
@app.get("/pdf/{id}/download", response_model=PDFResponse)
def get_pdf(id : int, db : Session = Depends(get_db)):
    pdf = db.query(PDF).filter(PDF.id == id).first()
    if pdf is None:
        raise HTTPException(status_code=404, detail="PDF not Found")
    return FileResponse(
        path=pdf.storage_path,
        media_type="application/pdf",
        filename=pdf.fileName
    )

#Summary Data Contracts
class SummaryRequest(BaseModel):
    pdf_id : int
    storage_id : str

class SummaryResponse(BaseModel):
    pdf_id : int
    summary : str

@app.post("/summary/", response_model=SummaryResponse)
def create_summary(summary_request : SummaryRequest, db : Session = Depends(get_db)):
    #Get the pdf
    #load pdf content
    #generate summary
    #save summary in db
    #return summary
    return summary_request.summary

@app.get("/summary/{pdf_id}", response_model=SummaryResponse)
def get_summary(pdf_id : int, db : Session = Depends(get_db)):
    #get the summary for this pdf
    #return the summary for this pdf
    return 
