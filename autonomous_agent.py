import os
import json
import asyncio
import random
import string
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import time

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

# Video Generation Tools
def generate_video_content(topic: str, scene_count: int = 7) -> str:
    """Generate educational content points for video creation"""
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"Write {scene_count} concise educational points about '{topic}'. Each point should be 1-2 sentences suitable for a video script."
        
        response = model.generate_content(prompt)
        content_lines = response.text.split('\n')
        
        # Clean and format content
        content_list = []
        for line in content_lines:
            line = line.strip()
            if line and not any(phrase in line.lower() for phrase in ["any more", "certainly", "here are"]):
                if '. ' in line[:5]:  # Remove numbering
                    line = line.split('.', 1)[-1].strip()
                if line:
                    content_list.append(line)
        
        return json.dumps({"content_points": content_list[:scene_count]})
    except Exception as e:
        return json.dumps({"error": str(e)})

def search_stock_video(query: str) -> str:
    """Mock stock video search - replace with real API"""
    try:
        clean_query = query.lower().replace(" ", "-").replace(".", "")
        video_id = abs(hash(query)) % 10000000
        
        return json.dumps({
            "video": f"https://media.gettyimages.com/id/{video_id}/video/{clean_query}.mp4",
            "poster": f"https://media.gettyimages.com/id/{video_id}/video/{clean_query}.jpg"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def generate_audio_file(text: str, index: int) -> str:
    """Generate audio file placeholder"""
    try:
        # Create audio directory
        audio_dir = Path("static/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate random filename
        random_chars = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(4))
        filename = f"static/audio/{index}_{random_chars}.mp3"
        
        # Create placeholder file
        with open(filename.replace('.mp3', '.txt'), 'w') as f:
            f.write(f"Audio placeholder for: {text}\n")
            f.write(f"Use Google Text-to-Speech or ElevenLabs API to generate actual audio\n")
        
        return json.dumps({"audio_file": filename, "text": text})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Create the autonomous agent
autonomous_agent = LlmAgent(
    name="video_creator_agent",
    model="gemini-2.0-flash",
    description="""Autonomous video content creator. Can generate educational video content, search for stock videos, and create audio files. Specializes in creating complete video data structures with text, video, and audio components.""",
    tools=[generate_video_content, search_stock_video, generate_audio_file]
)

# Application identifiers
APP_NAME = "autonomous_video_app"
USER_ID = "user1"
SESSION_ID = "session1"

async def create_video_content(topic: str, language: str = "en", scene_count: int = 7):
    """
    Single function to generate complete video content
    Just like your GenerateVideo class but using Google ADK
    """
    
    # Initialize session
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    
    # Initialize runner
    runner = Runner(
        agent=autonomous_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    
    # Single comprehensive prompt - agent decides which tools to use
    prompt = f"""Create a complete video content package for the topic: "{topic}"

Your task is to generate a video data structure exactly like this format:
{{
    0: {{
        "text": "educational content about the topic",
        "video": "stock_video_url",
        "poster": "poster_image_url", 
        "audio": "audio_file_path"
    }},
    1: {{
        "text": "second educational point",
        "video": "stock_video_url",
        "poster": "poster_image_url",
        "audio": "audio_file_path"
    }},
    ... and so on for {scene_count} scenes
}}

REQUIREMENTS:
1. Generate {scene_count} educational content points about "{topic}"
2. For each content point, search for appropriate stock video
3. Generate audio files for each text segment
4. Create the final JSON data structure with numbered keys (0, 1, 2, etc.)
5. Language: {language}

Use your available tools to:
- Generate educational content points
- Search for stock videos for each point
- Create audio files for narration
- Compile everything into the final data structure

Please complete this task autonomously and provide the final JSON result."""

    content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    # Get response from agent
    final_response = ""
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    ):
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("🤖 Agent Response:")
            print(final_response)
            break
    
    return final_response

# Simple usage function that matches your original GenerateVideo class
class GenerateVideoADK:
    """
    Google ADK version of your GenerateVideo class
    Single prompt -> Complete video content
    """
    
    def __init__(self, topic: str, language: str = "en"):
        self.topic = topic
        self.language = language
        self.scene_count = 7
    
    async def start(self):
        """
        Main method - equivalent to your start() method
        Returns the same data structure as your original code
        """
        print(f"🚀 Starting autonomous video generation for: {self.topic}")
        
        # Single call to generate everything
        result = await create_video_content(
            topic=self.topic,
            language=self.language,
            scene_count=self.scene_count
        )
        
        # Save result to file
        output_file = f"video_content_{self.topic.replace(' ', '_')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"💾 Content saved to: {output_file}")
        
        return result

# Main execution
async def main():
    """
    Main function - demonstrates single prompt video generation
    """
    
    # Example 1: Your original topic
    print("="*60)
    print("🎬 AUTONOMOUS VIDEO GENERATION DEMO")
    print("="*60)
    
    # Single prompt approach
    topic = "powerhouse of the cell"
    video_generator = GenerateVideoADK(topic, "en")
    result = await video_generator.start()
    
    print("\n" + "="*60)
    print("✅ VIDEO GENERATION COMPLETE!")
    print("="*60)
    
    return result

if __name__ == "__main__":
    # Single command execution
    asyncio.run(main())