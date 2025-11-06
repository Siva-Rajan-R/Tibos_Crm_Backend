from fastapi import FastAPI,Request
from api.routes import auth,contact,customer,order,product
from crud.auth_crud import AuthCrud
from fastapi.middleware.cors import CORSMiddleware
from database.configs.pg_config import init_pg_db
from database.configs.redis_config import check_redis_health,redis_client
from services.email_service import check_email_service_health
from icecream import ic
import sys,subprocess,asyncio
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
load_dotenv()

# changing event loop for better permformance *It works only on (linux,macos)
if sys.platform!="win32":
    uvloop_install_cmd=["pip","install","uvloop"]
    uvloop_exc_process=subprocess.Popen(uvloop_install_cmd)
    uvloop_exc_process.wait()
    ic("✅ Uvloop Installed Successfully")

    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    ic("✅ Event loop policy Changed Successfully")


# Controlling app startups to endup Lifecycle
@asynccontextmanager
async def api_lifespan(app:FastAPI):
    try:
        ic("🏎️ Executing API Lifespan... ")
        await init_pg_db()
        AuthCrud().init_superadmin()
        await check_email_service_health()
        await check_redis_health()
        yield
    except Exception as e:
        ic(f"❌ Error At Executing API Lifespan {e}")
    finally:
        ic("🌵 Shuttingdown API Lifespan")


# Hiding Dev Urls For Production
ENVIRONMENT=os.getenv("ENVIRONMENT",'production').lower()
openapi_url='/openapi.json'
docs='/docs'
redoc='/redoc'
debug=True

if ENVIRONMENT=="production":
    openapi_url=None
    docs=None
    redoc=None
    debug=False


app=FastAPI(lifespan=api_lifespan,openapi_url=openapi_url,docs_url=docs,redoc_url=redoc,debug=debug)

# Routers
@app.get('/')
def home_root(request:Request):
    return {"accesss token":request.headers.get("X-Access-Token"),'refresh_token':request.headers.get("X-Refresh-Token")}
app.include_router(auth.router)
app.include_router(contact.router)
app.include_router(customer.router)
app.include_router(order.router)
app.include_router(product.router)


#Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=["*"],
    allow_credentials=True
)