"""Issue Fetcher - Reads GitHub issues using the PyGithub library."""

import logging
import os
import shutil
from pathlib import Path

from github import Github
from github.Issue import Issue
from github.Repository import Repository
from git import Repo as GitRepo

from config import Config

logger = logging.getLogger(__name__)


class IssueFetcher:
    """Fetches GitHub issues and clones repositories for indexing."""

    def __init__(self) -> None:
        self.github = Github(Config.GITHUB_TOKEN)
        self.repo: Repository = self.github.get_repo(Config.REPO_NAME)

    def get_issue(self, issue_number: int) -> dict[str, str | int | list[str]]:
        """Fetch a single GitHub issue by number.

        Args:
            issue_number: The issue number to fetch.

        Returns:
            Dictionary with issue details: number, title, body, labels, state, author.
        """
        issue: Issue = self.repo.get_issue(number=issue_number)
        logger.info("Fetched issue #%d: %s", issue_number, issue.title)

        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "labels": [label.name for label in issue.labels],
            "state": issue.state,
            "author": issue.user.login if issue.user else "unknown",
        }

    def get_open_issues(self, limit: int = 10) -> list[dict[str, str | int | list[str]]]:
        """Fetch open issues from the repository.

        Args:
            limit: Maximum number of issues to fetch.

        Returns:
            List of issue dictionaries.
        """
        issues = self.repo.get_issues(state="open")
        result = []

        for issue in issues[:limit]:
            # Skip pull requests (GitHub API returns PRs as issues too)
            if issue.pull_request is not None:
                continue
            result.append({
                "number": issue.number,
                "title": issue.title,
                "body": issue.body or "",
                "labels": [label.name for label in issue.labels],
                "state": issue.state,
                "author": issue.user.login if issue.user else "unknown",
            })

        logger.info("Fetched %d open issues", len(result))
        return result

    def clone_repository(self, target_dir: str | None = None) -> str:
        """Clone the repository locally for code indexing.

        Args:
            target_dir: Directory to clone into. Defaults to Config.CLONE_DIR/<repo_name>.

        Returns:
            Path to the cloned repository.
        """
        repo_name = Config.REPO_NAME.replace("/", "_")
        clone_path = target_dir or os.path.join(Config.CLONE_DIR, repo_name)

        # Remove existing clone if present
        if Path(clone_path).exists():
            shutil.rmtree(clone_path)
            logger.info("Removed existing clone at %s", clone_path)

        os.makedirs(os.path.dirname(clone_path), exist_ok=True)

        clone_url = self.repo.clone_url
        logger.info("Cloning %s to %s...", Config.REPO_NAME, clone_path)

        GitRepo.clone_from(clone_url, clone_path)
        logger.info("Repository cloned successfully")

        return clone_path
