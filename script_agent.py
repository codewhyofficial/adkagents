import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

# Define Gemini-based LLM agent (system instructions may need to be handled differently)
llm_agent = LlmAgent(
    name="gemini_agent",
    model="gemini-2.0-flash",
    description="""Educational content creator specializing in biology and science topics. Expert in creating engaging video scripts and educational content. Uses built-in knowledge of biology and science topics to create accurate, well-structured content in requested formats.""",
)

# Application/session identifiers
APP_NAME = "demo_app"
USER_ID = "user1"
SESSION_ID = "session1"

async def main():
    # 1️⃣ Create session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    # 2️⃣ Initialize runner
    runner = Runner(
        agent=llm_agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    # 3️⃣ Send detailed prompt with instructions for video script
    prompt = """You are an expert educational content creator with extensive knowledge of biology and science topics. 

Your task: Write a 2 min video script of this topic in an interactive way: "powerhouse of the cell" 

Requirements:
- Use your built-in knowledge about mitochondria and cellular biology
- Return the content in JSON format with strictly these keys: {"scenes": [{"title": "", "content": ["line1", "line2"]}, {"title": "", "content": ["line1", "line2"]},{"title": "", "content": ["line1", "line2"]}]}
- Make it engaging and educational, suitable for a 2-minute video
- Include interactive elements like questions for the audience
- Focus on mitochondria being the powerhouse of the cell
- Each scene should be roughly 30-40 seconds of content

Create an engaging, scientifically accurate video script now."""

    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            print("Agent response:", event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(main())