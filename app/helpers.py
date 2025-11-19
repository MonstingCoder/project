from fastapi import HTTPException, status
from functools import wraps

def default_e_h(raise_=lambda msg: HTTPException(status.HTTP_418_IM_A_TEAPOT, msg), except_=Exception):
    def decorator(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except except_ as e:
                match(e.args):
                    case [m, *_]:
                        detail = m
                    case m:
                        detail = m
                
                if not detail:
                    detail = str(e)
                
                raise raise_(detail)
        
        return wrapped
    
    return decorator
