from fastapi import FastAPI
from fastapi.responses import ORJSONResponse


app = FastAPI(default_response_class=ORJSONResponse)


@app.get('/')
async def index():
    return {'message': 'go to http://localhost:8080/docs to see the documentation'}

def main():
    from fastapi_cli import cli
    import os

    os.system('cls' if os.name == 'nt' else 'clear')
    cli.dev()

if __name__ == '__main__':
    main()
    