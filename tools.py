import asyncio
import json
import os

import dotenv
import requests
from autogen_agentchat.agents import UserProxyAgent, AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from bs4 import BeautifulSoup

dotenv.load_dotenv()

BROWSERLESS_API_KEY = os.getenv("BROWSERLESS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")








def search(query:str):
    """Search the web using Serper API.
    This function sends a search query to the Serper API and returns the response.
    Args:
        query (str): The search query.
    """

    try:
        url = "https://google.serper.dev/search"

        payload = json.dumps({
            "q": query
        })
        headers = {
            'X-API-KEY': os.getenv("SERPER_API_KEY"),
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return response.text
    except Exception as e:
        print(f"Error occurred while searching: {e}")
        return f"Error occurred while searching: {e}"

def scrape(url: str):
    """Scrape a website and summarize its content if it's too large.
    This function sends a request to the specified URL using the Browserless API,
    Args:
        url  (str): The URL of the website to scrape.
    """
    print("Scraping website...")
    try:
        # Define the headers for the request
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json',
        }

        # Build the POST URL
        post_url = f"https://chrome.browserless.io/content?token={BROWSERLESS_API_KEY}"

        # Send the POST request
        response = requests.post(post_url, headers=headers, json={"url": url})

        # Check the response status code
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text()
            print("CONTENTTTTTT:", text)

            # if len(text) > 8000:
            #     output = summary(text)
            #     return output
            # else:
            return text
        else:
            print(f"HTTP request failed with status code {response.status_code}")
    except :
        print("Error occurred while scraping the website.")
        return "Error occurred while scraping the website."
#
# def summary(content):
#     llm = ChatOpenAI(temperature=0, model="gpt-4o")
#     text_splitter = RecursiveCharacterTextSplitter(
#         separators=["\n\n", "\n"], chunk_size=10000, chunk_overlap=500)
#     docs = text_splitter.create_documents([content])
#     map_prompt = """
#     Write a detailed summary of the following text for a research purpose:
#     "{text}"
#     SUMMARY:
#     """
#     map_prompt_template = PromptTemplate(
#         template=map_prompt, input_variables=["text"])
#
#     summary_chain = load_summarize_chain(
#         llm=llm,
#         chain_type='map_reduce',
#         map_prompt=map_prompt_template,
#         combine_prompt=map_prompt_template,
#         verbose=True
#     )
#
#     output = summary_chain.run(input_documents=docs,)
#
#     return output


# out = scrape("https://www.iefimerida.gr/")
# print("OUTTTTTTTTTTTTTTTT:", out)
def research(query:str):
    """
    Research about a given topic, return the research material including reference links
    This function calls the search function to get relevant information from the web and then scrapes the content of the website.
    Args:
        research_query (str): The topic to be researched about

    Returns:

    """
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

    researcher = AssistantAgent(
        name="researcher",
        system_message="Research about a given research_query, collect as many information as possible,"
                       " and generate detailed research results with loads of technique details with all reference links attached; Add TERMINATE to the end of the research report;",
        model_client=model_client,
        tools=[search,scrape],
        reflect_on_tool_use=True,    )

    # user_proxy = UserProxyAgent(
    #     name="User_proxy",
    #
    # )
    #groupchat = RoundRobinGroupChat([ researcher])
    results = asyncio.run(researcher.run(task=f"Research about {query}"))
    return results.messages[-1].content

def write_content(research_material:str, topic:str):
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

    editor = AssistantAgent(
        name="editor",
        description="Seasoned editor skilled in structuring blog posts for clarity and coherence, using material from the Research Assistant.",
        system_message='''
        Welcome, Senior Editor.
        As a seasoned professional, you bring meticulous attention to detail, a deep appreciation for literary and cultural nuance, and a commitment to upholding the highest editorial standards. 
        Your role is to craft the structure of a short blog post using the material from the Research Assistant. Use your experience to ensure clarity, coherence, and precision. 
        Once structured, pass it to the Writer to pen the final piece.
        ''',
        model_client=model_client,    )

    writer = AssistantAgent(
        name="writer",
        description="Blogger tasked with composing short blog posts using the structure from the Editor, embodying clear, concise, and journalistic style.",
        system_message='''
        Welcome, Blogger.
        Your task is to compose a short blog post using the structure given by the Editor and incorporating feedback from the Reviewer. 
        Embrace stylistic minimalism: be clear, concise, and direct. 
        Approach the topic from a journalistic perspective; aim to inform and engage the readers without adopting a sales-oriented tone. 
        After two rounds of revisions, conclude your post with "TERMINATE".
        ''',
        model_client=model_client,
    )

    reviewer = AssistantAgent(
        name="reviewer",
        description="Expert blog content critic focused on reviewing and providing feedback to ensure the highest standards of editorial excellence.",
        system_message='''
        As a distinguished blog content critic, you are known for your discerning eye, deep literary and cultural understanding, and an unwavering commitment to editorial excellence. 
        Your role is to meticulously review and critique the written blog, ensuring it meets the highest standards of clarity, coherence, and precision. 
        Provide invaluable feedback to the Writer to elevate the piece. After two rounds of content iteration, conclude with "TERMINATE".
        ''',        
        model_client=model_client,
    )

    user_proxy = UserProxyAgent(
        name="admin",
        description="A human admin. Interact with editor to discuss the structure. Actual writing needs to be approved by this admin.",

    )

    groupchat = RoundRobinGroupChat([user_proxy, editor, writer, reviewer],
        termination_condition=    TextMentionTermination("APPROVE")|TextMentionTermination("TERMINATE",sources=["writer"]))
   

    results = asyncio.run(groupchat.run(
        task=f"Write a blog about {topic}, here are the material: {research_material}"))

    return results.messages[-1].content