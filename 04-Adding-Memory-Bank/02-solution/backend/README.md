# Smart Christmas Tree Backend

This is the backend service for the Smart Christmas Tree application, powered by Google Vertex AI and the Agent Development Kit (ADK).

## Prerequisites

- Python 3.11+
- `uv` (Python package installer and runner)
- Google Cloud SDK (`gcloud`) authenticated with a project that has Vertex AI enabled.

## Setup

1.  **Environment Variables**:
    Ensure you have a `.env` file in this directory with the following variables:
    ```env
    PROJECT_ID=your-google-cloud-project-id
    LOCATION=us-central1
    AGENT_ENGINE_ID=your-agent-engine-id
    GOOGLE_API_KEY=your-gemini-api-key
    ```

2.  **Agent Engine Registration**:
    If you haven't registered an Agent Engine yet (or if `AGENT_ENGINE_ID` is missing), run the deployment script:
    ```bash
    uv run deploy_agent.py
    ```
    This script will:
    - Initialize Vertex AI.
    - Create an Agent Engine resource.
    - Output the `AGENT_ENGINE_ID` which you must add to your `.env` file.

## Running the Backend

To start the backend server with hot-reloading:

```bash
uv run uvicorn main:app --reload --port 8001
```

The API will be available at `http://localhost:8001`.

## API Endpoints

-   `POST /api/chat`: Send a message to the Christmas Tree Agent.
-   `GET /api/state`: Get the current visual state of the tree.


frontend/
 npm run dev