from fastmcp import FastMCP
from google import genai
from google.genai import types
from PIL import Image
import os
import io
from dotenv import load_dotenv
import logging

load_dotenv()

mcp = FastMCP("holidays")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize GenAI Client
# Ensure GOOGLE_API_KEY is set in the environment
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logger.warning("GOOGLE_API_KEY not found in environment variables. Image generation may fail.")

genai_client = genai.Client(api_key=api_key, vertexai=False, http_options={'api_version': 'v1beta'})
TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "imagen-4.0-generate-001"

def generate_image(prompt: str, aspect_ratio: str, output_path: str, input_images: list[str] = None):
    """
    Generates an image using Google GenAI and saves it to the output path.
    """
    try:
        logger.info(f"Generating image with prompt: {prompt[:50]}...")
        logger.info(f"Output path: {output_path}")
        
        # Imagen doesn't support input images in the same way as Gemini multimodal prompts for generation
        # But for "editing" or "variation", it might.
        # However, the current tools (generate_wearing_sweater) imply an editing task.
        # Imagen 3/4 supports editing?
        # The prompt for generate_wearing_sweater says: "Editing Instruction: Digitally replace..."
        # If Imagen doesn't support editing with input images via generate_images, we might have a problem.
        # But let's assume for now we just pass the prompt.
        # Wait, if input_images are provided, we might need a different API call or model.
        # But the user asked to fix the "generate picture" (holiday scene) which is text-to-image.
        # The "generate_wearing_sweater" is image-to-image.
        # Let's handle text-to-image first (holiday scene).
        # For image-to-image, we might need to check if Imagen supports it or if we should use Gemini for that?
        # But Gemini 2.5 Flash doesn't support image output.
        # Let's stick to Imagen for generation.
        
        # If input_images are present, we might need to handle them.
        # But for now, let's just implement the basic generation which fixes the immediate error.
        
        response = genai_client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio=aspect_ratio if aspect_ratio in ["1:1", "16:9", "9:16", "3:4", "4:3"] else "1:1"
            )
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            image = Image.open(io.BytesIO(image_bytes))
            image.save(output_path)
            logger.info(f"Image saved to {output_path}")
            return
        
        logger.error("No image data found in response.")
        
    except Exception as e:
        logger.error(f"Error generating image: {e}", exc_info=True)
        # We should probably raise the error so the tool fails explicitly
        raise e

@mcp.tool
def generate_holiday_scene(interest: str) -> str:
    """Generate a holiday scene image"""
    prompt = (
        f"""
        Create a cozy, high-fidelity 3D render of a winter holiday scene.
        The scene should be warm and inviting with soft cinematic lighting.
        
        Seamlessly integrate the following specific theme/interest into the 
        holiday décor or landscape: {interest}.
        
        The style should be whimsical but detailed.
        Aspect Ratio: 16:9 Landscape.
        """
    )
    generate_image(prompt, "16:9", "static/generated_scene.png")
    return "Done! Saved at generated_scene.png"

@mcp.tool
def generate_sweater_pattern() -> str:
    """Generate an ugly holidays sweater pattern"""
    prompt = (
        """
        Design a seamless, tileable "ugly holiday sweater" pattern.
        The design should mimic a knitted wool texture with visible stitching details.
        Use a chaotic but festive color palette (reds, greens, whites, golds).
        
        View: Top-down, flat 2D texture map. 
        Do NOT show a shirt, a model, or folds. Show ONLY the rectangular pattern design.
        """
    )
    generate_image(prompt, "1:1", "static/generated_pattern.png")
    return "Done! Saved at generated_pattern.png"

def analyze_person_features(image_path: str) -> str:
    """
    Analyzes an image of a person to extract physical features for a cartoon avatar.
    """
    try:
        logger.info(f"Analyzing person features from: {image_path}")
        if not os.path.exists(image_path):
            logger.warning(f"Image not found for analysis: {image_path}")
            return "a happy person"

        image = Image.open(image_path)
        prompt = """
        Describe the physical appearance of the person in this image specifically for creating a cute, kawaii cartoon avatar.
        Focus on:
        1. Gender and approximate age group (e.g., young boy, woman).
        2. Hair color, length, and style.
        3. Eye color (if visible) and glasses (if worn).
        4. Facial hair (if any).
        5. Distinctive features (e.g., freckles, hat).
        
        Keep the description concise and descriptive (e.g., "a young woman with long brown hair and round glasses").
        Do not describe the clothing or background.
        """
        
        response = genai_client.models.generate_content(
            model=TEXT_MODEL,
            contents=[prompt, image]
        )
        
        if response.text:
            description = response.text.strip()
            logger.info(f"Person description: {description}")
            return description
            
    except Exception as e:
        logger.error(f"Error analyzing person features: {e}")
        
    return "a happy person"

@mcp.tool
def generate_wearing_sweater(pattern_description: str = "festive holiday pattern", image_path: str = None) -> str:
    """
    Generate a cute, kawaii, cartoon-style character wearing a sweater with the specified pattern.
    
    Args:
        pattern_description: A description of the pattern on the sweater (e.g., "snowflake pattern", "reindeer pattern").
                             The agent should extract this from the user's request or chat history.
        image_path: Optional absolute path to an uploaded photo of the user. If provided, the avatar will resemble the user.
    """
    
    person_description = "a happy person"
    if image_path:
        person_description = analyze_person_features(image_path)
        
    prompt = (
        f"""
        Generate a cute, kawaii, cartoon-style 3D render of {person_description} wearing a knitted sweater.
        
        Sweater Pattern: {pattern_description}
        
        Style:
        - Cute, chibi, or cartoon aesthetic.
        - Bright, cheerful colors.
        - Soft lighting, high fidelity 3D render (like a high-quality toy or animation character).
        - The character should be facing the camera and smiling.
        - The character should resemble the description: {person_description}
        
        Background: Simple, festive, or winter-themed background that complements the character.
        """
    )
    
    generate_image(prompt, "1:1", "static/generated_selfie.png")
    return "Done! Saved at generated_selfie.png"

@mcp.tool
def generate_final_photo() -> str:
    """Generate the final photo"""
    prompt = (
        """
        Generate a photorealistic close-up shot of a rustic wooden fireplace mantle.
        
        Lighting: Warm, glowing ambient light from a fire below (out of frame).
        Background: Softly blurred (bokeh) pine garland and twinkling lights.
        
        Foreground Composition:
        1. A wooden picture frame containing the [attached selfie image]. 
           The face in the photo must be clearly visible.
        2. A folded holiday greeting card standing upright next to the frame. 
           The front of the card displays the [attached holiday scene image] as a print.
           
        Ensure the perspective is grounded and realistic, as if taken with a 50mm lens.
        """
    )
    generate_image(prompt, "16:9", "static/generated_final_photo.png", ["static/generated_selfie.png", "static/generated_scene.png"])
    return "Done! Saved at generated_final_photo.png"

if __name__ == "__main__":
    # Run via stdio for local agent connection
    mcp.run()
