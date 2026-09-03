"""
RecoverAI - Main FastAPI Application
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION, CORS_ORIGINS
from app.db.session import init_db
from app.api.router import api_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager: handles database startup and schema verification.
    """
    init_db()
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers for clean, professional client error responses
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "message": "The submitted request data failed schema validation.",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Hide internal Python stack traces from clients
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred while processing the request.",
            "type": exc.__class__.__name__,
        },
    )


# Mount Master API router under /api
app.include_router(api_router, prefix="/api")


@app.get("/api-info", tags=["System"])
def api_info():
    """
    Returns API system metadata.
    """
    return {
        "platform": APP_TITLE,
        "description": APP_DESCRIPTION,
        "version": APP_VERSION,
        "status": "OPERATIONAL",
        "documentation": "/docs",
        "api_root": "/api",
    }


# Mount Static Frontend if directory exists
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    @app.get("/style.css", include_in_schema=False)
    def get_style():
        return FileResponse(FRONTEND_DIR / "style.css")

    @app.get("/script.js", include_in_schema=False)
    def get_script():
        return FileResponse(FRONTEND_DIR / "script.js")

    @app.get("/", include_in_schema=False)
    def get_index():
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    def root_status():
        return api_info()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
