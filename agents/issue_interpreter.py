"""Issue Interpreter - LLM-powered analysis of GitHub issues."""

import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert software engineer analyzing GitHub issues.
Your job is to interpret the issue and produce a clear, actionable summary that
another AI agent can use to generate a code patch.

For each issue, provide:
1. **Summary**: A concise description of what the issue is about.
2. **Issue Type**: One of [bug, feature, refactor, documentation, test, other].
3. **Affected Areas**: Which parts of the codebase are likely involved.
4. **Suggested Approach**: High-level steps to resolve the issue.
5. **Search Queries**: 2-3 natural language queries to search the codebase for relevant code.

Respond in a structured format."""


class IssueInterpreter:
    """Interprets GitHub issues using an LLM to produce actionable analysis."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def interpret(self, issue_title: str, issue_body: str) -> dict[str, str]:
        """Analyze a GitHub issue and return structured interpretation.

        Args:
            issue_title: The title of the GitHub issue.
            issue_body: The body/description of the GitHub issue.

        Returns:
            Dictionary with keys: summary, issue_type, affected_areas,
            suggested_approach, search_queries, raw_response.
        """
        user_prompt = (
            f"## Issue Title\n{issue_title}\n\n"
            f"## Issue Description\n{issue_body or 'No description provided.'}"
        )

        logger.info("Interpreting issue: %s", issue_title)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        raw_response = response.choices[0].message.content or ""
        logger.info("Issue interpreted successfully")

        return {
            "summary": self._extract_section(raw_response, "Summary"),
            "issue_type": self._extract_section(raw_response, "Issue Type"),
            "affected_areas": self._extract_section(raw_response, "Affected Areas"),
            "suggested_approach": self._extract_section(raw_response, "Suggested Approach"),
            "search_queries": self._extract_section(raw_response, "Search Queries"),
            "raw_response": raw_response,
        }

    def _extract_section(self, text: str, section_name: str) -> str:
        """Extract a named section from the LLM response.

        Args:
            text: The full LLM response text.
            section_name: Name of the section to extract.

        Returns:
            The extracted section content, or empty string if not found.
        """
        lines = text.split("\n")
        capturing = False
        captured: list[str] = []

        for line in lines:
            # Check if this line is a section header matching our target
            stripped = line.strip().strip("*").strip("#").strip()
            if stripped.lower().startswith(section_name.lower()):
                capturing = True
                # Capture content after the colon if on the same line
                after_colon = stripped.split(":", 1)
                if len(after_colon) > 1 and after_colon[1].strip():
                    captured.append(after_colon[1].strip())
                continue

            # Stop capturing when we hit the next section header
            if capturing and line.strip().startswith(("**", "##", "#")):
                if any(
                    line.strip().strip("*").strip("#").strip().lower().startswith(kw)
                    for kw in ["summary", "issue type", "affected", "suggested", "search"]
                ):
                    break

            if capturing:
                captured.append(line)

        return "\n".join(captured).strip()
