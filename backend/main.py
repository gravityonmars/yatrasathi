import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from backend.models.forex import get_forex
from backend.models.weather import get_weather
from backend.models.rag import query_rag

load_dotenv()

GROQ_API_KEY = Groq(api_key=os.getenv("GROQ_API_KEY"))

def search_travel_guide(query: str) -> dict:
    """Search internal Nepal travel documents, permits (TIMS, ACAP, Sagarmatha), FAQs, and guidelines.

    Args:
        query: Specific search phrase or question about Nepal destinations or local rules.
    """
    context = query_rag(query)
    if not context.strip():
        return {"result": "No matching document entries found."}
    return {"result": context}


APP_NAME = "yatrasathi_app"

SYSTEM_INSTRUCTION = """You are YatraSathi, an expert AI travel assistant for Nepal.
Your goal is to assist travelers with itinerary planning, local culture, mountain trekking advice, live weather forecasts, and currency conversions.

Guidelines:
1. Use `get_weather` when users ask for weather conditions or forecasts for locations/coordinates.
2. Use `get_forex` whenever currency exchange or conversion rates are requested (e.g., USD to NPR).
3. Use `search_travel_guide` whenever users ask questions about local trekking permits, regulations, or local destination guides.
4. Keep responses structured, concise, and helpful.
"""

root_agent = Agent(
    name="yatrasathi_agent",
    model=LiteLlm(
        model="groq/openai/gpt-oss-20b",
        include_reasoning=False
    ),
    instruction=SYSTEM_INSTRUCTION,
    tools=[get_forex, get_weather, search_travel_guide]
)

adk_app = App(
    name=APP_NAME,
    root_agent=root_agent
)

session_service = InMemorySessionService()

runner = Runner(
    app=adk_app,
    session_service=session_service,
    auto_create_session=True
)

api = FastAPI(
    title="YatraSathi API",
    version="1.0.0",
    description="Nepal Travel Assistant Backend using Google ADK and FastAPI"
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str

async def run_agent(message: str, user_id: str, session_id: str) -> str:
    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )

    response_text = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = "".join(
                    part.text
                    for part in event.content.parts
                    if part.text
                )

    return response_text

@api.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    try:
        response = await run_agent(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id
        )
        return ChatResponse(
            response=response or "No response received.",
            session_id=session_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))