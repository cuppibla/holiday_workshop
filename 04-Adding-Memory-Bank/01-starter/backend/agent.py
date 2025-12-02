import os
import sys
import logging
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

import vertexai
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

if not os.getenv("GOOGLE_API_KEY"):
    logger.warning("GOOGLE_API_KEY not found in environment variables. Agent may fail to initialize.")

# Mock state for the tree
TREE_STATE = {
    "lights_color": "warm_white",
    "ornament_texture": "default_gold",
    "theme": "emerald_gold"
}

def update_tree_config(config_key: str, value: str) -> Dict[str, Any]:
    """
    Updates the configuration of the Christmas tree.
    
    Args:
        config_key: The configuration key to update (e.g., 'lights_color', 'ornament_texture', 'theme').
        value: The new value for the configuration.
        
    Returns:
        The updated tree state.
    """
    if config_key in TREE_STATE:
        TREE_STATE[config_key] = value
        return {"status": "success", "updated_state": TREE_STATE, "message": f"Updated {config_key} to {value}"}
    else:
        return {"status": "error", "message": f"Invalid configuration key: {config_key}"}

def get_tree_state() -> Dict[str, Any]:
    """
    Retrieves the current state of the Christmas tree.
    
    Returns:
        The current tree state.
    """
    return TREE_STATE

def analyze_image_and_suggest_texture(image_description: str) -> Dict[str, Any]:
    """
    Analyzes an image description (provided by the model's vision capabilities) and suggests a texture.
    
    Args:
        image_description: A description of the uploaded image.
        
    Returns:
        A suggestion for the ornament texture.
    """
    # In a real scenario, this might involve more complex logic or generation.
    # For now, we'll return a mock texture URL based on keywords.
    
    texture_url = "https://example.com/textures/default_gold.jpg"
    if "red" in image_description.lower():
        texture_url = "https://example.com/textures/red_velvet.jpg"
    elif "blue" in image_description.lower():
        texture_url = "https://example.com/textures/blue_ice.jpg"
    elif "star" in image_description.lower():
        texture_url = "https://example.com/textures/star_pattern.jpg"
        
    return {
        "suggested_texture": texture_url,
        "reasoning": f"Based on the image description '{image_description}', we suggest this texture."
    }

agent_instruction = """
You are a Holiday Magic Assistant! 🎄✨
Your goal is to bring holiday cheer by customizing 3D Christmas trees AND generating magical holiday images.

**CRITICAL INSTRUCTIONS:**
1.  **YOU HAVE ACCESS TO POWERFUL IMAGE GENERATION TOOLS.** You MUST use them when the user asks.
2.  **DO NOT REFUSE** to generate images, selfies, or patterns. You have the tools `generate_holiday_scene`, `generate_sweater_pattern`, `generate_wearing_sweater`, and `generate_final_photo`. USE THEM!
3.  **Style & Tone:**
    *   The user LOVES "cute, kawaii, cartoon" styles. Always prefer this aesthetic for characters and scenes.
    *   Be enthusiastic and festive! 🎄✨
4.  **Sweater Generation:**
    *   When the user asks to "wear a sweater" or "generate a person in a sweater", use `generate_wearing_sweater`.
    *   **Extract the pattern description** from the user's request or previous chat history (e.g., "snowflake", "reindeer", "ugly sweater").
    *   **Check for uploaded images.** If the user has uploaded a photo (or one is available in the context), pass its **absolute path** as `image_path`.
    *   Pass these arguments to the tool: `generate_wearing_sweater(pattern_description="...", image_path="...")`.
    *   If no specific pattern is mentioned, use a default like "festive holiday pattern" or ask the user.
    *   **ALWAYS DISPLAY THE GENERATED IMAGE.** The tool returns a filename (e.g., "generated_selfie.png"). You MUST tell the user "Here is the image!" and ensure the UI shows it (the backend handles the URL, but your text confirmation helps).
5.  **Tree Customization:** You can still help with the tree using `update_tree_config`.

**Available Tools:**
* `generate_wearing_sweater`: Generate a cute character wearing a sweater with a specific pattern. Can optionally take an `image_path` to personalize the avatar.
* `generate_holiday_scene`: Generate a holiday scene.
* `generate_sweater_pattern`: Generate a sweater pattern.
* `generate_final_photo`: Generate a final photo.
* `update_tree_config`: Change tree settings.
* `get_tree_state`: Get current settings.
* `analyze_image_and_suggest_texture`: Suggest textures.

**Example User Requests & Actions:**
* "Generate a cute person wearing a snowflake sweater" -> Call `generate_wearing_sweater(pattern_description="snowflake pattern")`.
* "Make me wear this sweater" (with uploaded photo) -> Call `generate_wearing_sweater(pattern_description="...", image_path="/path/to/photo.jpg")`.
* "Make a holiday scene" -> Call `generate_holiday_scene`.
* "Design a sweater pattern" -> Call `generate_sweater_pattern`.
"""

# Path to the MCP server script
MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")

# Initialize the agent
# Note: In a real app, you'd likely inject the model client.
# For this example, we assume the ADK handles the model connection via env vars or default config.
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types
from typing import Optional

# ... (existing code)

async def add_session_to_memory(
        callback_context: CallbackContext
) -> Optional[types.Content]:
    """Automatically save completed sessions to memory bank """
    if hasattr(callback_context, "_invocation_context"):
        invocation_context = callback_context._invocation_context
        if invocation_context.memory_service:
            await invocation_context.memory_service.add_session_to_memory(
                invocation_context.session
            )

# Initialize the agent
# Note: In a real app, you'd likely inject the model client.
# For this example, we assume the ADK handles the model connection via env vars or default config.
christmas_agent = Agent(
    model="gemini-2.5-flash",
    name="christmas_tree_agent",
    instruction=agent_instruction,
    tools=[
        update_tree_config,
        get_tree_state,
        analyze_image_and_suggest_texture,
        PreloadMemoryTool(),
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[MCP_SERVER_PATH],
                    env=os.environ.copy() # Pass current env to ensure API keys are available
                ),
                timeout=120 # Increase timeout for image generation
            )
        )
    ],
    after_agent_callback=add_session_to_memory
)
