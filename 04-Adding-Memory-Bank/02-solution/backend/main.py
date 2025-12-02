import os
import time
import logging
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import vertexai
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.genai import types
from agent import christmas_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

if not PROJECT_ID:
    logger.warning("PROJECT_ID not found in environment variables. Vertex AI services may fail.")

# Initialize Vertex AI
if PROJECT_ID:
    # If we are using Vertex AI (implied by PROJECT_ID), we should ensure GOOGLE_API_KEY is not set
    # to avoid "Project/location and API key are mutually exclusive" error in some SDK versions.
    if "GOOGLE_API_KEY" in os.environ:
        logger.info("Unsetting GOOGLE_API_KEY to avoid conflict with Vertex AI Project/Location configuration.")
        del os.environ["GOOGLE_API_KEY"]

    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

app = FastAPI(title="Smart Christmas Tree API")

# Mount static directory for serving images
# Ensure directory exists
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    image_data: Optional[str] = None # Base64 string if needed, or handle via multipart

class ChatResponse(BaseModel):
    response: str
    tree_state: dict
    generated_image: Optional[str] = None

# Initialize ADK services with Vertex AI
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID")

if AGENT_ENGINE_ID:
    logger.info(f"Using Agent Engine ID: {AGENT_ENGINE_ID}")
    session_service = VertexAiSessionService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )
    memory_service = VertexAiMemoryBankService(
        project=PROJECT_ID, location=LOCATION, agent_engine_id=AGENT_ENGINE_ID
    )
else:
    logger.warning("AGENT_ENGINE_ID not found. Falling back to InMemory services.")
    from google.adk.sessions import InMemorySessionService
    from google.adk.memory import InMemoryMemoryService
    session_service = InMemorySessionService()
    memory_service = InMemoryMemoryService()

# Initialize Runner
runner = Runner(
    app_name="agents",
    agent=christmas_agent,
    session_service=session_service,
    memory_service=memory_service,
)

# Global variable to store the current session ID
CURRENT_SESSION_ID = None

@app.post("/api/chat")
async def chat_endpoint(
    message: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    Chat endpoint that accepts text and an optional image file.
    """
    print("DEBUG: chat_endpoint called! Code has been reloaded.")
    global CURRENT_SESSION_ID
    
    try:
        user_input = message
        uploaded_file_path = None
        
        if file:
            # Save the uploaded file
            file_location = f"static/uploads/{file.filename}"
            # Use absolute path for the agent
            abs_file_location = os.path.abspath(file_location)
            
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(file.file, file_object)
            
            uploaded_file_path = abs_file_location
            logger.info(f"File saved to {abs_file_location}")
            
            # Inject file path into the user message for the agent
            user_input += f"\n[System: User uploaded an image. It is saved at: {abs_file_location}]"
        
        user_id = "demo_user"
        session = None
        
        # Try to retrieve existing session if we have an ID
        if CURRENT_SESSION_ID:
            try:
                t0 = time.time()
                session = await session_service.get_session(app_name="agents", session_id=CURRENT_SESSION_ID, user_id=user_id)
                logger.info(f"Session retrieval took {time.time() - t0:.4f}s")
                logger.info(f"Session found: {session.id}")
            except Exception as e:
                logger.warning(f"Failed to retrieve session {CURRENT_SESSION_ID}: {e}")
                CURRENT_SESSION_ID = None
        
        # Create new session if needed
        if not session:
            try:
                t0 = time.time()
                if isinstance(session_service, VertexAiSessionService):
                     session = await session_service.create_session(app_name="agents", user_id=user_id)
                else:
                     session = await session_service.create_session(app_name="agents", session_id="demo_session", user_id=user_id)
                
                logger.info(f"Session creation took {time.time() - t0:.4f}s")
                CURRENT_SESSION_ID = session.id
                logger.info(f"New session created: {session.id}")
            except Exception as e:
                logger.error(f"Failed to create session: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")
        
        session_id = CURRENT_SESSION_ID
        
        logger.info(f"Calling runner.run with session_id={session_id}")

        # Create content object
        content = types.Content(role="user", parts=[{"text": user_input}])
        
        # Run the agent via the runner
        start_time = time.time()
        logger.info(f"Starting runner.run at {start_time}")
        
        events = runner.run(
            user_id=user_id,
            session_id=session_id, 
            new_message=content
        )
        logger.info(f"runner.run initialized in {time.time() - start_time:.4f}s")
        
        final_response_text = ""
        generated_image_url = None
        
        # Iterate through events to find the final response
        for event in events:
            logger.info(f"Event received: {type(event)} - {event}")
            if event.is_final_response():
                # Extract text from the final response
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                    
                    # Check for generated image in the response text OR if a new file was created recently
                    # The agent/tool should return the path or filename
                    # We look for "Saved at [filename]" pattern from the tool output
                    # Or we can check the static directory for new files?
                    # Better: The tool returns "Done! Saved at [filename]".
                    # The agent might repeat this.
                    
                    # Simple heuristic: Look for known generated filenames in the text
                    # generated_scene.png, generated_pattern.png, generated_selfie.png, generated_final_photo.png
                    known_files = ["generated_scene.png", "generated_pattern.png", "generated_selfie.png", "generated_final_photo.png"]
                    
                    # Check if any of these files were modified recently (within last 10 seconds)
                    # This is more robust than relying on the agent's text response
                    for filename in known_files:
                        filepath = os.path.join("static", filename)
                        if os.path.exists(filepath):
                            mtime = os.path.getmtime(filepath)
                            if time.time() - mtime < 10: # Modified in last 10 seconds
                                logger.info(f"Detected recently generated file: {filename}")
                                # Construct URL
                                # Assuming backend runs on port 8001
                                generated_image_url = f"http://localhost:8001/static/{filename}"
                                # Add a cache buster
                                generated_image_url += f"?t={int(time.time())}"
                                break
                    
                    # Fallback: Check text if file check didn't find anything (though file check should cover it)
                    if not generated_image_url:
                        for filename in known_files:
                            if filename in final_response_text:
                                # Construct URL
                                generated_image_url = f"http://localhost:8001/static/{filename}"
                                generated_image_url += f"?t={int(time.time())}"
                                break
        
        if not final_response_text:
            final_response_text = "I'm sorry, I didn't get a response."

        # Get the latest tree state to return to frontend
        from agent import get_tree_state
        current_state = get_tree_state()
        
        return {
            "response": final_response_text,
            "tree_state": current_state,
            "generated_image": generated_image_url
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/state")
async def get_state():
    from agent import get_tree_state
    return get_tree_state()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
