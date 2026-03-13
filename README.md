# GitFix_AI

An intelligent development agent that transforms GitHub issues into pull requests by understanding repository context, generating code patches, and performing automated AI code reviews.

## Architecture

GitFix_AI implements a **Hybrid RAG + LLM + GitHub Automation** pipeline:

```
Issue Creation
      ↓
Issue Interpreter (LLM)
      ↓
Codebase Indexing (Embeddings)
      ↓
Context Retrieval (RAG Search)
      ↓
Patch Generation (LLM)
      ↓
Pull Request Creation
      ↓
AI Automated Code Review
```

### System Components

| Component | Purpose |
|-----------|---------|
| **Issue Interpreter** | LLM-powered analysis of GitHub issues |
| **Codebase Indexer** | Embeds repository code into vectors |
| **Context Retriever** | RAG-based semantic search for relevant code |
| **Patch Generator** | LLM-generated unified diff patches |
| **PR Creator** | Automated GitHub Pull Request creation |
| **Code Reviewer** | AI-powered automated code review |
| **Webhook Server** | FastAPI server for GitHub event automation |

## Tech Stack

- **Python 3.10+**
- **OpenAI API** (GPT-4 / GPT-4o) — Issue interpretation, patch generation, code review
- **LangChain** — RAG orchestration and embeddings
- **FAISS** — Vector database for semantic code search
- **PyGithub** — GitHub API integration
- **FastAPI + Uvicorn** — Webhook server
- **GitPython** — Repository cloning
- **python-dotenv** — Environment configuration

## Project Structure

```
gitfix_ai/
├── agents/
│   ├── __init__.py
│   ├── issue_interpreter.py   # LLM issue analysis
│   ├── patch_generator.py     # LLM code patch generation
│   └── reviewer.py            # AI code review
├── rag/
│   ├── __init__.py
│   ├── embedder.py            # Code → embeddings
│   ├── vector_store.py        # FAISS vector storage
│   └── retriever.py           # Semantic code search
├── github_service/
│   ├── __init__.py
│   ├── issue_fetcher.py       # Read GitHub issues
│   └── pr_creator.py          # Create Pull Requests
├── api/
│   ├── __init__.py
│   └── webhook_server.py      # FastAPI webhook handler
├── main.py                    # Pipeline orchestrator
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── .gitignore
```

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Arnold-28/protothon.git
cd protothon
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `GITHUB_TOKEN` | Yes | GitHub Personal Access Token (needs `repo` scope) |
| `REPO_NAME` | Yes | Target repository in `owner/repo` format |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4o`) |
| `WEBHOOK_SECRET` | No | GitHub webhook secret for signature verification |
| `SERVER_PORT` | No | Webhook server port (default: `8000`) |

## Usage

### Process a Specific Issue

```bash
python main.py --issue 42
```

This runs the full pipeline:
1. Fetches issue #42 from GitHub
2. Interprets the issue using GPT-4o
3. Clones and indexes the repository codebase
4. Retrieves relevant code context via RAG
5. Generates a code patch
6. Reviews the patch with AI
7. Creates a Pull Request

### List Open Issues

```bash
python main.py --list-issues
```

### Start the Webhook Server

```bash
python main.py --server
```

The server listens on port 8000 (configurable) for GitHub webhook events. When a new issue is opened, the pipeline runs automatically.

#### Setting Up GitHub Webhooks

1. Go to your repository → **Settings** → **Webhooks** → **Add webhook**
2. Set **Payload URL** to your server's public URL + `/webhook` (e.g., `https://your-server.com/webhook`)
3. Set **Content type** to `application/json`
4. Set **Secret** to match your `WEBHOOK_SECRET` in `.env`
5. Select **Let me select individual events** → check **Issues**
6. Click **Add webhook**

## How It Works

### 1. Issue Interpretation
The **Issue Interpreter** agent uses GPT-4o to analyze the issue title and description, producing:
- A concise summary
- Issue type classification (bug, feature, refactor, etc.)
- Affected areas of the codebase
- Suggested approach for resolution
- Search queries for finding relevant code

### 2. Codebase Indexing (RAG)
The **Code Embedder** loads all source files from the repository, splits them into chunks, and generates vector embeddings using OpenAI's `text-embedding-3-small` model. These are stored in a **FAISS** vector database for fast similarity search.

### 3. Context Retrieval
The **Code Retriever** uses the search queries from the issue interpretation to find the most relevant code chunks via semantic similarity search against the FAISS index.

### 4. Patch Generation
The **Patch Generator** agent takes the issue analysis and relevant code context, then uses GPT-4o to generate a unified diff patch that resolves the issue while following the repository's existing code style.

### 5. AI Code Review
The **Code Reviewer** agent evaluates the generated patch for correctness, code quality, security, performance, and edge case handling, providing a verdict (APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION) and a quality score.

### 6. Pull Request Creation
The **PR Creator** creates a new branch, commits the changes from the patch, and opens a pull request that references the original issue and includes the AI code review.

## License

MIT
