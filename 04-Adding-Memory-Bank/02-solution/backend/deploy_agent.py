import os
import logging
from dotenv import load_dotenv
import vertexai
from vertexai.preview import reasoning_engines

# Import class-based types for Memory Bank
from vertexai import types
from google.genai import types as genai_types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION", "us-central1")
AGENT_DISPLAY_NAME = "christmas_tree_agent_engine_custom"

if not PROJECT_ID:
    raise ValueError("PROJECT_ID not found in environment variables.")

# Basic configuration types
MemoryBankConfig = types.ReasoningEngineContextSpecMemoryBankConfig
SimilaritySearchConfig = (
    types.ReasoningEngineContextSpecMemoryBankConfigSimilaritySearchConfig
)
GenerationConfig = types.ReasoningEngineContextSpecMemoryBankConfigGenerationConfig

# Advanced configuration types
CustomizationConfig = types.MemoryBankCustomizationConfig
MemoryTopic = types.MemoryBankCustomizationConfigMemoryTopic
CustomMemoryTopic = types.MemoryBankCustomizationConfigMemoryTopicCustomMemoryTopic
GenerateMemoriesExample = types.MemoryBankCustomizationConfigGenerateMemoriesExample
ConversationSource = (
    types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSource
)
ConversationSourceEvent = (
    types.MemoryBankCustomizationConfigGenerateMemoriesExampleConversationSourceEvent
)
ExampleGeneratedMemory = (
    types.MemoryBankCustomizationConfigGenerateMemoriesExampleGeneratedMemory
)
Content = genai_types.Content
Part = genai_types.Part

def register_agent_engine():
    """
    Registers an Agent Engine resource in Vertex AI to enable Sessions and Memory Bank.
    This does NOT deploy the agent code to the cloud.
    """
    logger.info(f"Initializing Vertex AI for project: {PROJECT_ID}, location: {LOCATION}")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    # --- Define Custom Topics ---
    logger.info("Defining custom topics...")
    
    custom_topics = [
        # Topic 1: Sweater Preference
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="sweater_preference",
                description="""Extract the user's preferences for sweater styles, patterns, and designs. Include:
                - Specific patterns (snowflake, reindeer, geometric, fair isle, solid, etc.)
                - Style preferences (chunky knit, cardigan, pullover, turtleneck, oversized, fitted)
                - Color preferences (red, green, navy, pastel, etc.)
                - Material preferences if mentioned (wool, cotton, cashmere, itchy/soft)
                - Themes (retro, modern, ugly christmas sweater, elegant)
                
                Example: "User wants a retro style sweater with a pixelated reindeer pattern."
                Example: "User prefers dark blue colors and hates itchy wool."
                """,
            )
        ),
        # Topic 2: Personal Context
        MemoryTopic(
            custom_memory_topic=CustomMemoryTopic(
                label="personal_context",
                description="""Extract the user's personal context including hobbies, pets, interests, job, and preferred scenes. Include:
                - Hobbies and activities (skiing, reading, gaming, cooking, etc.)
                - Pets (type, breed, name, color)
                - Job or profession if relevant to their style
                - General interests (sci-fi, nature, vintage, tech)
                - Preferred scenes or vibes (cozy fireplace, snowy mountain, cyberpunk city, beach)
                
                Example: "User has a golden retriever named Max."
                Example: "User loves skiing and wants a snowy mountain background."
                Example: "User is a software engineer who likes cyberpunk aesthetics."
                """,
            )
        )
    ]

    # --- Define Few-Shot Examples ---
    logger.info("Defining few-shot examples...")
    
    few_shot_examples = [
        GenerateMemoriesExample(
            conversation_source=ConversationSource(
                events=[
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="I want a sweater that matches my dog. He's a golden retriever.")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="model",
                            parts=[Part(text="That sounds adorable! A golden retriever themed sweater would be great. Do you want a picture of him on it or just matching colors?")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="Maybe just the color, like a golden yellow. And I like skiing, so maybe add some snowflakes.")]
                        )
                    )
                ]
            ),
            generated_memories=[
                ExampleGeneratedMemory(fact="User has a golden retriever dog"),
                ExampleGeneratedMemory(fact="User prefers a golden yellow color for their sweater"),
                ExampleGeneratedMemory(fact="User likes skiing"),
                ExampleGeneratedMemory(fact="User wants snowflake patterns on their sweater")
            ]
        ),
        GenerateMemoriesExample(
            conversation_source=ConversationSource(
                events=[
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="I'm a programmer, so I want something geeky. Maybe a matrix style?")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="model",
                            parts=[Part(text="A Matrix style sweater sounds cool! We could do falling code rain patterns.")]
                        )
                    ),
                    ConversationSourceEvent(
                        content=Content(
                            role="user",
                            parts=[Part(text="Yes! Green code on black. And make it a hoodie style if possible.")]
                        )
                    )
                ]
            ),
            generated_memories=[
                ExampleGeneratedMemory(fact="User is a programmer"),
                ExampleGeneratedMemory(fact="User wants a 'Matrix' style sweater with falling code rain pattern"),
                ExampleGeneratedMemory(fact="User prefers green code on black background"),
                ExampleGeneratedMemory(fact="User prefers hoodie style sweaters")
            ]
        )
    ]

    # --- Create Customization Config ---
    customization_config = CustomizationConfig(
        memory_topics=custom_topics,
        generate_memories_examples=few_shot_examples
    )

    logger.info(f"Creating/Registering Agent Engine: {AGENT_DISPLAY_NAME}")
    
    # Create Agent Engine with Memory Bank configuration
    agent_engine = client.agent_engines.create(
        config={
            "display_name": AGENT_DISPLAY_NAME,
            "context_spec": {
                "memory_bank_config": {
                    "generation_config": {
                        "model": f"projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/gemini-2.5-flash"
                    },
                    "customization_configs": [customization_config]
                }
            },
        }
    )

    agent_engine_id = agent_engine.api_resource.name.split("/")[-1]
    logger.info("✅ Agent Engine Registered Successfully!")
    logger.info(f"Agent Engine ID: {agent_engine_id}")
    logger.info("\nIMPORTANT: Add the following line to your backend/.env file:")
    logger.info(f"AGENT_ENGINE_ID={agent_engine_id}")

if __name__ == "__main__":
    try:
        register_agent_engine()
    except Exception as e:
        logger.error(f"Failed to register Agent Engine: {e}")
