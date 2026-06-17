"""
SprintMind — Jira REST API Client
Creates issues (Epics, Stories, Tasks, Subtasks) in Jira Cloud.
"""

import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()


class JiraClient:
    """Wrapper around Jira Cloud REST API v3."""

    def __init__(self):
        self.base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
        self.email = os.getenv("JIRA_EMAIL", "")
        self.api_token = os.getenv("JIRA_API_TOKEN", "")
        self.project_key = os.getenv("JIRA_PROJECT_KEY", "")
        self.auth = HTTPBasicAuth(self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, json_data: dict = None) -> dict:
        """Make an authenticated request to Jira REST API."""
        url = f"{self.base_url}/rest/api/3/{endpoint}"
        response = requests.request(
            method,
            url,
            headers=self.headers,
            auth=self.auth,
            json=json_data,
            timeout=30,
        )
        response.raise_for_status()
        return response.json() if response.text else {}

    def create_issue(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        story_points: int = None,
        acceptance_criteria: list[str] = None,
    ) -> dict:
        """
        Create a Jira issue.

        Args:
            summary: Issue title
            description: Issue description (plain text, converted to ADF)
            issue_type: One of Epic, Story, Task, Sub-task
            story_points: Optional story point estimate
            acceptance_criteria: Optional list of acceptance criteria strings

        Returns:
            Dict with 'key' and 'self' URL of created issue
        """
        # Build description in Atlassian Document Format (ADF)
        desc_content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": description}],
            }
        ]

        # Append acceptance criteria as a bullet list if provided
        if acceptance_criteria:
            desc_content.append(
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Acceptance Criteria:",
                            "marks": [{"type": "strong"}],
                        }
                    ],
                }
            )
            desc_content.append(
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": ac}],
                                }
                            ],
                        }
                        for ac in acceptance_criteria
                    ],
                }
            )

        fields = {
            "project": {"key": self.project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": desc_content,
            },
            "issuetype": {"name": issue_type},
        }

        # Story points — field name varies by Jira config; common ones:
        if story_points is not None:
            fields["story_points"] = story_points

        payload = {"fields": fields}
        result = self._request("POST", "issue", payload)
        return {"key": result["key"], "url": f"{self.base_url}/browse/{result['key']}"}

    def create_subtask(
        self,
        parent_key: str,
        summary: str,
        description: str,
        story_points: int = None,
        acceptance_criteria: list[str] = None,
    ) -> dict:
        """Create a subtask under a parent issue."""
        desc_content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": description}],
            }
        ]

        if acceptance_criteria:
            desc_content.append(
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Acceptance Criteria:",
                            "marks": [{"type": "strong"}],
                        }
                    ],
                }
            )
            desc_content.append(
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": ac}],
                                }
                            ],
                        }
                        for ac in acceptance_criteria
                    ],
                }
            )

        fields = {
            "project": {"key": self.project_key},
            "parent": {"key": parent_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": desc_content,
            },
            "issuetype": {"name": "Sub-task"},
        }

        if story_points is not None:
            fields["story_points"] = story_points

        payload = {"fields": fields}
        result = self._request("POST", "issue", payload)
        return {"key": result["key"], "url": f"{self.base_url}/browse/{result['key']}"}

    def test_connection(self) -> dict:
        """Test Jira connection by fetching current user."""
        return self._request("GET", "myself")
