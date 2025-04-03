import asyncio
import os

import dotenv
from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console

from tools import research, write_content


from autogen_ext.models.openai import OpenAIChatCompletionClient


dotenv.load_dotenv()
#openai.api_key = os.getenv("OPENAI_API_KEY")
BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

brand_task = "Satalia "#input("Please enter the brand or company name: ")
user_task = "Developing an Advertising Campaign for a New Mobile App" # input("Please enter the your goal, brief, or problem statement: ")


async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
    # Initialize the agents
    agency_manager = AssistantAgent(
        name="Agency_Manager",
        description="Outlines plan for agents.",
        model_client=model_client,
        system_message=f'''
        Outline step-by-step tasks for {brand_task} and {user_task} with the team. 
        Act as a communication hub, maintain high-quality deliverables, and regularly update all stakeholders on progress. 
        Terminate the conversation with "TERMINATE" when all tasks are completed and no further actions are needed.
        '''
    )

    agency_researcher = AssistantAgent(
        name="Agency_Researcher",
        description="Conducts detailed research to provide insights for executing user-focused tasks.",
        model_client=model_client,
        system_message=f'''
        Utilize the research function to gather insights about {user_task}, market trends, user pain points, and cultural dynamics relevant to our project. 
        Focus on delivering clear, actionable information. 
         and generate detailed research results with loads of technique details with all reference links attached;
        Conclude your participation with "TERMINATE" once all relevant research has been provided and no further analysis is required.
        ''',
       tools=[research],reflect_on_tool_use=True,
    )



    agency_strategist = AssistantAgent(
        name="Agency_Strategist",
        description="Develops strategic briefs based on market analysis and research findings, focusing on brand positioning and audience insights.",
        model_client=model_client,
        system_message=f'''
        As the Lead Strategist, your key task is to develop strategic briefs for {brand_task}, guided by {user_task} objectives. 
        Utilize the insights from Agency_Researcher to inform your strategies, focusing on brand positioning, key messaging, and audience targeting. 
        Ensure your briefs offer unique perspectives and clear direction. 
        Coordinate closely with the Agency_Manager for alignment with project goals. 
        Conclude with "TERMINATE" once the strategic direction is established and communicated.
        '''
    )

    agency_writer = AssistantAgent(
        name="Agency_Copywriter",
        description="Creates engaging content and narratives aligned with project goals, using insights from research and strategy.",
        model_client=model_client,
        system_message="""
        As the Lead Copywriter, your role is to craft compelling narratives and content.
        Focus on delivering clear, engaging, and relevant messages that resonate with our target audience.
        Use your creativity to transform strategic insights and research findings into impactful content.
        Ensure your writing maintains the brand's voice and aligns with the overall project strategy.
        Your goal is to create content that effectively communicates our message and engages the audience.
        """,
        tools=[write_content],reflect_on_tool_use=True,
    )

    writing_assistant = AssistantAgent(
        name="writing_assistant",
        description="Versatile assistant skilled in researching various topics and crafting well-written content.",
        model_client=model_client,
        system_message="""
        As a writing assistant, your role involves using the research function to stay updated on diverse topics and employing the write_content function to produce polished prose.  
        Ensure your written material is informative and well-structured, catering to the specific needs of the topic.  
        Conclude your contributions with "TERMINATE" after completing the writing tasks as required.
        """,
        tools= [research,write_content],reflect_on_tool_use=True,

    )

    agency_marketer = AssistantAgent(
        name="Agency_Marketer",
        description="Crafts marketing strategies and campaigns attuned to audience needs, utilizing insights from project research and strategy.",
        model_client=model_client,
        system_message=f'''
        As the Lead Marketer, utilize insights and strategies to develop marketing ideas that engage our target audience. 
        For {user_task}, create campaigns and initiatives that clearly convey our brand's value. 
        Bridge strategy and execution, ensuring our message is impactful and aligned with our vision. 
        Collaborate with teams for a unified approach, and coordinate with the Agency Manager for project alignment. 
        Conclude with "TERMINATE" when your marketing contributions are complete.
        '''
    )

    agency_mediaplanner = AssistantAgent(
        name="Agency_Media_Planner",
        description="Identifies optimal media channels and strategies for ad delivery, aligned with project goals.",
        model_client=model_client,
        system_message=f'''
        As the Lead Media Planner, your task is to identify the ideal media mix for delivering our advertising messages, targeting the client's audience. 
        Utilize the research function to stay updated on current and effective media channels and tactics. 
        Apply insights from {user_task} to formulate strategies that effectively reach the audience through various media, both traditional and digital. 
        Collaborate closely with the Agency Manager to ensure your plans are in sync with the broader user strategy. 
        Conclude your role with "TERMINATE" once the media planning is complete and aligned.
        '''
    )

    agency_director = AssistantAgent(
        name="Agency_Director",
        description="Guides the project's creative vision, ensuring uniqueness, excellence, and relevance in all ideas and executions.",
        model_client=model_client,
        system_message="""
        As the Creative Director, your role is to oversee the project's creative aspects. 
        Critically evaluate all work, ensuring each idea is not just unique but also aligns with our standards of excellence. 
        Encourage the team to innovate and explore new creative avenues. 
        Collaborate closely with the Agency_Manager for consistent alignment with the user_proxy. 
        When all agents with "TERMINATE" once you've ensured the project's creative integrity and alignment.
        """,
    )

    user_proxy = UserProxyAgent(
       name="user_proxy",
       description="Acts as a proxy for the user, capable of executing code and handling user interactions within predefined guidelines.",
    )
    termination = MaxMessageTermination(
        max_messages=15) & TextMentionTermination("TERMINATE") #| TextMentionTermination("termina | TextMentionTermination("terminated") | TextMentionTermination("TERMINATED")

    groupchat = SelectorGroupChat([user_proxy,
         agency_manager, agency_researcher, agency_strategist, agency_writer, writing_assistant, agency_marketer, agency_mediaplanner, agency_director],
        termination_condition=    termination,
        allow_repeated_speaker=True,  # Allow an agent to speak multiple turns in a row.
        model_client=model_client,
        selector_prompt="""Select an agent to perform task.

    {roles}

    Current conversation context:
    {history}

    Read the above conversation, then select an agent from {participants} to perform the next task.
    Make sure the agency_manager agent has assigned tasks before other agents start working.
    Only select one agent.
    """

    )



    await Console(groupchat.run_stream(task=user_task,
    ))

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:

        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("Process interrupted by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        loop.close()