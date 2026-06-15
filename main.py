from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

from place_data import places, inf

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def get_budget(request:Request):

    return templates.TemplateResponse(request=request, name = "budget.html")



@app.get("/popular_places")
async def popular_places(request: Request, q: Optional[str] = None):
    
    filtered_places = places
    
    if q and q.strip():                    # Защита от пустой строки
        q_lower = q.lower().strip()
        filtered_places = [
            place for place in places
            if (q_lower in place.get("name", "").lower() or
                q_lower in place.get("country", "").lower() or
                q_lower in place.get("description", "").lower() or
                any(q_lower in tag.lower() for tag in place.get("tags", [])))
        ]

    return templates.TemplateResponse( request=request, name = "place.html", context={ "places": filtered_places,"query": q or ""})



@app.get("/inf/{inf_id}", response_class=HTMLResponse)
async def get_place_page(request: Request, inf_id: int):
    # Ищем в places по ключу "id"
    place = next((p for p in places if p["id"] == inf_id), None)
    if not place:
        raise HTTPException(status_code=404, detail="Place not found")

    # Ищем в inf по ключу "id_inf"
    details = next((d for d in inf if d["id_inf"] == inf_id), {})

    # Объединяем данные. Если в details есть поля с такими же именами, они перезапишут place.
    page_data = {**place, **details}

    # Для удобства в шаблоне явно задаём id (чтобы в HTML всегда было place.id)
    page_data["id"] = inf_id

    return templates.TemplateResponse(request=request, name = "detail.html", context={"place":page_data})
     
   

