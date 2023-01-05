# urlshortener_app/main.py

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import validators
import secrets

from .database import SessionLocal, engine
from . import schemas, models


models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.get("/")
def read_root():
    return "Welcome to your App!"


def raise_bad_request(msg):
    raise HTTPException(status_code=400, detail=msg)


@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):

    #Check url provided
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    #Create random key and secret_key
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    key = "".join(secrets.choice(chars) for _ in range(4))
    secret_key = "".join(secrets.choice(chars) for _ in range(10))

    #create a database entry and add data into it
    db_url = models.URL(
        target_url=url.target_url, key=key, secret_key=secret_key
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    db_url.url = key
    db_url.admin_url = secret_key
    return db_url