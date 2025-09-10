from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from .database import create_tables

from .routers import companies, predictions, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and pre-load ML models on startup"""
    print("🚀 Starting FastAPI server...")
    print("📊 Initializing database...")
    try:
        create_tables()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
    
    print("🤖 Pre-loading ML models...")
    try:
        from .ml_service import ml_service
        test_ratios = {
            "debt_to_equity_ratio": 0.5,
            "current_ratio": 2.0,
            "quick_ratio": 1.5,
            "return_on_equity": 0.15,
            "return_on_assets": 0.08,
            "profit_margin": 0.10,
            "interest_coverage": 5.0,
            "fixed_asset_turnover": 1.2,
            "total_debt_ebitda": 2.5
        }
        ml_service.predict_default_probability(test_ratios)
        print("✅ ML models pre-loaded successfully")
    except Exception as e:
        print(f"⚠️ ML model pre-loading warning: {e}")
    
    yield
    
    print("🛑 Shutting down FastAPI server...")

app = FastAPI(
    title="Financial Default Risk Prediction API",
    description="FastAPI server for predicting corporate default risk using machine learning",
    version="1.0.0",
    docs_url="/docs" if os.getenv("DEBUG", "False").lower() == "true" else None,
    redoc_url="/redoc" if os.getenv("DEBUG", "False").lower() == "true" else None,
    lifespan=lifespan
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["authentication"]
)

app.include_router(
    companies.router,
    prefix="/api/companies",
    tags=["companies"]
)

app.include_router(
    predictions.router,
    prefix="/api/predictions",
    tags=["predictions"]
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Financial Default Risk Prediction API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "OK",
        "message": "Server is running",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    print(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if os.getenv("DEBUG") == "True" else "An error occurred"
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    print(f"🚀 Starting server on port {port}")
    print(f"📚 API docs: http://localhost:{port}/docs")
    
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
        access_log=True
    )