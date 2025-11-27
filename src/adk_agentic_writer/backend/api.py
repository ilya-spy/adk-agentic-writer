"""FastAPI backend server for the ADK Agentic Writer system."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from ..agents.static import (
    CoordinatorAgent as StaticCoordinator,
    StaticQuizWriterAgent,
    StoryWriterAgent,
    GameDesignerAgent,
    SimulationDesignerAgent,
    ReviewerAgent as StaticReviewer,
)
from ..models import ContentType

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gemini agents are optional
try:
    from ..agents.gemini import (
        GeminiCoordinatorAgent,
        GeminiQuizWriterAgent,
        GeminiStoryWriterAgent,
        GeminiGameDesignerAgent,
        GeminiSimulationDesignerAgent,
        GeminiReviewerAgent,
        SupportedTask,
    )

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini agents not available (google.adk not installed)")

# Global agent systems - initialize with empty dicts
agent_systems: Dict[str, Any] = {
    "static": {"initialized": False, "coordinator": None},
    "gemini": {"initialized": False, "coordinator": None},
}


class GenerateRequest(BaseModel):
    """Request model for content generation."""

    team: str = "static"  # "static" or "gemini"
    content_type: str
    topic: str
    parameters: Dict[str, Any] = {}


class GenerateResponse(BaseModel):
    """Response model for content generation."""

    request_id: str
    team: str
    content_type: str
    content: Dict[str, Any]
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup the agent systems."""
    logger.info("Initializing ADK multi-agent systems...")

    # Initialize Static Team
    try:
        # New coordinator auto-registers agents via runtime
        static_coordinator = StaticCoordinator(agent_id="static_coordinator")

        agent_systems["static"]["coordinator"] = static_coordinator
        agent_systems["static"]["initialized"] = True
        logger.info("Static team initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize static team: {e}")
        agent_systems["static"]["initialized"] = False

    # Initialize Gemini Team (if available)
    if GEMINI_AVAILABLE:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                gemini_coordinator = GeminiCoordinatorAgent(
                    agent_id="gemini_coordinator"
                )
                gemini_coordinator.register_agent(GeminiQuizWriterAgent())
                gemini_coordinator.register_agent(GeminiStoryWriterAgent())
                gemini_coordinator.register_agent(GeminiGameDesignerAgent())
                gemini_coordinator.register_agent(GeminiSimulationDesignerAgent())
                gemini_coordinator.register_agent(GeminiReviewerAgent())

                agent_systems["gemini"]["coordinator"] = gemini_coordinator
                agent_systems["gemini"]["initialized"] = True
                logger.info("Gemini team initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize gemini team: {e}")
                agent_systems["gemini"]["initialized"] = False
        else:
            logger.warning("No GOOGLE_API_KEY found - Gemini team unavailable")
            agent_systems["gemini"]["initialized"] = False
    else:
        logger.warning("Gemini agents not available (google.adk package not installed)")
        agent_systems["gemini"]["initialized"] = False

    yield

    # Shutdown
    logger.info("Shutting down ADK multi-agent systems...")
    agent_systems.clear()


