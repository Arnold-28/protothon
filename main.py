"""GitFix_AI - Main orchestrator that runs the full pipeline.

Usage:
    # Process a specific issue:
    python main.py --issue 42

    # Start the webhook server:
    python main.py --server

    # List open issues:
    python main.py --list-issues
"""

import argparse
import logging
import sys

from config import Config
from agents.issue_interpreter import IssueInterpreter
from agents.patch_generator import PatchGenerator
from agents.reviewer import CodeReviewer
from rag.vector_store import VectorStore
from rag.retriever import CodeRetriever
from github_service.issue_fetcher import IssueFetcher
from github_service.pr_creator import PRCreator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline(issue_number: int) -> dict[str, str]:
    """Run the full GitFix_AI pipeline for a given issue.

    Steps:
    1. Fetch the GitHub issue.
    2. Interpret the issue using the LLM.
    3. Clone the repository and build the code index.
    4. Retrieve relevant code context using RAG.
    5. Generate a code patch using the LLM.
    6. Review the patch using the AI code reviewer.
    7. Create a pull request with the patch.

    Args:
        issue_number: The GitHub issue number to process.

    Returns:
        Dictionary with pipeline results including the PR URL.
    """
    logger.info("=" * 60)
    logger.info("GitFix_AI Pipeline - Processing Issue #%d", issue_number)
    logger.info("=" * 60)

    # Step 1: Fetch the issue
    logger.info("Step 1/7: Fetching issue #%d...", issue_number)
    fetcher = IssueFetcher()
    issue = fetcher.get_issue(issue_number)
    issue_title = str(issue["title"])
    issue_body = str(issue["body"])

    # Step 2: Interpret the issue
    logger.info("Step 2/7: Interpreting issue...")
    interpreter = IssueInterpreter()
    analysis = interpreter.interpret(issue_title, issue_body)
    logger.info("Issue type: %s", analysis.get("issue_type", "unknown"))
    logger.info("Summary: %s", analysis.get("summary", "N/A"))

    # Step 3: Clone and index the repository
    logger.info("Step 3/7: Cloning and indexing repository...")
    repo_path = fetcher.clone_repository()
    vector_store = VectorStore()
    vector_store.build_index(repo_path)

    # Step 4: Retrieve relevant code context
    logger.info("Step 4/7: Retrieving relevant code context...")
    retriever = CodeRetriever(vector_store)

    # Use the search queries from the issue analysis
    search_query = analysis.get("search_queries", analysis.get("summary", issue_title))
    relevant_docs = retriever.retrieve_context(search_query, k=5)
    code_context = retriever.format_context(relevant_docs)

    # Step 5: Generate the patch
    logger.info("Step 5/7: Generating code patch...")
    patch_gen = PatchGenerator()
    patch_result = patch_gen.generate_patch(analysis, code_context, Config.REPO_NAME)
    patch = patch_result["patch"]
    logger.info("Files to modify: %s", patch_result.get("files_modified", "none"))

    # Step 6: Review the patch
    logger.info("Step 6/7: Reviewing patch...")
    reviewer = CodeReviewer()
    review = reviewer.review_patch(patch, analysis, code_context)
    logger.info("Review verdict: %s (score: %s)", review.get("verdict"), review.get("score"))

    # Step 7: Create the pull request
    logger.info("Step 7/7: Creating pull request...")
    pr_creator = PRCreator()
    pr_result = pr_creator.create_pull_request(
        issue_number=issue_number,
        patch=patch,
        issue_title=issue_title,
        review_summary=review.get("raw_review", ""),
    )

    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info("PR #%s: %s", pr_result["number"], pr_result["url"])
    logger.info("=" * 60)

    return {
        "issue_number": str(issue_number),
        "pr_number": str(pr_result["number"]),
        "pr_url": str(pr_result["url"]),
        "review_verdict": review.get("verdict", ""),
        "review_score": review.get("score", ""),
    }


def list_open_issues() -> None:
    """List open issues in the configured repository."""
    fetcher = IssueFetcher()
    issues = fetcher.get_open_issues()

    if not issues:
        logger.info("No open issues found in %s", Config.REPO_NAME)
        return

    logger.info("Open issues in %s:", Config.REPO_NAME)
    for issue in issues:
        labels = ", ".join(issue.get("labels", []))
        label_str = f" [{labels}]" if labels else ""
        logger.info("  #%s: %s%s", issue["number"], issue["title"], label_str)


def main() -> None:
    """Main entry point for GitFix_AI."""
    parser = argparse.ArgumentParser(
        description="GitFix_AI - AI-powered GitHub issue resolver",
    )
    parser.add_argument(
        "--issue", "-i",
        type=int,
        help="GitHub issue number to process",
    )
    parser.add_argument(
        "--server", "-s",
        action="store_true",
        help="Start the webhook server",
    )
    parser.add_argument(
        "--list-issues", "-l",
        action="store_true",
        help="List open issues in the repository",
    )

    args = parser.parse_args()

    # Validate configuration
    errors = Config.validate()
    if errors:
        for error in errors:
            logger.error("Configuration error: %s", error)
        logger.error("Please check your .env file. See .env.example for reference.")
        sys.exit(1)

    if args.server:
        from api.webhook_server import start_server
        start_server()
    elif args.issue:
        result = run_pipeline(args.issue)
        print(f"\nPull Request created: {result['pr_url']}")
    elif args.list_issues:
        list_open_issues()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
