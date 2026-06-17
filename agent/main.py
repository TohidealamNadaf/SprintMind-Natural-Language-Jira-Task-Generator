"""
SprintMind — FastAPI Application
Endpoints for generating tickets and pushing them to Jira.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import SprintMindAgent, TicketPlan, Ticket
from jira_client import JiraClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sprintmind")

app = FastAPI(
    title="SprintMind Agent",
    description="AI-powered feature brief → Jira ticket generator",
    version="1.0.0",
)

# CORS — allow Angular dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent and Jira client
agent = SprintMindAgent()
jira = JiraClient()


# ── Request / Response models ─────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    brief: str


class GenerateResponse(BaseModel):
    tickets: list[Ticket]


class PushRequest(BaseModel):
    tickets: list[Ticket]


class CreatedTicket(BaseModel):
    key: str
    url: str
    title: str
    type: str


class PushResponse(BaseModel):
    created: list[CreatedTicket]
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "sprintmind-agent"}


@app.post("/generate", response_model=GenerateResponse)
def generate_tickets(request: GenerateRequest):
    """
    Generate Jira tickets from a feature brief using Gemini.

    Accepts a plain-English feature description and returns structured
    tickets with types, descriptions, acceptance criteria, and story points.
    """
    if not request.brief.strip():
        raise HTTPException(status_code=400, detail="Brief cannot be empty")

    try:
        logger.info(f"Generating tickets for brief: {request.brief[:100]}...")
        plan = agent.generate_tickets(request.brief)
        logger.info(f"Generated {len(plan.tickets)} tickets")
        return GenerateResponse(tickets=plan.tickets)
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ticket generation failed: {str(e)}")


@app.post("/push", response_model=PushResponse)
def push_to_jira(request: PushRequest):
    """
    Create tickets in Jira.

    Takes the generated ticket list and creates them in Jira,
    respecting parent-child relationships (Epics → Stories → Sub-tasks).
    """
    if not request.tickets:
        raise HTTPException(status_code=400, detail="No tickets to push")

    created = []
    # Map ticket titles to Jira keys for parent linking
    title_to_key: dict[str, str] = {}

    try:
        # Sort: Epics first, then Stories/Tasks, then Sub-tasks
        type_order = {"Epic": 0, "Story": 1, "Task": 1, "Sub-task": 2}
        sorted_tickets = sorted(
            request.tickets,
            key=lambda t: type_order.get(t.type, 1)
        )

        for ticket in sorted_tickets:
            logger.info(f"Creating {ticket.type}: {ticket.title}")

            if ticket.type == "Sub-task" and ticket.parent:
                parent_key = title_to_key.get(ticket.parent)
                if not parent_key:
                    logger.warning(
                        f"Parent '{ticket.parent}' not found for subtask '{ticket.title}', creating as Task"
                    )
                    result = jira.create_issue(
                        summary=ticket.title,
                        description=ticket.description,
                        issue_type="Task",
                        story_points=ticket.story_points,
                        acceptance_criteria=ticket.acceptance_criteria,
                    )
                else:
                    result = jira.create_subtask(
                        parent_key=parent_key,
                        summary=ticket.title,
                        description=ticket.description,
                        story_points=ticket.story_points,
                        acceptance_criteria=ticket.acceptance_criteria,
                    )
            else:
                result = jira.create_issue(
                    summary=ticket.title,
                    description=ticket.description,
                    issue_type=ticket.type,
                    story_points=ticket.story_points,
                    acceptance_criteria=ticket.acceptance_criteria,
                )

            title_to_key[ticket.title] = result["key"]
            created.append(
                CreatedTicket(
                    key=result["key"],
                    url=result["url"],
                    title=ticket.title,
                    type=ticket.type,
                )
            )
            logger.info(f"Created {result['key']}: {ticket.title}")

        return PushResponse(
            created=created,
            message=f"Successfully created {len(created)} tickets in Jira",
        )

    except Exception as e:
        logger.error(f"Jira push failed: {e}")
        # Return partial results if some tickets were created
        if created:
            return PushResponse(
                created=created,
                message=f"Partially created {len(created)} tickets. Error: {str(e)}",
            )
        raise HTTPException(status_code=500, detail=f"Jira push failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
