import datetime
from fastapi import APIRouter, HTTPException, Depends

api_router = APIRouter()

from .db import Database
from .config import EVENT_ID, MAX_TXN_DURATION


@api_router.post('/bind_token')
async def bind_token(ticket_code, token, conn=Database):
    """Bind activate ticket and bind it to access token"""

    ticket = await conn.fetchrow('SELECT * FROM ticket WHERE event_id=$1 AND code=$2 FOR UPDATE', EVENT_ID, ticket_code)
    if not ticket:
        raise HTTPException(status_code=400, detail='Unknown ticket code')

    if ticket['activated_at']:
        raise HTTPException(status_code=409, detail='Ticket already activated')

    # activate ticket
    await conn.execute('UPDATE ticket SET activated_at=$3 WHERE event_id=$1 AND code=$2', EVENT_ID, ticket_code, datetime.datetime.now())
    await conn.execute('INSERT INTO access_token (event_id, ticket_code, token) VALUES($1, $2, $3)', EVENT_ID, ticket_code, token)

    return {'status': 'ok', 'message': 'Ticket activated and bound to access token'}


def validate_status(token, turngate):
    if token['status'] == 'in' and turngate['direction'] == 'exit':
        return 'out'
    elif token['status'] == 'out' and turngate['direction'] == 'enter':
        return 'in'

    raise RuntimeError(f"Token with status {token['status']!r} not allowed to use turngate with direction {turngate['direction']!r}")


async def validate_turngate_and_token(turngate_id, token, conn):
    token = await conn.fetchrow('SELECT * FROM access_token WHERE event_id=$1 AND token=$2 FOR UPDATE', EVENT_ID, token)
    if not token:
        raise HTTPException(status_code=400, detail='no such token')

    turngate = await conn.fetchrow('SELECT * FROM turngate WHERE event_id=$1 AND turngate_id=$2', EVENT_ID, turngate_id)
    if not turngate:
        raise HTTPException(status_code=400, detail='unknown turngate')

    return turngate, token


@api_router.post('/validate_token')
async def validate_token(turngate_id, token, conn=Database):
    """Bind activate ticket and bind it to access token"""

    token = await conn.fetchrow('SELECT * FROM access_token WHERE event_id=$1 AND token=$2 FOR UPDATE', EVENT_ID, token)
    if not token:
        raise HTTPException(status_code=400, detail='no such token')

    turngate = await conn.fetchrow('SELECT * FROM turngate WHERE event_id=$1 AND turngate_id=$2', EVENT_ID, turngate_id)
    if not turngate:
        raise HTTPException(status_code=400, detail='unknown turngate')

    try:
        new_status = validate_status(token, turngate)
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

    # ticket = await conn.fetchrow('SELECT * FROM ticket WHERE event_id=$1 AND code=$2 FOR UPDATE', EVENT_ID, ticket_code)
    # if not ticket:
    #     return {'status': 'error', 'message': 'Unknown ticket code'}

    # if ticket['activated_at']:
    #     return {'status': 'error', 'message': 'Ticket already activated'}

    # # activate ticket
    # await conn.execute('UPDATE ticket SET activated_at=$3 WHERE event_id=$1 AND code=$2', EVENT_ID, ticket_code, datetime.datetime.now())
    # await conn.execute('INSERT INTO access_token (event_id, ticket_code, token) VALUES($1, $2, $3)', EVENT_ID, ticket_code, token)

    return {'status': 'ok', 'message': 'Token valid, access allowed'}


@api_router.post('/process_token')
async def process_token(turngate_id, token, conn=Database):
    """Bind activate ticket and bind it to access token"""

    token = await conn.fetchrow('SELECT * FROM access_token WHERE event_id=$1 AND token=$2 FOR UPDATE', EVENT_ID, token)
    if not token:
        raise HTTPException(status_code=400, detail='no such token')

    turngate = await conn.fetchrow('SELECT * FROM turngate WHERE event_id=$1 AND turngate_id=$2', EVENT_ID, turngate_id)
    if not turngate:
        raise HTTPException(status_code=400, detail='unknown turngate')

    try:
        new_status = validate_status(token, turngate)
    except Exception as e:
        return HTTPException(status_code=409, detail=str(e))

    await conn.execute('UPDATE access_token SET status=$3 WHERE event_id=$1 AND token=$2', EVENT_ID, token['token'], new_status)

    return {'status': 'ok', 'message': 'Access registered'}


@api_router.post('/access/start')
async def access_start(turngate_id, token, conn=Database):
    turngate, token = await validate_turngate_and_token(turngate_id, token, conn)

    try:
        new_status = validate_status(token, turngate)
    except Exception as e:
        return HTTPException(status_code=409, detail=str(e))

    txn_start = token['txn_start']
    if txn_start:
        txn_delta = (datetime.datetime.now() - txn_start).total_seconds()
    else:
        txn_delta = 0

    print(repr(txn_start), repr(txn_delta))
    txn_gate_id = token['txn_gate_id']
    if txn_start is not None and (txn_gate_id != turngate_id and txn_delta < MAX_TXN_DURATION):
        return HTTPException(status_code=409, detail='Another access event in progress')

    await conn.execute('UPDATE access_token SET txn_start=now(), txn_gate_id=$3 WHERE event_id=$1 AND token=$2', EVENT_ID, token['token'], turngate['turngate_id'])

    return {'status': 'ok', 'message': 'Access allowed'}



@api_router.post('/access/complete')
async def access_complete(turngate_id, token, conn=Database):
    turngate, token = await validate_turngate_and_token(turngate_id, token, conn)

    try:
        new_status = validate_status(token, turngate)
    except Exception as e:
        return HTTPException(status_code=409, detail=str(e))

    await conn.execute('UPDATE access_token SET status=$3, txn_start=NULL, txn_gate_id=NULL WHERE event_id=$1 AND token=$2', EVENT_ID, token['token'], new_status)

    return {'status': 'ok', 'message': 'Access registered'}


@api_router.post('/access/cancel')
async def access_cancel(turngate_id, token, conn=Database):
    turngate, token = await validate_turngate_and_token(turngate_id, token, conn)

    await conn.execute('UPDATE access_token SET txn_start=NULL, txn_gate_id=NULL WHERE event_id=$1 AND token=$2', EVENT_ID, token['token'])

    return {'status': 'ok', 'message': 'Access request cancelled'}
