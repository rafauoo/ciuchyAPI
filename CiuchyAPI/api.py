from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from pydantic import BaseModel
from datetime import datetime
import os
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
DATABASE_URL = "postgresql://admin123:haslo123#@ciuchydb.postgres.database.azure.com:5432/ciuchy"  # Update with your database credentials

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

origins = [
    "*",
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:8080",  # Ustaw port, na którym uruchamiasz frontend Vue.js
    # Dodaj inne dozwolone adresy URL frontendu, jeśli to konieczne
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/images", StaticFiles(directory="images"), name="images")

class Action(Base):
    __tablename__ = 'actions'
    action = Column(String(50), primary_key=True)

class Ciuchy(Base):
    __tablename__ = 'ciuchy'
    id = Column(Numeric, primary_key=True, index=True)
    img = Column(String(150), nullable=False)
    action = Column(String(50), ForeignKey('actions.action'), nullable=False)

Base.metadata.create_all(bind=engine)
class CiuchyUpdateAction(BaseModel):
    action: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/ciuchy/")
async def create_ciuchy(file: UploadFile = File(...), action: str = None, db: Session = Depends(get_db)):
    currentDateAndTime = datetime.now()
    currentTime = currentDateAndTime.strftime("%d_%m_%Y_%H:%M:%S")
    file_location = f"images/{file.filename}at{currentTime}"
    if not os.path.exists('images'):
        os.makedirs('images')

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    if action:
        db_action = db.query(Action).filter(Action.action == action).first()
        if not db_action:
            raise HTTPException(status_code=400, detail="Invalid action")

    db_ciuchy = Ciuchy(img=file_location, action=action)
    db.add(db_ciuchy)
    db.commit()
    db.refresh(db_ciuchy)
    return db_ciuchy

@app.get("/ciuchy/")
def get_all_ciuchy(db: Session = Depends(get_db)):
    return db.query(Ciuchy).all()

@app.get("/actions/")
def get_all_actions(db: Session = Depends(get_db)):
    return db.query(Action).all()

@app.put("/ciuchy/{ciuchy_id}/action")
def update_ciuchy_action(ciuchy_id: int, action_update: CiuchyUpdateAction, db: Session = Depends(get_db)):
    db_ciuchy = db.query(Ciuchy).filter(Ciuchy.id == ciuchy_id).first()
    if db_ciuchy is None:
        raise HTTPException(status_code=404, detail="Clothing item not found")

    db_action = db.query(Action).filter(Action.action == action_update.action).first()
    if db_action is None:
        raise HTTPException(status_code=400, detail="Invalid action")

    db_ciuchy.action = action_update.action
    db.commit()
    db.refresh(db_ciuchy)
    return db_ciuchy

@app.post("/ciuchy/multiple/")
async def create_multiple_ciuchy(
    files: list[UploadFile] = File(...),
    action: str = None,
    db: Session = Depends(get_db)
):
    if action:
        # Check if the action exists
        db_action = db.query(Action).filter(Action.action == action).first()
        if db_action is None:
            raise HTTPException(status_code=400, detail="Invalid action")

    # Process each file
    ciuchy_list = []
    for file in files:
        currentDateAndTime = datetime.now()
        currentTime = currentDateAndTime.strftime("%d_%m_%Y_%H:%M:%S:%f")
        file_location = f"images/{file.filename}at{currentTime}"
        if not os.path.exists('images'):
            os.makedirs('images')

        with open(file_location, "wb") as buffer:
            buffer.write(await file.read())
        
        db_ciuchy = Ciuchy(img=file_location, action=action)
        db.add(db_ciuchy)
        ciuchy_list.append(db_ciuchy)
    db.commit()
    return {"status": "success", "items_created": len(ciuchy_list)}

@app.post("/files")
def file_contents(files: List[UploadFile]):
    return {"filenames": [file.filename for file in files]}