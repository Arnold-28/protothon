"""Code Reviewer - AI-powered automated code review for generated patches."""

import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert code reviewer performing an automated review of a proposed code patch.

Evaluate the patch on the following criteria:
1. **Correctness**: Does the patch actually fix the described issue?
2. **Code Quality**: Is the code clean, readable, and well-structured?
3. **Security**: Are there any security concerns (e.g., injection, exposed secrets)?
4. **Performance**: Are there any performance concerns?
5. **Edge Cases**: Does the patch handle edge cases appropriately?
6. **Style**: Does the patch follow the repository's existing code style?

Provide your review in this format:
- **Verdict**: APPROVE, REQUEST_CHANGES, or NEEDS_DISCUSSION
- **Score**: 1-10 (10 being perfect)
- **Summary**: Brief overall assessment.
- **Issues Found**: List of specific issues (if any).
- **Suggestions**: Recommendations for improvement (if any)."""


class CodeReviewer:
    """Performs AI-powered code review on generated patches."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def review_patch(
        self,
        patch: str,
        issue_analysis: dict[str, str],
        code_context: str,
    ) -> dict[str, str]:
        """Review a generated patch against the issue and codebase context.

        Args:
            patch: The unified diff patch to review.
            issue_analysis: The interpreted issue data.
            code_context: Relevant code context from the repository.

        Returns:
            Dictionary with keys: verdict, score, summary, issues_found,
            suggestions, raw_review.
        """
        user_prompt = (
            f"## Issue Summary\n{issue_analysis.get('summary', 'N/A')}\n\n"
            f"## Issue Type\n{issue_analysis.get('issue_type', 'N/A')}\n\n"
            f"## Relevant Codebase Context\n{code_context}\n\n"
            f"## Proposed Patch\n```diff\n{patch}\n```\n\n"
            "Please review this patch thoroughly."
        )

        logger.info("Reviewing patch...")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        raw_review = response.choices[0].message.content or ""
        logger.info("Code review completed")

        return {
            "verdict": self._extract_field(raw_review, "Verdict"),
            "score": self._extract_field(raw_review, "Score"),
            "summary": self._extract_field(raw_review, "Summary"),
            "issues_found": self._extract_field(raw_review, "Issues Found"),
            "suggestions": self._extract_field(raw_review, "Suggestions"),
            "raw_review": raw_review,
        }

    def _extract_field(self, text: str, field_name: str) -> str:
        """Extract a named field value from the review response.

        Args:
            text: The full review response.
            field_name: The field name to extract.

        Returns:
            Extracted field value or empty string.
        """
        for line in text.split("\n"):
            stripped = line.strip().strip("*").strip("-").strip()
            if stripped.lower().startswith(field_name.lower()):
                parts = stripped.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
        return ""
