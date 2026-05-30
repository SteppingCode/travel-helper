from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import date
from typing import Optional

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/details", status_code=303)


@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.post("/create_route")
async def create_route(
        request: Request,
        trip_name: str = Form(...),
        trip_date: date = Form(...),
        destination: str = Form(...),
        budget: Optional[float] = Form(None)
):
    print(f"--- Получены данные от TravelPlanner ---")
    print(f"Название: {trip_name}")
    print(f"Дата: {trip_date}")
    print(f"Направление: {destination}")
    print(f"Бюджет: {budget} руб.")

    return RedirectResponse(url="/details", status_code=303)


@app.get("/details", response_class=HTMLResponse)
async def details(request: Request):
    return templates.TemplateResponse(request=request, name="details.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)