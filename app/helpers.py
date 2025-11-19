from fastapi import HTTPException, status
from functools import wraps

def default_e_h(raise_=lambda msg: HTTPException(status.HTTP_418_IM_A_TEAPOT, msg), except_=Exception):
    def decorator(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except except_ as e:
                detail = {'from': 'default error handling'}
                match(e.args):
                    case list():
                        detail['info'] = e.args
                    case m:
                        detail['info'] = m
                
                if not detail:
                    detail['info'] = str(e)
                
                raise raise_(detail)
        
        return wrapped
    
    return decorator
