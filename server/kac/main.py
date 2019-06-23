import asyncpg
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from .db import init_db, close_db, Database
from . import discovery
# from app.api.api_v1.api import api_router
# from app.core import config
# from app.db.session import Session

app = FastAPI(title="Kurenivka Access Control server", openapi_url="/api/v1/openapi.json")

# CORS
# origins = []

# Set all CORS enabled origins
# if config.BACKEND_CORS_ORIGINS:
#     origins_raw = config.BACKEND_CORS_ORIGINS.split(",")
#     for origin in origins_raw:
#         use_origin = origin.strip()
#         origins.append(use_origin)
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=origins,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     ),

from .api import api_router
app.include_router(api_router, prefix='/api/v1')

@app.on_event("startup")
async def startup_event():
    await init_db(app)

    discovery.discovery_register(app)

@app.on_event("shutdown")
async def shutdown_event():
    discovery.discovery_unregister(app)

    await close_db(app)


@app.get("/db")
async def db(conn = Database):
    print(conn)
    return {'conn': 'ok'}

@app.get("/db2")
async def db(conn = Database):
    print(conn)
    raise Exception("")


@app.get("/nodb")
async def nodb():
    return {'nodb': 'no'}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

