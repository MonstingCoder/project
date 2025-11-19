from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import ORJSONResponse, RedirectResponse
from .routers import auth, users


async def lifespan(app: FastAPI):
    from .database import conn
    await conn.init_db()
    yield


app = FastAPI(default_response_class=ORJSONResponse, lifespan=lifespan)

app.include_router(auth.router)
app.include_router(users.router)
app.mount(
    r'/static',
    StaticFiles(directory=r'app/static'),
    name='static',
)


@app.get('/', response_class=RedirectResponse)
async def index():
    return r'/static/index.html'


@app.get('/ping')
async def ping_pong():
    return {'message': 'pong'}


def main():
    from fastapi_cli import cli
    import os

    os.system('cls' if os.name == 'nt' else 'clear')
    cli.dev()


if __name__ == '__main__':
    main()
    