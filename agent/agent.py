"""
SprintMind — LangChain Agent with Google Gemini
Parses feature briefs into structured Jira tickets.
"""

import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

load_dotenv()


# ── Pydantic models for structured output ──────────────────────────────────────

class Ticket(BaseModel):
    """A single Jira ticket generated from a feature brief."""
    type: str           # Epic, Story, Task, Sub-task
    title: str          # Short summary / ticket title
    description: str    # Detailed description
    acceptance_criteria: list[str]  # List of ACs
    story_points: int   # Fibonacci estimate (1,2,3,5,8,13)
    parent: str | None = None  # Title of parent ticket (for Stories under Epics)


class TicketPlan(BaseModel):
    """Full plan of tickets generated from a feature brief."""
    tickets: list[Ticket]


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are SprintMind, an expert Agile product manager and technical lead.

Given a feature brief, you decompose it into a structured set of Jira tickets following these rules:

1. **Hierarchy**: Create 1-2 Epics at the top level. Under each Epic, create Stories. Under complex Stories, create Sub-tasks.
2. **Ticket Quality**:
   - Titles must be concise and action-oriented (start with a verb)
   - Descriptions must be detailed enough for a developer to start work
   - Each ticket MUST have 2-4 specific, testable acceptance criteria
   - Story points use Fibonacci: 1, 2, 3, 5, 8, 13
3. **Coverage**: Ensure the full scope of the brief is covered. Include:
   - Frontend/UI work
   - Backend/API work
   - Database/data model changes
   - Testing requirements
   - Documentation if needed
4. **Parent references**: For Stories, set `parent` to the exact title of the parent Epic. For Sub-tasks, set `parent` to the exact title of the parent Story. Epics have `parent: null`.
5. **Output**: Return ONLY valid JSON matching this schema:

{
  "tickets": [
    {
      "type": "Epic|Story|Task|Sub-task",
      "title": "...",
      "description": "...",
      "acceptance_criteria": ["AC1", "AC2"],
      "story_points": 5,
      "parent": null | "Parent Title"
    }
  ]
}

Do NOT include markdown code fences. Return raw JSON only."""


# ── Agent class ────────────────────────────────────────────────────────────────

class SprintMindAgent:
    """LangChain agent that uses Gemini to generate Jira tickets from briefs."""

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set in environment")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.3,  # Low temp for consistent, structured output
        )

    def generate_tickets(self, brief: str) -> TicketPlan:
        """
        Generate structured tickets from a feature brief.

        Args:
            brief: Plain-English feature description

        Returns:
            TicketPlan with list of Ticket objects
        """
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=f"Feature Brief:\n\n{brief}"),
        ]

        response = self.llm.invoke(messages)
        raw_text = response.content.strip()

        # Clean up potential markdown fences
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            # Remove first line (```json) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            raw_text = "\n".join(lines)

        parsed = json.loads(raw_text)
        return TicketPlan(**parsed)
