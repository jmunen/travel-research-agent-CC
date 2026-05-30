"""FastAPI application entry point for the Travel Research Agent."""

import os
import logging
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
    logger.info(f"🌍 Travel Research Agent starting on port {port}...")
    orchestrator = TravelResearchOrchestrator()
    logger.info("✅ All services initialized successfully")
    yield
    logger.info("👋 Travel Research Agent shutting down")


app = FastAPI(
    title="Travel Research Agent",
    description="AI-powered travel research assistant that generates comprehensive travel briefs",
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
    """
    Generate a comprehensive travel brief for a destination.

    Takes a destination and optional preferences, researches the web,
    generates an AI-powered travel brief, and uploads it to Box.
    """
    logger.info(f"Received research request for: {request.destination}")
    result = await orchestrator.run(request)
    return result


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the web UI for the Travel Research Agent."""
    return HTML_PAGE


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Research Agent</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }
        .container {
            max-width: 700px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 0.5rem;
            font-size: 2rem;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
            font-size: 0.95rem;
        }
        .form-group {
            margin-bottom: 1.25rem;
        }
        label {
            display: block;
            margin-bottom: 0.4rem;
            color: #444;
            font-weight: 500;
            font-size: 0.9rem;
        }
        input, select {
            width: 100%;
            padding: 0.7rem 1rem;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 0.95rem;
            transition: border-color 0.2s;
        }
        input:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }
        button {
            width: 100%;
            padding: 0.9rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.05rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.1s, box-shadow 0.2s;
            margin-top: 0.5rem;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        .result {
            margin-top: 2rem;
            padding: 1.5rem;
            border-radius: 10px;
            display: none;
        }
        .result.success {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            display: block;
        }
        .result.error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            display: block;
        }
        .result h3 {
            margin-bottom: 0.75rem;
            color: #333;
        }
        .result p {
            color: #555;
            line-height: 1.6;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }
        .result a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        .result a:hover {
            text-decoration: underline;
        }
        .preview {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 1rem;
            margin-top: 0.75rem;
            font-size: 0.85rem;
            color: #475569;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            display: none;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Travel Research Agent</h1>
        <p class="subtitle">AI-powered travel research assistant. Enter a destination to generate a comprehensive travel brief.</p>

        <form id="researchForm">
            <div class="form-group">
                <label for="destination">Destination *</label>
                <input type="text" id="destination" name="destination" placeholder="e.g. Tokyo, Japan" required>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="trip_length">Trip Length</label>
                    <input type="text" id="trip_length" name="trip_length" placeholder="e.g. 7 days">
                </div>
                <div class="form-group">
                    <label for="budget_level">Budget Level</label>
                    <select id="budget_level" name="budget_level">
                        <option value="">-- Select --</option>
                        <option value="budget">Budget</option>
                        <option value="mid-range">Mid-Range</option>
                        <option value="luxury">Luxury</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label for="travel_style">Travel Style</label>
                    <input type="text" id="travel_style" name="travel_style" placeholder="adventure, cultural, relaxation">
                </div>
                <div class="form-group">
                    <label for="food_interests">Food Interests</label>
                    <input type="text" id="food_interests" name="food_interests" placeholder="street food, fine dining">
                </div>
            </div>

            <div class="form-group">
                <label for="group_type">Group Type</label>
                <select id="group_type" name="group_type">
                    <option value="">-- Select --</option>
                    <option value="solo">Solo</option>
                    <option value="couple">Couple</option>
                    <option value="friends">Friends</option>
                    <option value="family">Family</option>
                </select>
            </div>

            <button type="submit" id="submitBtn">Generate Travel Brief</button>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Researching your destination... This may take 1-2 minutes.</p>
        </div>

        <div class="result" id="result"></div>
    </div>

    <script>
        document.getElementById('researchForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = document.getElementById('submitBtn');
            const loading = document.getElementById('loading');
            const resultDiv = document.getElementById('result');

            // Reset UI
            submitBtn.disabled = true;
            loading.classList.add('active');
            resultDiv.className = 'result';
            resultDiv.style.display = 'none';

            // Build request body
            const destination = document.getElementById('destination').value;
            const tripLength = document.getElementById('trip_length').value;
            const budgetLevel = document.getElementById('budget_level').value;
            const travelStyle = document.getElementById('travel_style').value;
            const foodInterests = document.getElementById('food_interests').value;
            const groupType = document.getElementById('group_type').value;

            const preferences = {};
            if (tripLength) preferences.trip_length = tripLength;
            if (budgetLevel) preferences.budget_level = budgetLevel;
            if (travelStyle) preferences.travel_style = travelStyle.split(',').map(s => s.trim()).filter(s => s);
            if (foodInterests) preferences.food_interests = foodInterests.split(',').map(s => s.trim()).filter(s => s);
            if (groupType) preferences.group_type = groupType;

            const body = {
                destination: destination,
                preferences: Object.keys(preferences).length > 0 ? preferences : null
            };

            try {
                const response = await fetch('/research', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body)
                });

                const data = await response.json();

                if (data.success) {
                    let html = `<h3>✅ Research Complete!</h3>`;
                    html += `<p><strong>Destination:</strong> ${data.destination}</p>`;
                    html += `<p><strong>Message:</strong> ${data.message}</p>`;

                    if (data.box_file_url) {
                        html += `<p><strong>File:</strong> <a href="${data.box_file_url}" target="_blank">${data.box_file_name}</a></p>`;
                    } else if (data.box_file_name) {
                        html += `<p><strong>File:</strong> ${data.box_file_name}</p>`;
                    }

                    if (data.brief_preview) {
                        html += `<div class="preview">${data.brief_preview}...</div>`;
                    }

                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<h3>❌ Error</h3><p>${data.message}</p>`;
                }
            } catch (err) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `<h3>❌ Error</h3><p>Request failed: ${err.message}</p>`;
            } finally {
                submitBtn.disabled = false;
                loading.classList.remove('active');
            }
        });
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("APP_PORT", "8000"))
    print(f"\n🌍 Travel Research Agent starting on http://localhost:{port}")
    print(f"📖 API docs available at http://localhost:{port}/docs\n")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
