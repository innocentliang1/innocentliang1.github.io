from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os

app = FastAPI()

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 导入原main.py的路由
from fastapi import APIRouter
router = APIRouter()

# 这里需要将原main.py的路由逻辑复制过来
@router.get("/")
async def read_root(request: Request):
    return {"message": "Hello World"}

app.include_router(router)

# Vercel需要这个handler
def handler(request):
    from mangum import Mangum
    mangum = Mangum(app)
    return mangum(request)