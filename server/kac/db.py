import asyncio
import asyncpg
from fastapi import Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from . import config

db_pool = None


async def init_db(app):
    global db_pool
    db_pool = await asyncpg.create_pool(database=config.POSTGRES_DB,
                                        user=config.POSTGRES_USER, host=config.POSTGRES_SERVER, password=config.POSTGRES_PASSWORD)

    app.middleware("http")(db_session_middleware)

async def close_db(app):
    await asyncio.wait_for(db_pool.close(), 2)

async def get_db_conn(request: Request):
    request.state.db_conn = conn = await db_pool.acquire()
    request.state.db_txn = tr = conn.transaction()
    # print("RS", id(request), request.state.__dict__)
    await tr.start()

    return conn


Database = Depends(get_db_conn)


async def db_session_middleware(request: Request, call_next):
    request.state.db_conn = None
    request.state.db_txn = None
    # print("RS2", id(request), request.state.__dict__)
    try:
        try:
            response = await call_next(request)
        except:
            if request.state.db_txn:
                print("txn rollback")
                await request.state.db_txn.rollback()
            raise
        else:
            if request.state.db_txn:
                print("txn commit")
                await request.state.db_txn.commit()
    finally:
        conn = request.state.db_conn
        if conn:
            print("closing conn")
            await db_pool.release(conn)
    return response


