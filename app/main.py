from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, RedirectResponse
from .routers import crew, token

async def lifespan(app: FastAPI):
    from .database import conn
    await conn.init_db()
    yield

app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)

app.include_router(token.router)
app.include_router(crew.router)
app.mount(
    r'/static',
    StaticFiles(directory=r'app/static'),
    name='static',
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.get('/', response_class=RedirectResponse)
async def index():
    return r'/static/index.html'

@app.get('/ping')
async def ping_pong():
    return {'message': 'pong'}
