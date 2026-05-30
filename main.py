"""FastAPI application entry point for the Travel Research Agent."""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from models.schemas import ResearchRequest, ResearchResponse
from agent.orchestrator import TravelResearchOrchestrator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: TravelResearchOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize services on startup."""
    global orchestrator
    port = os.getenv("APP_PORT", "8000")
    logger.info(f"Travel Research Agent starting on port {port}...")
    orchestrator = TravelResearchOrchestrator()
    logger.info("All services initialized successfully")
    yield
    logger.info("Travel Research Agent shutting down")


app = FastAPI(
    title="Travel Research Agent",
    description="AI-powered travel research assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    """Generate a travel brief for a destination."""
    logger.info(f"Received research request for: {request.destination}")
    result = await orchestrator.run(request)
    return result


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the web UI."""
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    print(f"\n Travel Research Agent starting on http://localhost:{port}")
    print(f" API docs available at http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
