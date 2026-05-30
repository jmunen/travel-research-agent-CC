# 🌍 Travel Research Agent

An AI-powered travel research assistant that generates comprehensive travel briefs by combining web research with AI summarization.

## How It Works

```
┌──────────┐     ┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────┐
│   User   │────▶│  FastAPI  │────▶│    Apify    │────▶│   Bedrock    │────▶│   Box   │
│ (Request)│     │  Server   │     │  (Scraping) │     │   (Claude)   │     │ (Upload)│
└──────────┘     └──────────┘     └─────────────┘     └──────────────┘     └─────────┘
                       │                                                          │
                       │◀─────────────────────────────────────────────────────────│
                       │              Response with Box file link                  │
                       ▼
                 ┌──────────┐
                 │   User   │
                 │(Response)│
                 └──────────┘
```

**Pipeline:**
1. User submits a destination + optional preferences
2. Apify scrapes Google for travel data (attractions, restaurants, tips)
3. Amazon Bedrock Claude synthesizes the data into a polished travel brief
4. The brief is uploaded to Box as a Markdown file
5. User receives a confirmation with a link to the file

## Prerequisites

- **Python 3.11+**
- **Apify account** — [Sign up](https://apify.com/) and get your API token
- **AWS account** — With Amazon Bedrock access enabled for Claude models
- **Box developer account** — [Sign up](https://developer.box.com/) and create an app for a developer token

## Setup

### 1. Clone the repository

```bash
git clone <repo-url>
cd travel-research-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Description |
|----------|-------------|
| `APIFY_API_TOKEN` | Your Apify API token from [Apify Console](https://console.apify.com/account/integrations) |
| `AWS_ACCESS_KEY_ID` | AWS access key with Bedrock permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `BEDROCK_MODEL_ID` | Claude model ID (default: `anthropic.claude-3-5-sonnet-20241022-v2:0`) |
| `BOX_CLIENT_ID` | Box app client ID |
| `BOX_CLIENT_SECRET` | Box app client secret |
| `BOX_ACCESS_TOKEN` | Box developer token (expires every 60 min) |
| `BOX_FOLDER_ID` | Box folder ID to upload to (`0` = root) |

## Running the App

```bash
uvicorn main:app --reload --port 8000
```

Or simply:

```bash
python main.py
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

## API Documentation

Interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Endpoints

#### `POST /research`

Generate a travel brief for a destination.

**Request Body:**

```json
{
  "destination": "Tokyo, Japan",
  "preferences": {
    "trip_length": "7 days",
    "budget_level": "mid-range",
    "travel_style": ["cultural", "food"],
    "food_interests": ["ramen", "sushi", "street food"],
    "group_type": "couple"
  }
}
```

**Response:**

```json
{
  "success": true,
  "destination": "Tokyo, Japan",
  "box_file_id": "123456789",
  "box_file_name": "travel_brief_tokyo_japan_20250115_143022.md",
  "box_file_url": "https://app.box.com/s/abc123...",
  "brief_preview": "# Travel Brief: Tokyo, Japan\n\n## 1. Destination Overview\n\nTokyo is a mesmerizing blend of...",
  "message": "Travel brief generated and uploaded successfully for Tokyo, Japan!"
}
```

#### `GET /health`

Health check endpoint.

```json
{"status": "ok"}
```

#### `GET /`

Web UI with a form to submit research requests.

## Getting API Tokens

### Apify
1. Create an account at [apify.com](https://apify.com)
2. Go to **Settings → Integrations**
3. Copy your **Personal API Token**

### AWS Bedrock
1. Ensure your AWS account has Bedrock access enabled
2. In the Bedrock console, request access to Claude models
3. Create an IAM user with `bedrock:InvokeModel` permission
4. Generate access keys for the IAM user

### Box
1. Create a developer account at [developer.box.com](https://developer.box.com)
2. Create a new **Custom App** with **Server Authentication (Client Credentials Grant)**
3. In the app's Configuration tab, find your Client ID and Client Secret
4. Generate a **Developer Token** (valid for 60 minutes) for testing
5. Note: For production, implement the full OAuth2 flow

## Project Structure

```
travel-research-agent/
├── .env.example              # Environment variable template
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── main.py                   # FastAPI app entry point
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py       # Main agent orchestration logic
│   ├── apify_collector.py    # Apify web scraping integration
│   ├── ai_summarizer.py      # Bedrock Claude summarization
│   └── box_exporter.py       # Box file upload integration
├── models/
│   ├── __init__.py
│   └── schemas.py            # Pydantic request/response models
└── utils/
    ├── __init__.py
    └── prompt_builder.py     # Builds AI prompts from collected data
```

## Notes

- The Box developer token expires every 60 minutes. For production use, implement the full OAuth2 refresh flow.
- Apify actor runs consume compute units from your Apify plan.
- Bedrock Claude calls are billed per token by AWS.
- The agent limits searches to 3 queries with 5 results each to balance speed and cost.

## License

MIT
