from fastmcp import FastMCP
from google import genai
from google.genai import types
from PIL import Image
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

mcp = FastMCP("holidays")

genai_client = genai.Client()
TEXT_MODEL = "gemini-2.5-flash"
IMAGE_MODEL = "gemini-2.5-flash-image"

def generate_image(prompt: str, aspect_ratio: str, output_path: str, input_images=[]):
    """Take a prompt and input images (if any) and generate and save a resulting image using a model."""
    logger.info(f"Generating image with prompt: {prompt[:50]}...")
    logger.info(f"Output path: {output_path}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    contents = [prompt]
    for image in input_images:
        contents.append(Image.open(image))

    response = genai_client.models.generate_content(
        model=IMAGE_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            image_config=types.ImageConfig(
                aspect_ratio=aspect_ratio,
            )
        )
    )
    for part in response.parts:
        if part.text is not None:
            print(part.text)
        elif part.inline_data is not None:
            image = part.as_image()
            image.save(output_path)

@mcp.tool
def generate_holiday_scene(interest: str) -> str:
    """
    Generate a holiday scene image

    Args:
        interest: A description of the user's interests (e.g., "birds", "music").
    """
    
    #REPLACE_GENERATE_HOLIDAY_SCENE

@mcp.tool
def generate_sweater_pattern(motif: str) -> str:
    """
    Generate a holidays sweater pattern
    
    Args:
        motif: A description of the pattern on the sweater (e.g., "snowflake pattern", "reindeer pattern").
    """
    
    #REPLACE_GENERATE_SWEATER_PATTERN

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
        image_path: Optional absolute path to an uploaded photo of the user. If provided, the avatar will resemble the user.
    """
    
    #REPLACE_GENERATE_WEARING_SWEATER

@mcp.tool
def generate_final_photo() -> str:
    """
    Generate the final photo
    """
    
    #REPLACE_GENERATE_FINAL_PHOTO

if __name__ == "__main__":
    mcp.run()