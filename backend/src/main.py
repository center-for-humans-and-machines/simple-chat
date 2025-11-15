import motor.motor_asyncio
import sentry_sdk
from beanie import init_beanie
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langfuse import Langfuse
from src.models import __beanie_models__, get_settings
from src.routes.dashboard import dashboard_router
from src.routes.download import download_router
from src.routes.llm import llm_router
from src.routes.project import project_router
from src.routes.socket_setup import sio_app
from src.utils.logging import setup_logger

# SETUP

logger = setup_logger(__name__)

settings = get_settings()

if settings.sentry_enabled and settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        # Skip sending PII data
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=False,
    )

if settings.langfuse_enabled and settings.langfuse_public_key and settings.langfuse_secret_key:
    langfuse_client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
else:
    langfuse_client = None


app = FastAPI()
app.mount("/ws", app=sio_app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(project_router)
app.include_router(download_router)
app.include_router(llm_router)
app.include_router(dashboard_router)


# Initialize database
async def init_db():
    # Create an asynchronous MongoDB client
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
    database = client[settings.database_name]

    # Initialize Beanie ODM with the MongoDB database
    await init_beanie(database=database, document_models=__beanie_models__)


# Startup event to initialize the database
@app.on_event("startup")
async def startup_event():
    logger.info("Startup event started")
    await init_db()
