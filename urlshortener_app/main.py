# urlshortener_app/main.py

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import validators

from .database import SessionLocal, engine
from . import schemas, models, crud


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

def raise_not_found(request):

    msg = f"URL '{request.url}' doesn't exist"

    raise HTTPException(status_code=404, detail=msg)


@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):

    #Check url provided
    if not validators.url(url.target_url):
        raise_bad_request(msg="Your provided URL is not valid")

    
    db_url = crud.create_db_url(db=db, url=url)

    #create a database entry and add data into it
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key
    return db_url


@app.get("/{url_key}")
def forward_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db)
    ):
    #select the first row that has the given url_key
    db_url = (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)
        .first()
    )
    #redirect user to the target url
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@app.get("/admin/{secret_key}")
def get_stats_admin(
    secret_key : str,
    request : Request,
    db: Session = Depends(get_db)
):
    #select the first row that has the given secret_key
    db_url = (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.is_active)
        .first()
    )
    #redirect admin to stats
    from pydantic import parse_obj_as
    from typing import Dict, Any
    if db_url: 
        return {"is_active": db_url.is_active, "clicks": db_url.clicks,"url": db_url.target_url }
        #Same result with 
        #return parse_obj_as(Dict[str, Any], {"is_active": db_url.is_active, "clicks": db_url.clicks,"url": db_url.target_url })
    else:
        raise_not_found(request)
        