# Create FastAPI app
app = FastAPI(
    title="ADK Agentic Writer API",
    description="Multi-agentic system for interactive content production",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the server directory page."""
    import pathlib

    # Get the path to the frontend/public/index.html
    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    index_path = project_root / "frontend" / "public" / "index.html"

    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    else:
        # Fallback to JSON response if file not found
        return HTMLResponse(
            content="""
            <html>
                <head><title>ADK Agentic Writer</title></head>
                <body>
                    <h1>ADK Agentic Writer API</h1>
                    <p>Server is running!</p>
                    <ul>
                        <li><a href="/health">Health Check</a></li>
                        <li><a href="/teams">Available Teams</a></li>
                        <li><a href="/docs">API Documentation</a></li>
                    </ul>
                </body>
            </html>
            """,
            status_code=200,
        )


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "message": "ADK Agentic Writer API",
        "version": "1.0.0",
        "teams": {
            "static": agent_systems["static"].get("initialized", False),
            "gemini": agent_systems["gemini"].get("initialized", False),
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "static_team": agent_systems["static"].get("initialized", False),
        "gemini_team": agent_systems["gemini"].get("initialized", False),
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate_content(request: GenerateRequest):
    """Generate content using specified team."""
    request_id = str(uuid.uuid4())

    # Validate team
    if request.team not in ["static", "gemini"]:
        raise HTTPException(status_code=400, detail=f"Invalid team: {request.team}")

    # Check if team is initialized
    if not agent_systems[request.team].get("initialized"):
        raise HTTPException(
            status_code=503, detail=f"{request.team.capitalize()} team not available"
        )

    # Get coordinator
    coordinator = agent_systems[request.team]["coordinator"]

    try:
        # Prepare parameters
        params = request.parameters.copy() if request.parameters else {}
        topic = request.topic

        # Generate content based on team and content type
        if request.team == "static":
            # Static team uses generate_content method
            result = await coordinator.generate_content(
                content_type=request.content_type, topic=topic, **params
            )
        else:
            # Gemini team uses structured tasks (old interface for now)
            params["content_type"] = request.content_type
            params["topic"] = topic

            if GEMINI_AVAILABLE and SupportedTask:
                task_mapping = {
                    "quiz": SupportedTask.GENERATE_QUIZ,
                    "branched_narrative": SupportedTask.GENERATE_STORY,
                    "quest_game": SupportedTask.GENERATE_GAME,
                    "web_simulation": SupportedTask.GENERATE_SIMULATION,
                }
                task = task_mapping.get(
                    request.content_type, SupportedTask.GENERATE_QUIZ
                )
                params["task"] = task

            # Note: Gemini coordinator still uses old interface
            result = await coordinator.process_task(
                f"Generate {request.content_type}", params
            )

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=result,
            status="completed",
        )

    except ValueError as e:
        # Handle invalid content types gracefully
        logger.warning(f"Invalid content type or parameters: {e}")
        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content={"error": str(e), "status": "failed"},
            status="error",
        )
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/with-review", response_model=GenerateResponse)
async def generate_with_review(request: GenerateRequest):
    """Generate content with review and refinement cycles."""
    request_id = str(uuid.uuid4())

    if request.team != "static":
        raise HTTPException(
            status_code=400, detail="Review workflow only available for static team"
        )

    if not agent_systems["static"].get("initialized"):
        raise HTTPException(status_code=503, detail="Static team not available")

    coordinator = agent_systems["static"]["coordinator"]

    try:
        params = request.parameters.copy() if request.parameters else {}
        max_iterations = params.pop("max_iterations", 2)

        # Generate content using coordinator
        result = await coordinator.generate_content(
            content_type=request.content_type, topic=request.topic, **params
        )

        # Implement review cycles here
        reviewer = coordinator._get_reviewer()
        review_history = []

        for iteration in range(max_iterations):
            review = await reviewer.process_task(
                None,
                {
                    "content": result["content"],
                    "content_type": request.content_type,
                    "criteria": ["clarity", "engagement", "structure", "completeness"],
                },
            )
            review_history.append(review)

            if review["status"] == "approved":
                break

        # Add review metadata
        result_with_review = {
            **result,
            "review_history": review_history,
            "final_status": (
                review_history[-1]["status"] if review_history else "unreviewed"
            ),
            "iterations": len(review_history),
        }

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=result_with_review,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating with review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/multimodal-story")
async def generate_multimodal_story(request: GenerateRequest):
    """Generate complex multimodal story with embedded games and quizzes."""
    request_id = str(uuid.uuid4())

    if request.team != "static":
        raise HTTPException(
            status_code=400,
            detail="Multimodal stories only available for static team",
        )

    if not agent_systems["static"].get("initialized"):
        raise HTTPException(status_code=503, detail="Static team not available")

    coordinator = agent_systems["static"]["coordinator"]

    try:
        params = request.parameters.copy() if request.parameters else {}
        num_story_nodes = params.get("num_story_nodes", 8)
        num_mini_games = params.get("num_mini_games", 2)
        num_mini_quizzes = params.get("num_mini_quizzes", 2)
        genre = params.get("genre", "adventure")

        # Parallel generation
        results = await asyncio.gather(
            coordinator.generate_content(
                "branched_narrative",
                request.topic,
                num_nodes=num_story_nodes,
                genre=genre,
            ),
            *[
                coordinator.generate_content(
                    "quest_game", f"{request.topic} Mini-Game {i+1}", num_nodes=4
                )
                for i in range(num_mini_games)
            ],
            *[
                coordinator.generate_content(
                    "quiz", f"{request.topic} Quiz {i+1}", num_questions=3
                )
                for i in range(num_mini_quizzes)
            ],
            return_exceptions=True,
        )

        # Extract and integrate
        story_result = results[0] if not isinstance(results[0], Exception) else None
        if not story_result:
            raise ValueError("Story generation failed")

        story_content = story_result["content"]
        nodes = story_content.get("nodes", {})

        # Inject games and quizzes
        game_results = results[1 : 1 + num_mini_games]
        quiz_results = results[1 + num_mini_games :]

        for i, result in enumerate(game_results):
            if not isinstance(result, Exception) and i + 1 < len(nodes):
                node_id = list(nodes.keys())[i + 1]
                nodes[node_id]["embedded_game"] = result["content"]

        for i, result in enumerate(quiz_results):
            if not isinstance(result, Exception) and num_mini_games + i + 1 < len(
                nodes
            ):
                node_id = list(nodes.keys())[num_mini_games + i + 1]
                nodes[node_id]["embedded_quiz"] = result["content"]

        multimodal_result = {
            "content_type": "multimodal_story",
            "content": story_content,
            "embedded_games": sum(
                1 for r in game_results if not isinstance(r, Exception)
            ),
            "embedded_quizzes": sum(
                1 for r in quiz_results if not isinstance(r, Exception)
            ),
            "total_nodes": len(nodes),
            "generation_method": "parallel_mixed_team",
        }

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type="multimodal_story",
            content=multimodal_result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating multimodal story: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/adaptive")
async def generate_adaptive(request: GenerateRequest):
    """Generate content with adaptive workflow based on quality metrics."""
    request_id = str(uuid.uuid4())

    if request.team != "static":
        raise HTTPException(
            status_code=400, detail="Adaptive workflow only available for static team"
        )

    if not agent_systems["static"].get("initialized"):
        raise HTTPException(status_code=503, detail="Static team not available")

    coordinator = agent_systems["static"]["coordinator"]

    try:
        params = request.parameters.copy() if request.parameters else {}
        quality_threshold = params.pop("quality_threshold", 7.5)

        # Generate content
        result = await coordinator.generate_content(
            content_type=request.content_type, topic=request.topic, **params
        )

        # Quick review
        reviewer = coordinator._get_reviewer()
        review = await reviewer.process_task(
            None,
            {
                "content": result["content"],
                "content_type": request.content_type,
                "criteria": ["clarity", "engagement"],
            },
        )

        # Adaptive branching
        workflow_path = (
            "enhanced" if review["overall_score"] >= quality_threshold else "refined"
        )

        if workflow_path == "enhanced" and request.content_type in [
            "branched_narrative",
            "story",
        ]:
            result["content"]["metadata"] = result["content"].get("metadata", {})
            result["content"]["metadata"]["enhanced"] = True

        adaptive_result = {
            **result,
            "review": review,
            "workflow_path": workflow_path,
            "adaptive": True,
        }

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=adaptive_result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating adaptive content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate/parallel-variants")
async def generate_parallel_variants(request: GenerateRequest):
    """Generate multiple variants in parallel and select the best."""
    request_id = str(uuid.uuid4())

    if request.team != "static":
        raise HTTPException(
            status_code=400,
            detail="Parallel variants only available for static team",
        )

    if not agent_systems["static"].get("initialized"):
        raise HTTPException(status_code=503, detail="Static team not available")

    coordinator = agent_systems["static"]["coordinator"]

    try:
        params = request.parameters.copy() if request.parameters else {}
        num_variants = params.pop("num_variants", 3)
        params.pop("merge_best", True)  # Remove unused parameter

        # Generate variants in parallel
        variants = await asyncio.gather(
            *[
                coordinator.generate_content(
                    request.content_type, request.topic, **params
                )
                for _ in range(num_variants)
            ],
            return_exceptions=True,
        )

        valid_variants = [v for v in variants if not isinstance(v, Exception)]
        if not valid_variants:
            raise ValueError("No valid variants generated")

        # Review all variants
        reviewer = coordinator._get_reviewer()
        reviews = await asyncio.gather(
            *[
                reviewer.process_task(
                    None,
                    {
                        "content": v["content"],
                        "content_type": request.content_type,
                        "criteria": ["clarity", "engagement", "completeness"],
                    },
                )
                for v in valid_variants
            ]
        )

        # Select best variant
        best_idx = max(enumerate(reviews), key=lambda x: x[1]["overall_score"])[0]

        variant_result = {
            **valid_variants[best_idx],
            "variant_scores": [r["overall_score"] for r in reviews],
            "selected_variant": best_idx,
            "num_variants": len(valid_variants),
            "num_variants_generated": len(valid_variants),
            "generation_method": "parallel_selection",
        }

        return GenerateResponse(
            request_id=request_id,
            team=request.team,
            content_type=request.content_type,
            content=variant_result,
            status="completed",
        )

    except Exception as e:
        logger.error(f"Error generating parallel variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/showcase", response_class=HTMLResponse)
async def showcase():
    """Serve the showcase page."""
    import pathlib

    # Get the path to the frontend/public/showcase.html
    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    showcase_path = project_root / "frontend" / "public" / "showcase.html"

    if showcase_path.exists():
        return showcase_path.read_text(encoding="utf-8")
    else:
        return HTMLResponse(
            content="<html><body><h1>Showcase page not found</h1></body></html>",
            status_code=404,
        )


@app.get("/frontend", response_class=HTMLResponse)
async def frontend():
    """Serve the legacy frontend page."""
    import pathlib

    current_file = pathlib.Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    frontend_path = project_root / "frontend" / "public" / "frontend.html"

    if frontend_path.exists():
        return frontend_path.read_text(encoding="utf-8")
    else:
        return HTMLResponse(
            content="<html><body><h1>Frontend page not found</h1></body></html>",
            status_code=404,
        )


@app.get("/teams")
async def get_teams():
    """Get available teams and their status."""
    return {
        "teams": [
            {
                "id": "static",
                "name": "Static Team",
                "description": "Fast, template-based generation. No API calls required.",
                "available": agent_systems["static"].get("initialized", False),
                "icon": "⚡",
            },
            {
                "id": "gemini",
                "name": "Gemini Team",
                "description": "AI-powered generation via Google ADK. High quality, creative.",
                "available": agent_systems["gemini"].get("initialized", False),
                "icon": "🤖",
            },
        ]
    }


@app.get("/content-types")
async def get_content_types():
    """Get available content types."""
    return {
        "content_types": [
            {
                "value": "quiz",
                "label": "Quiz",
                "description": "Interactive quizzes with multiple choice questions",
            },
            {
                "value": "quest_game",
                "label": "Quest Game",
                "description": "Quest-based adventure games with choices and rewards",
            },
            {
                "value": "branched_narrative",
                "label": "Branched Story",
                "description": "Branching storylines with multiple endings",
            },
            {
                "value": "web_simulation",
                "label": "Simulation",
                "description": "Interactive simulations with variables and controls",
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
