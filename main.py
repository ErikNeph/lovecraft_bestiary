from fastapi import FastAPI
from routers import bestiary

app = FastAPI()
app.include_router(bestiary.router, prefix="/bestiary", tags=["Bestiary"])


@app.get("/")
def root():
    return {"message": "Добро пожаловать в Бестиарий Лавкрафта!"}
