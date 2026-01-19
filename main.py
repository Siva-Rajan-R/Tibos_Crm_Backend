from fastapi import FastAPI,Request
from api.routes import auth,contact,customer,order,product,user,drop_downs,dashboard,opportunity,leads,twofactor,distributor
from fastapi.middleware.cors import CORSMiddleware
from infras.primary_db.services.user_service import UserService,UserRoles
from infras.primary_db.main import init_pg_db,add_delete
from infras.caching.main import check_redis_health,redis_client
from icecream import ic
from infras.primary_db.main import AsyncLocalSession
import sys,subprocess,asyncio
from contextlib import asynccontextmanager
import os
from core.settings import SETTINGS,EnvironmentEnum
from dotenv import load_dotenv
load_dotenv()

# changing event loop for better permformance *It works only on (linux,macos)
if sys.platform!="win32":
    # uvloop_install_cmd=["pip","install","uvloop"]
    # uvloop_exc_process=subprocess.Popen(uvloop_install_cmd)
    # uvloop_exc_process.wait()
    # ic("✅ Uvloop Installed Successfully")

    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    ic("✅ Event loop policy Changed Successfully")


# Controlling app startups to endup Lifecycle
@asynccontextmanager
async def api_lifespan(app:FastAPI):
    try:
        ic("🏎️ Executing API Lifespan... ")
        await init_pg_db()
        await add_delete()
        async with AsyncLocalSession() as session:
            await UserService(session=session,user_role=UserRoles.SUPER_ADMIN).init_superadmin()
        await check_redis_health()
        # await redis_client.flushall()
        yield
    except Exception as e:
        ic(f"❌ Error At Executing API Lifespan {e}")
    finally:
        ic("🌵 Shuttingdown API Lifespan")


# Hiding Dev Urls For Production
openapi_url='/openapi.json'
docs='/docs'
redoc='/redoc'
debug=True

if SETTINGS.ENVIRONMENT==EnvironmentEnum.PRODUCTION.value:
    openapi_url=None
    docs=None
    redoc=None
    debug=False


app=FastAPI(
    lifespan=api_lifespan,
    openapi_url=openapi_url,
    docs_url=docs,
    redoc_url=redoc,
    debug=debug,
    title="TIBOS-CRM API",
    version="0.1.2"
)

# Routers
@app.get('/')
def home_root(request:Request):
    return {"accesss token":request.headers.get("X-Access-Token"),'refresh_token':request.headers.get("X-Refresh-Token")}

app.include_router(auth.router)
app.include_router(twofactor.router)
app.include_router(user.router)
app.include_router(customer.router)
app.include_router(contact.router)
app.include_router(product.router)
app.include_router(distributor.router)
app.include_router(order.router)
app.include_router(leads.router)
app.include_router(opportunity.router)
app.include_router(drop_downs.router)
app.include_router(dashboard.router)

#Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=["*"],
    allow_credentials=True
)