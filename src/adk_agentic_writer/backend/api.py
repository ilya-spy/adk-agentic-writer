"""FastAPI backend server for the ADK Agentic Writer system."""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..agents import (
    CoordinatorAgent,
    GameDesignerAgent,
    QuizWriterAgent,
    ReviewerAgent,
    SimulationDesignerAgent,
    StoryWriterAgent,
)
from ..models import ContentRequest, ContentResponse, ContentType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global agent system
agent_system: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the agent system."""
    # Startup: Initialize agents
    logger.info("Initializing multi-agent system...")
    
    coordinator = CoordinatorAgent()
    
    # Create specialized agents
    quiz_writer = QuizWriterAgent()
    story_writer = StoryWriterAgent()
    game_designer = GameDesignerAgent()
    simulation_designer = SimulationDesignerAgent()
    reviewer = ReviewerAgent()
    
    # Register agents with coordinator
    coordinator.register_agent(quiz_writer)
    coordinator.register_agent(story_writer)
    coordinator.register_agent(game_designer)
    coordinator.register_agent(simulation_designer)
    coordinator.register_agent(reviewer)
    
    # Store in global state
    agent_system["coordinator"] = coordinator
    agent_system["agents"] = {
        "quiz_writer": quiz_writer,
        "story_writer": story_writer,
        "game_designer": game_designer,
        "simulation_designer": simulation_designer,
        "reviewer": reviewer,
    }
    
    logger.info("Multi-agent system initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down multi-agent system...")
    agent_system.clear()


# Create FastAPI app
app = FastAPI(
    title="ADK Agentic Writer API",
    description="Multi-agentic system for interactive content production",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "ADK Agentic Writer API",
        "version": "0.1.0",
        "status": "operational",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/agents")
async def list_agents() -> Dict[str, List[Dict[str, str]]]:
    """List all available agents and their status."""
    agents = agent_system.get("agents", {})
    
    agent_info = []
    for agent_id, agent in agents.items():
        state = agent.get_state()
        agent_info.append({
            "agent_id": state.agent_id,
            "role": state.role.value,
            "status": state.status.value,
        })
    
    return {"agents": agent_info}


@app.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest) -> ContentResponse:
    """
    Generate interactive content using the multi-agent system.
    
    Args:
        request: ContentRequest with content_type, topic, and parameters
        
    Returns:
        ContentResponse with generated content
    """
    logger.info(f"Received request to generate {request.content_type}: {request.topic}")
    
    coordinator = agent_system.get("coordinator")
    if not coordinator:
        raise HTTPException(status_code=503, detail="Agent system not initialized")
    
    try:
        # Process the request through the coordinator
        result = await coordinator.process_task(
            task_description=request.topic,
            parameters={
                "content_type": request.content_type,
                "topic": request.topic,
                **request.parameters,
            },
        )
        
        # Create response
        response = ContentResponse(
            request_id=str(uuid.uuid4()),
            content_type=request.content_type,
            content=result.get("content", {}),
            agents_involved=result.get("agents_involved", []),
        )
        
        logger.info(f"Successfully generated {request.content_type} content")
        return response
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@app.get("/content-types")
async def get_content_types() -> Dict[str, Any]:
    """Get available content types."""
    return {
        "content_types": [ct.value for ct in ContentType],
        "descriptions": {
            ContentType.QUIZ.value: "Interactive quizzes with multiple choice questions",
            ContentType.QUEST_GAME.value: "Quest-based adventure games with choices and rewards",
            ContentType.BRANCHED_NARRATIVE.value: "Branching storylines with multiple endings",
            ContentType.WEB_SIMULATION.value: "Interactive simulations with variables and controls",
        },
    }


@app.post("/generate/quiz")
async def generate_quiz(topic: str, num_questions: int = 5) -> Dict[str, Any]:
    """Convenience endpoint for generating quizzes."""
    request = ContentRequest(
        content_type=ContentType.QUIZ,
        topic=topic,
        parameters={"num_questions": num_questions},
    )
    return await generate_content(request)


@app.post("/generate/story")
async def generate_story(topic: str, genre: str = "fantasy") -> Dict[str, Any]:
    """Convenience endpoint for generating branched narratives."""
    request = ContentRequest(
        content_type=ContentType.BRANCHED_NARRATIVE,
        topic=topic,
        parameters={"genre": genre},
    )
    return await generate_content(request)


@app.post("/generate/game")
async def generate_game(topic: str, complexity: str = "medium") -> Dict[str, Any]:
    """Convenience endpoint for generating quest games."""
    request = ContentRequest(
        content_type=ContentType.QUEST_GAME,
        topic=topic,
        parameters={"complexity": complexity},
    )
    return await generate_content(request)


@app.post("/generate/simulation")
async def generate_simulation(topic: str, simulation_type: str = "chart") -> Dict[str, Any]:
    """Convenience endpoint for generating web simulations."""
    request = ContentRequest(
        content_type=ContentType.WEB_SIMULATION,
        topic=topic,
        parameters={"simulation_type": simulation_type},
    )
    return await generate_content(request)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
