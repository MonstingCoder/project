from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse, RedirectResponse
from .routers import (
    crew,
    item,
    payment_proof,
    token,
    transaction,
)
from .database import conn


async def lifespan(app: FastAPI):
    await conn.init_db()
    yield
    await conn.close_db()

app = FastAPI(
    default_response_class=ORJSONResponse, lifespan=lifespan,
)

app.include_router(crew.router)
app.include_router(item.router)
app.include_router(payment_proof.router)
app.include_router(token.router)
app.include_router(transaction.router)
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
