import inspect,asyncio
from functools import wraps
from icecream import ic



def start_db_transaction(func):
    """Decorator to start a database transaction. 
    *Note, the first argument of the function,coroutine or object. that should be as the 'session' attribute or parameter.
    """
    @wraps(func)
    async def async_wrapper(*args,**kwargs):
        session=None
        if args:
            if hasattr(args[0],"session"):
                session = args[0].session
            else:
                session = args[0]
        else:
            session = kwargs.get("session",None)

        if not session:
            raise ValueError("No session found to start the transaction.")
        
        if session.in_transaction() or session.in_nested_transaction():
            ic("Transaction already active → Closing session ()")
            await session.close_all()
        
        ic(f"Started transaction from async with session of: {session}")
        async with session.begin():
            return await func(*args,**kwargs)
        
    @wraps(func)
    def sync_wrapper(*args,**kwargs):
        session=None
        if args:
            if hasattr(args[0],"session"):
                session = args[0].session
            else:
                session = args[0]
        else:
            session = kwargs.get("session",None)

        if not session:
            raise ValueError("No session found to start the transaction.")
        
        if session.in_transaction() or session.in_nested_transaction():
            ic("Transaction already active → Closing Session ()")
            session.close_all()
        
        ic(f"Started transaction from sync with session of: {session}")
        with session.begin():
            return func(*args,**kwargs)

    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
