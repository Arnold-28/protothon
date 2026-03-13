"""Patch Generator - LLM-powered code patch generation based on issue analysis and code context."""

import logging

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert software engineer generating code patches.
Given an issue analysis and relevant code context from the repository, generate
a unified diff patch that resolves the issue.

Rules:
1. Only modify files that are necessary to fix the issue.
2. Generate valid unified diff format that can be applied with `git apply`.
3. Include proper file paths (a/ and b/ prefixes).
4. Keep changes minimal and focused on the issue.
5. Follow the existing code style and conventions visible in the context.
6. Add appropriate comments only where the logic is non-obvious.

Output ONLY the unified diff patch, wrapped in a ```diff code block.
If you also need to create new files, use /dev/null as the old file path."""


class PatchGenerator:
    """Generates code patches using an LLM based on issue context and codebase knowledge."""

    def __init__(self) -> None:
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL

    def generate_patch(
        self,
        issue_analysis: dict[str, str],
        code_context: str,
        repo_name: str,
    ) -> dict[str, str]:
        """Generate a code patch to resolve a GitHub issue.

        Args:
            issue_analysis: Output from the IssueInterpreter.
            code_context: Formatted relevant code snippets from the retriever.
            repo_name: The repository name for reference.

        Returns:
            Dictionary with keys: patch, explanation, files_modified.
        """
        user_prompt = self._build_prompt(issue_analysis, code_context, repo_name)

        logger.info("Generating patch for issue: %s", issue_analysis.get("summary", ""))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=4000,
        )

        raw_response = response.choices[0].message.content or ""
        patch = self._extract_patch(raw_response)
        files_modified = self._extract_files_from_patch(patch)

        logger.info("Patch generated. Files modified: %s", ", ".join(files_modified))

        return {
            "patch": patch,
            "explanation": raw_response,
            "files_modified": ", ".join(files_modified),
        }

    def _build_prompt(
        self,
        issue_analysis: dict[str, str],
        code_context: str,
        repo_name: str,
    ) -> str:
        """Build the prompt for the LLM with issue and code context.

        Args:
            issue_analysis: The interpreted issue data.
            code_context: Formatted code snippets from the retriever.
            repo_name: Repository name.

        Returns:
            Formatted prompt string.
        """
        return (
            f"## Repository\n{repo_name}\n\n"
            f"## Issue Summary\n{issue_analysis.get('summary', 'N/A')}\n\n"
            f"## Issue Type\n{issue_analysis.get('issue_type', 'N/A')}\n\n"
            f"## Suggested Approach\n{issue_analysis.get('suggested_approach', 'N/A')}\n\n"
            f"## Relevant Code Context\n{code_context}\n\n"
            "## Instructions\n"
            "Generate a unified diff patch that resolves this issue. "
            "Only include necessary changes."
        )

    def _extract_patch(self, response: str) -> str:
        """Extract the unified diff patch from the LLM response.

        Args:
            response: Raw LLM response containing a diff code block.

        Returns:
            The extracted patch string.
        """
        # Look for diff code block
        if "```diff" in response:
            start = response.index("```diff") + len("```diff")
            end = response.index("```", start)
            return response[start:end].strip()

        # Fallback: look for generic code block
        if "```" in response:
            start = response.index("```") + 3
            # Skip language identifier if present on the same line
            newline_pos = response.index("\n", start)
            start = newline_pos + 1
            end = response.index("```", start)
            return response[start:end].strip()

        return response.strip()

    def _extract_files_from_patch(self, patch: str) -> list[str]:
        """Extract the list of modified files from a unified diff patch.

        Args:
            patch: Unified diff string.

        Returns:
            List of file paths that are modified in the patch.
        """
        files: list[str] = []
        for line in patch.split("\n"):
            if line.startswith("+++ b/"):
                filepath = line[6:].strip()
                if filepath and filepath != "/dev/null":
                    files.append(filepath)
        return files
