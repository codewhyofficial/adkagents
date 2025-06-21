import os
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
import google.generativeai as genai

load_dotenv()
assert os.getenv("GOOGLE_API_KEY"), "Set GOOGLE_API_KEY in .env"

# Configure the API key for image generation
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Script Generator Agent
script_agent = LlmAgent(
    name="script_agent",
    model="gemini-2.0-flash",
    description="""Educational content creator specializing in biology and science topics. Expert in creating engaging video scripts and educational content. Uses built-in knowledge of biology and science topics to create accurate, well-structured content in requested formats.""",
)

# Keyword Extractor Agent
keyword_agent = LlmAgent(
    name="keyword_agent",
    model="gemini-2.0-flash",
    description="""Expert at analyzing video script content and extracting relevant search keywords for vector illustrations. Specializes in identifying visual elements that would enhance educational content.""",
)

# Application/session identifiers
APP_NAME = "demo_app"
USER_ID = "user1"

class VideoContentPipeline:
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.script_session_id = "script_session"
        self.keyword_session_id = "keyword_session"
        
    async def initialize_sessions(self):
        """Initialize sessions for both agents"""
        await self.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=self.script_session_id
        )
        await self.session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=self.keyword_session_id
        )

    async def generate_script(self, topic: str) -> str:
        """Generate video script for the given topic"""
        runner = Runner(
            agent=script_agent,
            app_name=APP_NAME,
            session_service=self.session_service
        )

        prompt = f"""You are an expert educational content creator with extensive knowledge of biology and science topics. 

Your task: Write a 2 min video script of this topic in an interactive way: "{topic}" 

Requirements:
- Use your built-in knowledge about mitochondria and cellular biology
- Return the content in JSON format with strictly these keys: {{"scenes": [{{"title": "", "content": ["line1", "line2"]}}, {{"title": "", "content": ["line1", "line2"]}},{{"title": "", "content": ["line1", "line2"]}}]}}
- Make it engaging and educational, suitable for a 2-minute video
- Include interactive elements like questions for the audience
- Focus on mitochondria being the powerhouse of the cell
- Each scene should be roughly 30-40 seconds of content

Create an engaging, scientifically accurate video script now."""

        content = types.Content(role="user", parts=[types.Part(text=prompt)])
        
        script_response = ""
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=self.script_session_id,
            new_message=content
        ):
            if event.is_final_response():
                script_response = event.content.parts[0].text
                break
                
        return script_response

    async def extract_keywords(self, script_content: str) -> str:
        """Extract keywords for vector illustrations from script content"""
        runner = Runner(
            agent=keyword_agent,
            app_name=APP_NAME,
            session_service=self.session_service
        )

        prompt = f"""You are an expert at analyzing video script content and identifying visual elements for illustrations.

Analyze this video script content and give me the search keywords for finding vector illustrations for this content.

Script content:
{script_content}

Requirements:
- Extract 5-8 relevant keywords that would be good for finding vector illustrations
- Focus on visual elements, concepts, and objects mentioned in the script
- Keywords should be suitable for educational vector illustrations
- Return the output in JSON format, strictly like this: {{"keywords": ["keyword1", "keyword2", "keyword3"]}}

Provide the keywords now:"""

        content = types.Content(role="user", parts=[types.Part(text=prompt)])
        
        keywords_response = ""
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=self.keyword_session_id,
            new_message=content
        ):
            if event.is_final_response():
                keywords_response = event.content.parts[0].text
                break
                
        return keywords_response

    def create_images_folder(self) -> Path:
        """Create a folder for storing generated images"""
        images_folder = Path("generated_images")
        images_folder.mkdir(exist_ok=True)
        return images_folder

    async def generate_images(self, keywords_json: str, output_folder: Path):
        """Generate images using Google's image generation model"""
        try:
            # Parse keywords from JSON
            keywords_data = json.loads(keywords_json)
            keywords = keywords_data.get("keywords", [])
            
            print(f"Generating images for {len(keywords)} keywords...")
            
            # Initialize the image generation model
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            generated_files = []
            
            for i, keyword in enumerate(keywords):
                try:
                    # Create a detailed prompt for educational vector-style illustration
                    image_prompt = f"Create a clean, educational vector-style illustration of {keyword}. Make it suitable for a biology educational video about cells and mitochondria. Use bright, engaging colors with a modern flat design style. The illustration should be clear and simple enough for educational purposes."
                    
                    print(f"Generating image {i+1}/{len(keywords)}: {keyword}")
                    
                    # Note: This is a placeholder for image generation
                    # The actual Google ADK image generation API might be different
                    # You may need to use a different approach like:
                    # 1. Google's Imagen API
                    # 2. Integration with other image generation services
                    # 3. Or a different Google AI image generation endpoint
                    
                    # For now, creating a placeholder file
                    filename = f"{keyword.replace(' ', '_').lower()}_{i+1}.txt"
                    filepath = output_folder / filename
                    
                    with open(filepath, 'w') as f:
                        f.write(f"Image prompt: {image_prompt}\n")
                        f.write(f"Keyword: {keyword}\n")
                        f.write("Note: This is a placeholder. Actual image generation requires proper Google Imagen API integration.")
                    
                    generated_files.append(str(filepath))
                    print(f"Created placeholder for: {keyword}")
                    
                except Exception as e:
                    print(f"Error generating image for '{keyword}': {str(e)}")
            
            return generated_files
            
        except json.JSONDecodeError as e:
            print(f"Error parsing keywords JSON: {e}")
            return []
        except Exception as e:
            print(f"Error in image generation: {e}")
            return []

    async def run_complete_pipeline(self, topic: str):
        """Run the complete pipeline: script -> keywords -> images"""
        print("🚀 Starting Video Content Pipeline...")
        
        # Initialize sessions
        await self.initialize_sessions()
        
        # Step 1: Generate script
        print("📝 Generating video script...")
        script = await self.generate_script(topic)
        print("✅ Script generated!")
        print("Script:")
        print(script)
        print("\n" + "="*50 + "\n")
        
        # Step 2: Extract keywords
        print("🔍 Extracting keywords...")
        keywords = await self.extract_keywords(script)
        print("✅ Keywords extracted!")
        print("Keywords:")
        print(keywords)
        print("\n" + "="*50 + "\n")
        
        # Step 3: Create images folder
        images_folder = self.create_images_folder()
        print(f"📁 Created images folder: {images_folder}")
        
        # Step 4: Generate images
        print("🎨 Generating images...")
        generated_files = await self.generate_images(keywords, images_folder)
        print(f"✅ Generated {len(generated_files)} image files!")
        
        for file in generated_files:
            print(f"   - {file}")
        
        print("\n🎉 Pipeline completed successfully!")
        
        return {
            "script": script,
            "keywords": keywords,
            "generated_files": generated_files,
            "images_folder": str(images_folder)
        }

async def main():
    pipeline = VideoContentPipeline()
    result = await pipeline.run_complete_pipeline("powerhouse of the cell")
    
    # Save results to a summary file
    summary_file = Path("pipeline_results.json")
    with open(summary_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n📄 Results saved to: {summary_file}")

if __name__ == "__main__":
    asyncio.run(main())