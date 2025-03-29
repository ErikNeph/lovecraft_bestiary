from fastapi import FastAPI
from database import Base, engine
from routers import beastiary

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.include_router(beastiary.router, prefix="/beastiary", tags=["Beastiary"])


@app.get("/")
def root():
    return {"message": "Добро пожаловать в Бестиарий Лавкрафта!"}
