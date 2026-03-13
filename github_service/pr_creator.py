"""PR Creator - Creates GitHub Pull Requests with generated patches."""

import logging
import uuid

from github import Github, GithubException
from github.Repository import Repository

from config import Config

logger = logging.getLogger(__name__)


class PRCreator:
    """Creates GitHub Pull Requests containing AI-generated patches."""

    def __init__(self) -> None:
        self.github = Github(Config.GITHUB_TOKEN)
        self.repo: Repository = self.github.get_repo(Config.REPO_NAME)

    def create_pull_request(
        self,
        issue_number: int,
        patch: str,
        issue_title: str,
        review_summary: str,
    ) -> dict[str, str | int]:
        """Create a pull request with the generated patch.

        This method:
        1. Creates a new branch from the default branch.
        2. Applies the patch by committing changed files.
        3. Opens a pull request referencing the original issue.

        Args:
            issue_number: The GitHub issue number this PR addresses.
            patch: The unified diff patch content.
            issue_title: Title of the original issue.
            review_summary: AI review summary to include in the PR body.

        Returns:
            Dictionary with PR details: number, url, title, branch.
        """
        branch_name = f"gitfix/issue-{issue_number}-{uuid.uuid4().hex[:8]}"

        # Get the default branch and its latest commit SHA
        default_branch = self.repo.default_branch
        base_ref = self.repo.get_git_ref(f"heads/{default_branch}")
        base_sha = base_ref.object.sha

        # Create the new branch
        logger.info("Creating branch: %s", branch_name)
        self.repo.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base_sha,
        )

        # Parse and apply the patch as commits
        file_changes = self._parse_patch(patch)
        if file_changes:
            self._apply_changes(branch_name, file_changes, issue_number)
        else:
            logger.warning("No file changes could be parsed from the patch")

        # Create the pull request
        pr_title = f"Fix #{issue_number}: {issue_title}"
        pr_body = self._build_pr_body(issue_number, review_summary, patch)

        logger.info("Creating pull request: %s", pr_title)
        pr = self.repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=default_branch,
        )

        logger.info("Pull request #%d created: %s", pr.number, pr.html_url)

        return {
            "number": pr.number,
            "url": pr.html_url,
            "title": pr.title,
            "branch": branch_name,
        }

    def _parse_patch(self, patch: str) -> dict[str, str]:
        """Parse a unified diff patch into file path -> new content mapping.

        This is a simplified parser that extracts the intended file changes.
        For production use, a more robust diff parser would be needed.

        Args:
            patch: Unified diff string.

        Returns:
            Dictionary mapping file paths to their new content.
        """
        file_changes: dict[str, str] = {}
        current_file: str | None = None
        added_lines: list[str] = []

        for line in patch.split("\n"):
            if line.startswith("+++ b/"):
                # Save previous file if any
                if current_file and added_lines:
                    file_changes[current_file] = "\n".join(added_lines)
                    added_lines = []
                current_file = line[6:].strip()
            elif line.startswith("--- "):
                continue
            elif line.startswith("@@"):
                continue
            elif line.startswith("-"):
                continue
            elif line.startswith("+"):
                added_lines.append(line[1:])
            elif current_file is not None:
                # Context line (unchanged)
                added_lines.append(line[1:] if line.startswith(" ") else line)

        # Save last file
        if current_file and added_lines:
            file_changes[current_file] = "\n".join(added_lines)

        return file_changes

    def _apply_changes(
        self,
        branch_name: str,
        file_changes: dict[str, str],
        issue_number: int,
    ) -> None:
        """Apply file changes as a commit on the given branch.

        Args:
            branch_name: The branch to commit to.
            file_changes: Mapping of file paths to new content.
            issue_number: Issue number for the commit message.
        """
        for filepath, content in file_changes.items():
            commit_message = f"gitfix: update {filepath} for issue #{issue_number}"

            try:
                # Try to get existing file (update)
                existing = self.repo.get_contents(filepath, ref=branch_name)
                if isinstance(existing, list):
                    existing = existing[0]
                self.repo.update_file(
                    path=filepath,
                    message=commit_message,
                    content=content,
                    sha=existing.sha,
                    branch=branch_name,
                )
                logger.info("Updated file: %s", filepath)
            except GithubException:
                # File doesn't exist, create it
                self.repo.create_file(
                    path=filepath,
                    message=commit_message,
                    content=content,
                    branch=branch_name,
                )
                logger.info("Created file: %s", filepath)

    def _build_pr_body(
        self,
        issue_number: int,
        review_summary: str,
        patch: str,
    ) -> str:
        """Build the pull request description body.

        Args:
            issue_number: The issue being resolved.
            review_summary: AI code review summary.
            patch: The generated patch.

        Returns:
            Formatted PR body string.
        """
        return (
            f"## GitFix_AI - Automated Fix\n\n"
            f"Resolves #{issue_number}\n\n"
            f"### AI Code Review\n{review_summary}\n\n"
            f"### Generated Patch\n```diff\n{patch}\n```\n\n"
            f"---\n"
            f"*This pull request was automatically generated by GitFix_AI.*"
        )
