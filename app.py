from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database.database import Database, initialize_database

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")


def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/mytrips", response_class=HTMLResponse)
async def read_my_trips(request: Request, db: Database = Depends(get_db)):
    cards = db.select("trips")
    return templates.TemplateResponse(request=request, name="mytrips.html", context={"cards": cards})


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('static/favicon.ico')
