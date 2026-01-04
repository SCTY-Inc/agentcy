#!/usr/bin/env python3
"""
Agentcy 2.0: Multi-Agent Creative Collaboration Platform
Modernized with AG2, combining research, strategy, content creation, and visual design
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

# Core AG2 imports
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

# Web scraping and processing
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Optional imports with graceful fallbacks
try:
    import html2text
except ImportError:
    html2text = None

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from webdriver_manager.microsoft import EdgeChromiumDriverManager
    selenium_available = True
except ImportError:
    selenium_available = False

try:
    from tqdm import tqdm
except ImportError:
    # Fallback for progress bars
    def tqdm(iterable, *args, **kwargs):
        return iterable

# Image generation
try:
    import replicate
    replicate_available = True
except ImportError:
    replicate_available = False

# Environment and configuration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentcyConfig:
    """Configuration management for Agentcy"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.browserless_api_key = os.getenv("BROWSERLESS_API_KEY")
        self.replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
        
        # AG2 configuration
        try:
            self.config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")
        except:
            self.config_list = [{
                "model": "gpt-4o",
                "api_key": self.openai_api_key
            }]
        
        # Create output directories
        self.output_dir = Path("output")
        self.research_dir = self.output_dir / "research"
        self.content_dir = self.output_dir / "content"
        self.images_dir = self.output_dir / "images"
        
        for dir_path in [self.output_dir, self.research_dir, self.content_dir, self.images_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def validate(self) -> bool:
        """Validate that required API keys are present"""
        required_keys = [self.openai_api_key, self.serper_api_key]
        missing_keys = [key for key in required_keys if not key]
        
        if missing_keys:
            print(f"Missing required API keys. Please set: {', '.join(['OPENAI_API_KEY', 'SERPER_API_KEY'])}")
            return False
        return True

class AdvancedResearchTools:
    """Advanced research capabilities combining web search, scraping, and content processing"""
    
    def __init__(self, config: AgentcyConfig):
        self.config = config
        if html2text:
            self.h2t = html2text.HTML2Text()
            self.h2t.ignore_links = False
            self.h2t.body_width = 0
        else:
            self.h2t = None
    
    def search(self, query: str) -> Dict[str, Any]:
        """Enhanced web search with error handling"""
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': self.config.serper_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": f"Search failed: {str(e)}"}
    
    def scrape_basic(self, url: str) -> str:
        """Basic web scraping using requests"""
        try:
            headers = {
                'Cache-Control': 'no-cache',
                'Content-Type': 'application/json',
            }
            
            if self.config.browserless_api_key:
                # Use Browserless if available
                post_url = f"https://chrome.browserless.io/content?token={self.config.browserless_api_key}"
                response = requests.post(post_url, headers=headers, json={"url": url}, timeout=60)
            else:
                # Fallback to direct requests
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; Agentcy/2.0)'}, timeout=60)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                text = soup.get_text()
                
                if len(text) > 8000:
                    return self.summarize_text(text)
                return text
            else:
                return f"Error: HTTP {response.status_code}"
                
        except Exception as e:
            return f"Scraping failed: {str(e)}"
    
    def summarize_text(self, content: str) -> str:
        """Summarize long text using OpenAI directly instead of LangChain"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.config.openai_api_key)
            
            # Split content into chunks if too long
            max_chunk_size = 15000
            if len(content) > max_chunk_size:
                chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
                summaries = []
                
                for chunk in chunks:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Summarize the following text for research purposes, maintaining key insights and factual information."},
                            {"role": "user", "content": chunk}
                        ],
                        temperature=0.1
                    )
                    summaries.append(response.choices[0].message.content)
                
                # Final summary of summaries
                combined_summary = "\n\n".join(summaries)
                if len(combined_summary) > max_chunk_size:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Create a comprehensive summary from these research summaries."},
                            {"role": "user", "content": combined_summary}
                        ],
                        temperature=0.1
                    )
                    return response.choices[0].message.content
                return combined_summary
            
            # Single summary for shorter content
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Summarize the following text for research purposes, maintaining key insights and factual information."},
                    {"role": "user", "content": content}
                ],
                temperature=0.1
            )
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Summarization failed: {str(e)}. Original content (truncated): {content[:1000]}..."
    
    def advanced_research(self, query: str) -> str:
        """Comprehensive research combining search and scraping"""
        search_results = self.search(query)
        
        if "error" in search_results:
            return f"Research failed: {search_results['error']}"
        
        research_data = []
        research_data.append(f"# Research Report: {query}\n")
        research_data.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Process search results
        if "organic" in search_results:
            research_data.append("## Key Findings\n")
            
            for i, result in enumerate(search_results["organic"][:5]):  # Top 5 results
                title = result.get("title", "No title")
                snippet = result.get("snippet", "No description")
                link = result.get("link", "")
                
                research_data.append(f"### {i+1}. {title}")
                research_data.append(f"**Source:** {link}")
                research_data.append(f"**Summary:** {snippet}\n")
                
                # Try to scrape additional content from promising results
                if any(keyword in title.lower() or keyword in snippet.lower() for keyword in query.lower().split()):
                    scraped_content = self.scrape_basic(link)
                    if scraped_content and not scraped_content.startswith("Error") and not scraped_content.startswith("Scraping failed"):
                        research_data.append(f"**Additional Content:** {scraped_content[:500]}...\n")
        
        # Add related searches if available
        if "relatedSearches" in search_results:
            research_data.append("## Related Research Areas\n")
            for related in search_results["relatedSearches"]:
                research_data.append(f"- {related.get('query', '')}")
        
        research_content = "\n".join(research_data)
        
        # Save research report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.research_dir / f"research_{timestamp}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(research_content)
        
        return research_content

class VisualContentTools:
    """Image generation and critique capabilities"""
    
    def __init__(self, config: AgentcyConfig):
        self.config = config
        if config.replicate_api_token and replicate_available:
            os.environ["REPLICATE_API_TOKEN"] = config.replicate_api_token
    
    def generate_image(self, prompt: str) -> str:
        """Generate image using Stability AI via Replicate"""
        try:
            if not replicate_available:
                return "Image generation unavailable: replicate package not installed. Install with: pip install replicate"
            
            if not self.config.replicate_api_token:
                return "Image generation unavailable: REPLICATE_API_TOKEN not set"
            
            output = replicate.run(
                "stability-ai/sdxl:c221b2b8ef527988fb59bf24a8b97c4561f1c671f73bd389f866bfb27c061316",
                input={"prompt": prompt}
            )
            
            if output and len(output) > 0:
                image_url = output[0]
                
                # Download and save image
                current_time = datetime.now().strftime("%Y%m%d%H%M%S")
                safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                filename = self.config.images_dir / f"{safe_prompt}_{current_time}.png"
                
                response = requests.get(image_url, timeout=60)
                if response.status_code == 200:
                    with open(filename, "wb") as file:
                        file.write(response.content)
                    return f"Image generated and saved: {filename}"
                else:
                    return f"Image generated but download failed: {image_url}"
            else:
                return "Image generation failed"
                
        except Exception as e:
            return f"Image generation error: {str(e)}"
    
    def critique_image(self, image_path: str, original_prompt: str) -> str:
        """Critique generated image using LLaVA"""
        try:
            if not replicate_available:
                return "Image critique unavailable: replicate package not installed. Install with: pip install replicate"
            
            if not self.config.replicate_api_token:
                return "Image critique unavailable: REPLICATE_API_TOKEN not set"
            
            if not os.path.exists(image_path):
                return f"Image file not found: {image_path}"
            
            output = replicate.run(
                "yorickvp/llava-13b:2facb4a474a0462c15041b78b1ad70952ea46b5ec6ad29583c0b29dbd4249591",
                input={
                    "image": open(image_path, "rb"),
                    "prompt": f"Analyze this image and rate how well it matches this prompt: '{original_prompt}'. Rate from 1-10 and explain how to improve it."
                }
            )
            
            result = ""
            for item in output:
                result += item
            
            return result
            
        except Exception as e:
            return f"Image critique error: {str(e)}"

class MarketingFrameworks:
    """Professional marketing and copywriting frameworks"""
    
    COPYWRITING_PRINCIPLES = [
        "Reciprocity", "Scarcity", "Authority", "Commitment", 
        "Consistency", "Consensus/Social Proof", "Liking"
    ]
    
    MARKETING_FRAMEWORKS = {
        "4Ps": "Product, Price, Place, Promotion",
        "STP": "Segmentation, Targeting, Positioning", 
        "AIDA": "Attention, Interest, Desire, Action",
        "Customer Journey": "Awareness, Consideration, Purchase, Retention, Advocacy",
        "Marketing Funnel": "Awareness, Interest, Consideration, Intent, Evaluation, Purchase"
    }
    
    MEDIA_FRAMEWORKS = {
        "RACE": "Reach, Act, Convert, Engage",
        "STDC": "See, Think, Do, Care (Google Framework)",
        "POEM": "Paid, Owned, Earned Media",
        "OST": "Objectives, Strategy, Tactics"
    }
    
    @classmethod
    def get_copywriting_guidance(cls) -> str:
        """Get copywriting principles guidance"""
        return f"Apply these persuasive principles: {', '.join(cls.COPYWRITING_PRINCIPLES)}"
    
    @classmethod
    def get_marketing_guidance(cls) -> str:
        """Get marketing framework guidance"""
        frameworks = [f"{k}: {v}" for k, v in cls.MARKETING_FRAMEWORKS.items()]
        return f"Use appropriate marketing frameworks: {'; '.join(frameworks)}"
    
    @classmethod
    def get_media_guidance(cls) -> str:
        """Get media planning framework guidance"""
        frameworks = [f"{k}: {v}" for k, v in cls.MEDIA_FRAMEWORKS.items()]
        return f"Apply media planning frameworks: {'; '.join(frameworks)}"

class AgentcyCore:
    """Core Agentcy system with all integrated capabilities"""
    
    def __init__(self):
        self.config = AgentcyConfig()
        if not self.config.validate():
            raise ValueError("Configuration validation failed")
        
        self.research_tools = AdvancedResearchTools(self.config)
        self.visual_tools = VisualContentTools(self.config)
        self.frameworks = MarketingFrameworks()
        
        # Set up AG2 configuration
        self.llm_config = {"config_list": self.config.config_list, "timeout": 120}
        self.llm_config_with_functions = {
            "config_list": self.config.config_list,
            "timeout": 120,
            "functions": self._get_function_definitions()
        }
        
        self.setup_agents()
    
    def _get_function_definitions(self) -> List[Dict]:
        """Define all available functions for agents"""
        return [
            {
                "name": "research",
                "description": "Conduct comprehensive research on a topic using web search and scraping",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research query or topic"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "generate_image",
                "description": "Generate visual content using AI image generation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "Detailed description for image generation"
                        }
                    },
                    "required": ["prompt"]
                }
            },
            {
                "name": "critique_image",
                "description": "Analyze and critique generated images",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "Path to the image file"
                        },
                        "original_prompt": {
                            "type": "string",
                            "description": "Original prompt used to generate the image"
                        }
                    },
                    "required": ["image_path", "original_prompt"]
                }
            }
        ]
    
    def setup_agents(self):
        """Initialize all agency agents with enhanced capabilities"""
        
        # Agency Manager - Project coordination
        self.agency_manager = AssistantAgent(
            name="Agency_Manager",
            description="Coordinates all agency activities and ensures project alignment",
            llm_config=self.llm_config,
            system_message="""
            You are the Agency Manager coordinating a creative project. Your responsibilities:
            
            1. Create and communicate a clear project plan based on the brand and objectives
            2. Coordinate between all team members ensuring smooth workflow
            3. Monitor progress and provide regular updates
            4. Ensure all deliverables meet quality standards
            5. Manage timelines and resource allocation
            
            Always maintain a professional tone and focus on actionable outcomes.
            Conclude with "TERMINATE" when all objectives are completed.
            """
        )
        
        # Research Specialist - Enhanced research capabilities
        self.agency_researcher = AssistantAgent(
            name="Agency_Researcher", 
            description="Conducts comprehensive market research and competitive analysis",
            llm_config=self.llm_config_with_functions,
            system_message="""
            You are the Lead Researcher responsible for gathering comprehensive insights.
            
            Use the research function to investigate:
            - Market trends and opportunities
            - Competitive landscape analysis  
            - Target audience insights
            - Industry best practices
            - Cultural and social context
            
            Provide detailed, data-driven reports with actionable insights.
            Always cite sources and include relevant statistics when available.
            """
        )
        
        # Strategic Planner - Framework-driven strategy
        self.agency_strategist = AssistantAgent(
            name="Agency_Strategist",
            description="Develops strategic frameworks and positioning strategies", 
            llm_config=self.llm_config_with_functions,
            system_message=f"""
            You are the Lead Strategist creating comprehensive strategic briefs.
            
            {self.frameworks.get_marketing_guidance()}
            
            Develop strategies covering:
            - Brand positioning and differentiation
            - Target audience segmentation and personas
            - Value proposition development
            - Competitive positioning
            - Strategic messaging framework
            - Key performance indicators
            
            Use research insights to ground your strategy in market reality.
            Provide clear, actionable strategic direction.
            """
        )
        
        # Creative Copywriter - Persuasion-focused content
        self.agency_copywriter = AssistantAgent(
            name="Agency_Copywriter",
            description="Creates compelling copy using proven persuasion principles",
            llm_config=self.llm_config_with_functions,
            system_message=f"""
            You are the Lead Copywriter crafting persuasive content.
            
            {self.frameworks.get_copywriting_guidance()}
            
            Create content that:
            - Captures attention and builds interest
            - Addresses audience pain points and desires
            - Uses storytelling and emotional connections
            - Includes clear calls-to-action
            - Maintains consistent brand voice
            - Applies psychological triggers appropriately
            
            Focus on conversion-oriented copy that drives action.
            """
        )
        
        # Visual Creative Director - Image and visual strategy
        self.agency_visual_director = AssistantAgent(
            name="Agency_Visual_Director",
            description="Develops visual concepts and creates image content",
            llm_config=self.llm_config_with_functions,
            system_message="""
            You are the Visual Creative Director responsible for all visual content.
            
            Use generate_image and critique_image functions to:
            - Create compelling visual concepts that support the strategy
            - Generate images that align with brand identity
            - Ensure visual consistency across all materials
            - Critique and refine visual content for maximum impact
            
            Consider:
            - Visual hierarchy and composition
            - Color psychology and brand colors
            - Typography and readability
            - Cultural and contextual appropriateness
            - Platform-specific requirements
            
            Provide detailed creative direction and rationale for visual choices.
            """
        )
        
        # Marketing Strategist - Campaign and channel strategy
        self.agency_marketer = AssistantAgent(
            name="Agency_Marketer",
            description="Develops marketing campaigns and customer journey strategies",
            llm_config=self.llm_config,
            system_message=f"""
            You are the Lead Marketer creating comprehensive marketing strategies.
            
            {self.frameworks.get_marketing_guidance()}
            
            Develop marketing initiatives including:
            - Customer journey mapping
            - Campaign concepts and themes
            - Channel strategy and mix
            - Conversion optimization tactics
            - Performance measurement framework
            - Budget allocation recommendations
            
            Ensure marketing aligns with strategic objectives and brand positioning.
            Focus on measurable, results-driven marketing approaches.
            """
        )
        
        # Media Planning Specialist - Channel optimization
        self.agency_media_planner = AssistantAgent(
            name="Agency_Media_Planner",
            description="Optimizes media mix and channel strategies",
            llm_config=self.llm_config,
            system_message=f"""
            You are the Lead Media Planner optimizing channel strategy.
            
            {self.frameworks.get_media_guidance()}
            
            Create media strategies covering:
            - Channel selection and prioritization
            - Audience targeting and segmentation
            - Budget allocation across channels
            - Content format optimization
            - Performance measurement and KPIs
            - Testing and optimization strategies
            
            Consider both traditional and digital channels.
            Provide data-driven recommendations with clear rationale.
            """
        )
        
        # Creative Director - Overall creative vision
        self.agency_director = AssistantAgent(
            name="Agency_Director", 
            description="Provides creative leadership and ensures excellence",
            llm_config=self.llm_config,
            system_message="""
            You are the Creative Director setting the overall creative vision.
            
            Your responsibilities:
            - Ensure creative excellence across all outputs
            - Maintain brand consistency and integrity  
            - Challenge the team to push creative boundaries
            - Provide constructive feedback and direction
            - Ensure cultural relevance and appropriateness
            - Balance creativity with strategic objectives
            
            Review all creative work and provide expert guidance.
            Push for innovative, breakthrough creative solutions.
            """
        )
        
        # User Proxy - Human interface
        self.user_proxy = UserProxyAgent(
            name="User_Proxy",
            description="Represents the client and manages human interaction",
            is_termination_msg=lambda msg: "TERMINATE" in msg.get("content", ""),
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=1,
            code_execution_config={"work_dir": str(self.config.output_dir)},
            function_map={
                "research": self.research_tools.advanced_research,
                "generate_image": self.visual_tools.generate_image,
                "critique_image": self.visual_tools.critique_image
            }
        )
        
        # Setup group chat
        self.agents = [
            self.user_proxy,
            self.agency_manager, 
            self.agency_researcher,
            self.agency_strategist,
            self.agency_copywriter,
            self.agency_visual_director,
            self.agency_marketer,
            self.agency_media_planner,
            self.agency_director
        ]
        
        self.group_chat = GroupChat(
            agents=self.agents,
            messages=[],
            max_round=25
        )
        
        self.manager = GroupChatManager(
            groupchat=self.group_chat,
            llm_config=self.llm_config
        )
    
    def run_creative_session(self, brand_name: str, project_objective: str):
        """Execute a complete creative agency session"""
        
        print(f"\n🎨 Starting Agentcy 2.0 Creative Session")
        print(f"📍 Brand: {brand_name}")
        print(f"🎯 Objective: {project_objective}")
        print(f"📁 Output Directory: {self.config.output_dir}")
        print("=" * 60)
        
        # Craft comprehensive project brief
        project_brief = f"""
        CREATIVE PROJECT BRIEF
        
        Brand: {brand_name}
        Objective: {project_objective}
        
        Project Requirements:
        1. Conduct comprehensive research on the market, competitors, and target audience
        2. Develop strategic positioning and messaging framework
        3. Create compelling copy and content
        4. Generate supporting visual concepts and imagery
        5. Design comprehensive marketing and media strategy
        6. Ensure all deliverables align with creative excellence standards
        
        Expected Deliverables:
        - Research report with market insights
        - Strategic brief with positioning and messaging
        - Creative copy and content recommendations  
        - Visual concepts and generated imagery
        - Marketing campaign strategy
        - Media planning and channel recommendations
        - Final creative direction and implementation guide
        
        Please coordinate as a team to deliver a comprehensive creative solution.
        """
        
        # Start the collaborative session
        self.user_proxy.initiate_chat(
            self.manager,
            message=project_brief
        )
        
        print(f"\n✅ Creative session completed!")
        print(f"📁 All outputs saved to: {self.config.output_dir}")
        
        return True

def main():
    """Main application entry point"""
    print("🎨 Welcome to Agentcy 2.0 - Multi-Agent Creative Collaboration Platform")
    print("Powered by AG2 with advanced research, strategy, and visual capabilities")
    print("-" * 70)
    
    try:
        # Initialize the system
        agentcy = AgentcyCore()
        
        # Get user input
        brand_name = input("\n📍 Enter the brand or company name: ").strip()
        if not brand_name:
            brand_name = "YourBrand"
        
        project_objective = input("🎯 Enter your goal, brief, or problem statement: ").strip()
        if not project_objective:
            print("❌ Project objective is required!")
            return
        
        # Run the creative session
        agentcy.run_creative_session(brand_name, project_objective)
        
    except KeyboardInterrupt:
        print("\n👋 Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()