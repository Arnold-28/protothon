"""Webhook Server - FastAPI server that listens for GitHub webhook events."""

import hashlib
import hmac
import logging

from fastapi import FastAPI, Request, HTTPException
import uvicorn

from config import Config

logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitFix_AI Webhook Server",
    description="Receives GitHub webhook events and triggers the GitFix_AI pipeline.",
    version="1.0.0",
)


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the GitHub webhook signature.

    Args:
        payload: Raw request body bytes.
        signature: The X-Hub-Signature-256 header value.
        secret: The webhook secret.

    Returns:
        True if the signature is valid.
    """
    if not secret:
        return True  # Skip verification if no secret is configured

    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.get("/")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "GitFix_AI Webhook Server"}


@app.post("/webhook")
async def handle_webhook(request: Request) -> dict[str, str]:
    """Handle incoming GitHub webhook events.

    Listens for 'issues' events with 'opened' action and triggers
    the GitFix_AI pipeline for the new issue.

    Args:
        request: The incoming FastAPI request.

    Returns:
        Response indicating the action taken.
    """
    # Verify webhook signature
    payload = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    if Config.WEBHOOK_SECRET and not verify_signature(payload, signature, Config.WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse the event
    event_type = request.headers.get("X-GitHub-Event", "")
    data = await request.json()

    logger.info("Received webhook event: %s", event_type)

    if event_type == "issues" and data.get("action") == "opened":
        issue = data["issue"]
        issue_number = issue["number"]
        issue_title = issue["title"]

        logger.info("New issue opened: #%d - %s", issue_number, issue_title)

        # Import here to avoid circular imports at module level
        from main import run_pipeline

        try:
            result = run_pipeline(issue_number)
            return {
                "status": "success",
                "message": f"Pipeline triggered for issue #{issue_number}",
                "pr_url": result.get("pr_url", ""),
            }
        except Exception as exc:
            logger.error("Pipeline failed for issue #%d: %s", issue_number, exc)
            return {
                "status": "error",
                "message": f"Pipeline failed: {exc}",
            }

    if event_type == "ping":
        return {"status": "ok", "message": "Pong! Webhook configured successfully."}

    return {"status": "ignored", "message": f"Event '{event_type}' not handled"}


def start_server() -> None:
    """Start the FastAPI webhook server."""
    logger.info("Starting GitFix_AI webhook server on port %d", Config.SERVER_PORT)
    uvicorn.run(
        "api.webhook_server:app",
        host="0.0.0.0",
        port=Config.SERVER_PORT,
        reload=False,
    )
