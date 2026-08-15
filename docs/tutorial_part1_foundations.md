# LeaseGPT Tutorial - Part 1: Foundations, Setup, and Database

Welcome to Part 1 of the LeaseGPT tutorial series! In this tutorial, we will build a full-stack, AI-powered web application from scratch. We're going to build **LeaseGPT** — a system that allows users to upload PDF or image copies of their leases, and then ask natural language questions about them through a ChatGPT-like interface.

This tutorial is designed specifically for **complete beginners** to AI engineering. We will explain every concept, every tool, and every line of code. If you have some basic programming experience but have never touched AI, Docker, or Cloud architectures before, you are in the right place!

---

## Chapter 0: What Are We Building? (The Big Picture)

Before we write any code, let's understand the core concepts and technologies we'll be using.

### What is a Large Language Model (LLM)?
Imagine a person who has read millions of books, articles, and websites, and has learned the patterns of human language so well that they can predict, word by word, what should logically come next in a sentence. That's essentially what a Large Language Model is. It's a massive mathematical equation (a neural network) that takes in text (your prompt) and predicts the most likely response based on the massive amounts of data it was trained on. 

It does not "think" or "know" facts like a human does; it generates text based on patterns. When you ask it a question, it uses probabilities to guess the right words to output.

### What is RAG (Retrieval-Augmented Generation)?
Why can't we just give a lease document to the LLM and ask it questions directly? 
1. **Memory Limits (Context Window):** LLMs have a limit on how much text they can process at once. A massive commercial lease might exceed this limit.
2. **Cost:** Even if it fits, sending massive documents to an LLM every time you ask a question costs a lot of money and computational power.
3. **Accuracy (Hallucinations):** LLMs sometimes make things up (hallucinate).

**RAG is the solution.**
Think of an LLM as a very smart person locked in a room without internet access. If you ask them a highly specific question about your personal lease, they won't know the answer and might guess (hallucinate).
Now, what if you give that person a librarian (the **Retriever**)? When you ask a question, the librarian quickly searches through your lease, finds the 3 most relevant pages, and hands them to the smart person. The smart person then reads those 3 pages and gives you an accurate answer.

That's RAG! We **retrieve** relevant information from our database and **augment** the LLM's prompt with that information so it can **generate** an accurate response.

### What is Hybrid RAG?
There are two main ways to search text:
1. **Keyword Search:** Looking for exact words (like finding the word "pet" in a document).
2. **Semantic Search:** Looking for meaning. If you search for "dogs allowed?", semantic search is smart enough to find the paragraph talking about "canines permitted on the premises," even if the exact words "dogs" or "allowed" aren't there.

**Hybrid RAG** combines both methods to give us the best of both worlds—pinpoint accuracy for exact terms, and contextual understanding for concepts.

### What is a Vector Embedding?
How does an AI understand "meaning"? By turning words into numbers. 
A vector embedding is a list of numbers (a vector) that represents the meaning of a piece of text. 

Imagine a 2D graph where the X-axis is "How much is this related to animals?" and the Y-axis is "How much is this related to homes?". 
The word "Dog" might be at `[0.9, 0.1]`. The word "Apartment" might be at `[0.1, 0.9]`. The phrase "Pet Rent" might be right in the middle at `[0.8, 0.8]`.
Because "Dog" and "Pet Rent" are close to each other on the graph, the computer knows their meanings are related. 

In this project, we use embeddings with **768 dimensions** (not just 2!). This allows the AI to capture incredibly complex nuances in meaning.

### What is an AI Agent? What is LangGraph?
An **AI Agent** is an LLM that has been given tools and a loop to think. Instead of just answering a question immediately, an agent can say: "To answer this, I first need to use my Search Tool. Let me do that... Okay, I got the results. Now let me analyze them... Okay, here is the final answer."

**LangGraph** is a Python library that helps us build these agents. It lets us define the agent's decision-making process as a flowchart (a graph) with nodes (steps) and edges (rules for moving to the next step).

### What is Ollama?
Usually, to use a powerful LLM, you have to pay companies like OpenAI (ChatGPT) or Anthropic (Claude) for every message. 
**Ollama** is a free, open-source tool that lets you run powerful LLMs directly on your own computer. It means everything stays private (your lease data never leaves your laptop) and it's completely free!

### High-Level System Architecture

Here is how all the pieces fit together:

```mermaid
graph TD
    %% User Flow
    User((User)) --> |Asks Question| Frontend[Frontend UI<br>Next.js / React]
    Frontend --> |API Request| Backend[Backend API<br>FastAPI / Python]
    
    %% AI Agent Flow
    Backend --> Agent[AI Agent<br>LangGraph]
    Agent <--> |Uses Tools| Retriever[Hybrid Retriever]
    Agent <--> |Generates Answer| LLM[Local LLM<br>Ollama]
    
    %% Database Flow
    Retriever <--> |Semantic & Keyword Search| DB[(Database<br>PostgreSQL + pgvector)]
    Backend <--> |Chat History| Redis[(Cache<br>Redis)]
    
    %% Data Ingestion Flow
    Upload[PDF Upload] --> S3[AWS S3<br>Storage]
    S3 --> Lambda[AWS Lambda<br>Text Extraction]
    Lambda --> |Extracted Text| Chunker[Text Chunker]
    Chunker --> |Creates Embeddings| Embed[Embedding Model<br>Ollama]
    Embed --> |Saves Vectors| DB
    
    classDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;
    classDef primary fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;
    classDef ai fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px;
    classDef db fill:#e8f5e9,stroke:#4caf50,stroke-width:2px;
    
    class Frontend,Backend primary;
    class Agent,LLM,Embed ai;
    class DB,Redis db;
    class DB db;
```

### The Tech Stack Explained
- **Next.js + TypeScript + TailwindCSS:** The frontend framework. Next.js helps us build fast React websites. TypeScript ensures our code doesn't have silly typos. TailwindCSS makes styling easy.
- **Python + FastAPI + WebSockets:** The backend. Python is the king of AI languages. FastAPI is a super-fast web framework for Python. WebSockets allow for real-time streaming of chat responses.
- **LangGraph & LlamaIndex:** AI libraries. LangGraph controls the agent's logic, and LlamaIndex helps us handle documents and RAG.
- **PostgreSQL (with pgvector):** A database to store both normal data (users, chat history) and mathematical vectors (the embeddings of the lease text).
- **Redis:** A super-fast temporary database (cache) to store active chat sessions.
- **AWS (S3, Lambda, Step Functions, Textract):** Cloud services we'll use later to process uploaded PDFs.
- **Docker & Kubernetes:** Tools to package our application so it runs identically on any computer.
- **Ollama:** Runs our local LLM (Llama 3) and our embedding model (nomic-embed-text) for free.

---

## Chapter 1: Prerequisites & Environment Setup

Since this tutorial is for Windows, we will set everything up perfectly for a Windows environment.

> [!IMPORTANT]
> Take your time with this chapter. 90% of beginner programming headaches come from a poorly configured environment!

### 1. Python 3.12
Python is the language we'll use for the backend.
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.12 (do not use 3.13 yet, as some AI libraries are slow to update).
3. **CRITICAL:** When running the installer, check the box that says **"Add Python to PATH"** at the bottom of the first screen.
4. Verify by opening Command Prompt (CMD) or PowerShell and typing: `python --version`

### 2. Node.js 20 LTS
Node.js lets us run JavaScript outside the browser, which is needed for our Next.js frontend.
1. Go to [nodejs.org](https://nodejs.org/)
2. Download the **20.x LTS** (Long Term Support) version.
3. Install with default settings.
4. Verify in terminal: `node --version`

### 3. Docker Desktop
Docker lets us run applications in isolated "containers". Think of a container as a tiny, lightweight, disposable virtual machine that has exactly what our app needs to run.
1. Go to [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Download and install Docker Desktop for Windows.
3. Ensure WSL 2 (Windows Subsystem for Linux) is enabled when prompted during installation. This makes Docker run incredibly fast on Windows.
4. Restart your computer if prompted.
5. Open Docker Desktop to make sure it's running.
6. Verify in terminal: `docker --version`

### 4. Git
Git tracks changes to our code (version control).
1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and install with default settings.
3. Verify in terminal: `git --version`

### 5. VS Code
The best code editor for this stack.
1. Go to [code.visualstudio.com](https://code.visualstudio.com/)
2. Download and install.
3. Open VS Code, click the "Extensions" icon on the left (or press Ctrl+Shift+X), and install these extensions:
   - **Python** (by Microsoft)
   - **ESLint** (by Microsoft)
   - **Tailwind CSS IntelliSense** (by Tailwind Labs)
   - **Docker** (by Microsoft)
   - **Prisma** (by Prisma - useful for database schemas)

### 6. Ollama
This is the magic tool that will run our AI models locally.
1. Go to [ollama.com/download](https://ollama.com/download)
2. Download for Windows and install.
3. Open a terminal and run `ollama --version` to verify.
4. Now, we need to download our models. In your terminal, run:
   ```bash
   ollama pull llama3.1:8b
   ```
   *This downloads the Llama 3.1 model (the brain that will answer questions). It's about 4.7GB, so it might take a while depending on your internet.*
5. Next, download the embedding model:
   ```bash
   ollama pull nomic-embed-text
   ```
   *This downloads a smaller model specifically designed to turn text into numbers (vector embeddings). It's about 274MB.*

### 7. AWS CLI
We will use Amazon Web Services later in the tutorial.
1. Download the AWS CLI MSI installer for Windows from [aws.amazon.com/cli](https://aws.amazon.com/cli/).
2. Run the installer.
3. We will configure this in a later chapter when we actually need it.

### 8. Kubernetes (kubectl and kind)
We will use these later for deploying our app.
For now, let's just install them.
1. Open PowerShell **as Administrator**.
2. If you don't have a package manager like `winget` or `choco`, the easiest way on Windows is via Docker Desktop.
   - Open Docker Desktop Settings (gear icon) -> Kubernetes -> Check "Enable Kubernetes" -> Apply & Restart.
   - This installs `kubectl` automatically!

---

## Chapter 2: Project Scaffolding

Now let's build the skeleton of our project. We are using a **monorepo** structure, meaning our frontend, backend, and infrastructure code will all live in one single Git repository.

Open your terminal and let's create the folders:

```bash
mkdir leasegpt
cd leasegpt
mkdir frontend backend infra docs
```

Here is what these folders are for:
- `frontend/`: Our Next.js React user interface.
- `backend/`: Our Python FastAPI server and AI Agent code.
- `infra/`: Docker and Kubernetes configuration files.
- `docs/`: Documentation (like this tutorial!).

Now, open this `leasegpt` folder in VS Code.

### Root Files

Let's create some files in the main `leasegpt` folder.

#### 1. `.gitignore`
This file tells Git which files it should NOT upload to the internet (like secret passwords or massive auto-generated folders).

Create a file named `.gitignore` in the root folder:

```text
# .gitignore

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
venv/
venv.bak/

# Node
node_modules/
npm-debug.log
yarn-error.log
yarn-debug.log
.pnpm-debug.log

# Next.js
.next/
out/

# Docker
.docker/

# OS Files
.DS_Store
Thumbs.db

# IDEs
.vscode/
.idea/

# Environment Variables - NEVER COMMIT SECRETS!
.env
.env.local
.env.*.local
```

#### 2. `Makefile`
A Makefile is a script that gives us short commands to run long, annoying terminal commands. Note: On Windows, you might need to install `make` (e.g., via `choco install make`), or you can just read the commands from this file and run them manually.

Create a file named `Makefile` in the root folder:

```makefile
# Makefile

.PHONY: dev-up dev-down logs backend-shell db-shell

# Start all Docker services in the background (-d means detached)
dev-up:
	docker-compose -f infra/docker/docker-compose.yml up -d

# Stop all Docker services
dev-down:
	docker-compose -f infra/docker/docker-compose.yml down

# View logs from all services
logs:
	docker-compose -f infra/docker/docker-compose.yml logs -f

# Open a terminal inside the running backend container
backend-shell:
	docker-compose -f infra/docker/docker-compose.yml exec backend bash

# Open a database connection in the terminal
db-shell:
	docker-compose -f infra/docker/docker-compose.yml exec postgres psql -U postgres -d leasegpt
```

#### 3. `.env.example`
We use `.env` files to store secret passwords and configuration on our local computer. We NEVER upload `.env` to Git. Instead, we upload `.env.example` so other developers know what variables they need to set.

Create `.env.example`:

```env
# .env.example

# --- Database Settings ---
# URL format: postgresql+asyncpg://username:password@host:port/database_name
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/leasegpt
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=leasegpt
# --- Redis Settings ---
REDIS_URL=redis://localhost:6379/0


# --- AI Models ---
# The URL where Ollama is running locally
OLLAMA_BASE_URL=http://localhost:11434
# The LLM we pulled earlier
LLM_MODEL=llama3.1:8b
# The embedding model we pulled earlier
EMBEDDING_MODEL=nomic-embed-text

# --- Backend API ---
# Secret key for JWT tokens (change in production!)
API_SECRET_KEY=super_secret_dev_key_123
ENVIRONMENT=development
```

> [!TIP]
> Copy `.env.example` and rename the copy to `.env`. This `.env` file is where your app will actually read its configuration from!

#### 4. `README.md`
Create a basic `README.md`:

```markdown
# LeaseGPT

An AI-powered application that allows users to ask questions about their lease documents using RAG (Retrieval-Augmented Generation).

## Tech Stack
- Frontend: Next.js, TailwindCSS
- Backend: FastAPI, LangGraph, LlamaIndex
- Database: PostgreSQL (with pgvector), Redis
- AI: Ollama (Local Llama 3 & nomic-embed-text)
```

Now, let's initialize Git:
Open your terminal in VS code (Ctrl+`) and type:
```bash
git init
git add .
git commit -m "Initial commit: Project scaffolding"
```

---

## Chapter 3: Database Layer (PostgreSQL + pgvector)

Our app needs a place to store data. We need to store structured data (like Users and Chat Sessions) and we need to store our vector embeddings.

### Setting up Docker Compose

Instead of installing PostgreSQL and Redis manually on Windows (which is messy), we will use Docker to run them in containers.

Create the folder path `infra/docker/` and then create `docker-compose.yml` inside it:

```yaml
# infra/docker/docker-compose.yml

version: '3.8'

# 'services' defines the different containers we want to run
services:
  
  # 1. Our PostgreSQL Database
  postgres:
    # We use a specific image that already has the pgvector extension installed!
    image: pgvector/pgvector:pg16
    container_name: leasegpt-postgres
    # These map to our .env variables
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: leasegpt
    # We map port 5432 inside the container to 5432 on our Windows machine
    ports:
      - "5432:5432"
    # Volumes save our data. If we don't do this, the database wipes clean every time we restart Docker!
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # A healthcheck ensures the database is fully booted before other services try to connect
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d leasegpt"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 2. Redis (Our fast in-memory cache)
  redis:
    image: redis:7-alpine
    container_name: leasegpt-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5



# We must declare the volumes we used above
volumes:
  postgres_data:
  redis_data:

```
**What just happened?** We wrote a recipe that tells Docker: "Hey, go download a PostgreSQL database (specifically one with the vector extension) and a Redis cache, set them up with these passwords, open these ports so my computer can talk to them, and make sure their data survives a restart."

Start it up by running this in your terminal:
```bash
docker-compose -f infra/docker/docker-compose.yml up -d
```
*(The `-d` means "detached" so it runs in the background and frees up your terminal).*

### Python Backend Setup

Now let's set up the Python side of our database.

In your terminal, navigate to the backend folder:
```bash
cd backend
```

Let's create our Python environment and configuration file.

#### Installing Poetry (Our Dependency Manager)

**Poetry** is a modern Python dependency manager used widely in industry. Think of it as a smarter version of `pip` — it manages your virtual environment, tracks exact dependency versions in a **lock file** (so your teammates get the *identical* setup), and provides a clean CLI for adding/removing packages.

Install Poetry on Windows by opening PowerShell and running:
```bash
# Install Poetry using the official installer script
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Add Poetry to your PATH (restart your terminal after this)
# Poetry installs to: %APPDATA%\Python\Scripts
# The installer will tell you the exact path — add it to your system PATH.

# Verify it works
poetry --version
# Should print something like: Poetry (version 1.8.x)
```

> [!TIP]
> **Why Poetry over plain pip?**
> - **Lock file** (`poetry.lock`): Pins every dependency to an *exact* version. If you install `fastapi>=0.110.0`, pip might install 0.110 today and 0.115 tomorrow. Poetry locks it to exactly 0.110.3 so every developer and server gets the same thing.
> - **Virtual env management**: Poetry creates and manages the virtual environment for you — no manual `python -m venv` steps.
> - **Dependency groups**: Cleanly separates production dependencies from dev/test tools.
> - **One command**: `poetry install` reads `pyproject.toml`, creates the virtual env, and installs everything.

Now, in the `backend` folder, create `pyproject.toml`:

```toml
# backend/pyproject.toml

# ============================================================
# Poetry Project Configuration
# ============================================================
# Poetry reads this file to manage your dependencies, virtual
# environment, and project metadata. It's the single source of
# truth for everything your Python project needs.
#
# Key commands:
#   poetry install          → Install all dependencies
#   poetry add <package>    → Add a new dependency
#   poetry remove <package> → Remove a dependency
#   poetry shell            → Activate the virtual environment
#   poetry run <command>    → Run a command inside the virtual env
# ============================================================

[tool.poetry]
name = "leasegpt-backend"
version = "0.1.0"
description = "FastAPI backend for LeaseGPT — AI-powered lease document Q&A"
authors = ["Your Name <you@example.com>"]
# readme = "README.md"  # Optional: uncomment if you create a README.md inside backend/
packages = [{include = "app"}]

[tool.poetry.dependencies]
python = "^3.11"

# --- Web Framework ---
fastapi = "^0.110.0"               # Our web framework — handles HTTP routes, WebSockets, auto-docs
uvicorn = {extras = ["standard"], version = "^0.29.0"}  # ASGI server that runs FastAPI (the "engine")
python-multipart = "^0.0.9"        # Required for file upload endpoints in FastAPI

# --- Data Validation & Configuration ---
pydantic = "^2.6.0"                # Validates data shapes/types (like a spell-checker for data)
pydantic-settings = "^2.2.0"       # Reads .env files into typed Python config objects

# --- Database (PostgreSQL) ---
sqlalchemy = {extras = ["asyncio"], version = "^2.0.29"}  # ORM — maps Python classes to database tables
asyncpg = "^0.29.0"                # Async PostgreSQL driver (lets SQLAlchemy talk to Postgres)
alembic = "^1.13.1"                # Database migrations — version control for your DB schema
pgvector = "^0.2.5"                # pgvector support — store/search vector embeddings in Postgres

# --- Cache (Redis) ---
redis = {extras = ["hiredis"], version = "^5.0.3"}  # Redis client with C-based parser for speed

# --- AI / LLM ---
llama-index-core = "^0.10.30"              # Core RAG framework — chunking, indexing, retrieval
llama-index-llms-ollama = "^0.1.3"         # LlamaIndex ↔ Ollama LLM integration
llama-index-embeddings-ollama = "^0.1.2"   # LlamaIndex ↔ Ollama embeddings integration
langgraph = "^0.0.30"                      # Agent orchestration — defines Q&A workflow as a graph
langchain-core = "^0.1.40"                 # LangChain core (required by LangGraph)

# --- Document Processing ---
PyMuPDF = "^1.24.1"                # PDF text extraction (also known as 'fitz')
boto3 = "^1.34.84"                 # AWS SDK — talks to S3, Textract, Step Functions
httpx = "^0.27.0"                  # Async HTTP client for calling Ollama API

# --- Reliability ---
tenacity = "^8.2.3"                # Retry logic with exponential backoff for LLM calls

# --- Dev / Test Dependencies ---
# These are NOT installed in production. Only for development and testing.
# Install with: poetry install --with dev
[tool.poetry.group.dev.dependencies]
pytest = "^8.1.0"                  # Python test framework
pytest-asyncio = "^0.23.0"        # Run async tests with pytest
ruff = "^0.3.0"                    # Lightning-fast Python linter + formatter
mypy = "^1.9.0"                    # Static type checker — catches bugs before runtime
ragas = "^0.1.5"                   # RAG evaluation framework — measures answer quality

# --- Build System ---
# This tells Poetry (and pip) how to build the project.
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

# --- Tool Configurations ---
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

> [!NOTE]
> **How Poetry's Caret (`^`) Operator Works:**
> The caret (`^`) operator sets a **minimum version** and automatically accepts non-breaking updates up to the next breaking version boundary:
> - **Post-1.0 packages (e.g., `^2.6.0`):** Minimum version `2.6.0`. Automatically allows minor and patch updates (`2.7.0`, `2.8.1`), but stops before major breaking version `3.0.0` (`>=2.6.0, <3.0.0`).
> - **Pre-1.0 packages (e.g., `^0.110.0`):** Minimum version `0.110.0`. In `0.x` releases, minor version bumps contain breaking changes. So `^0.110.0` automatically allows patch fixes (`0.110.1`, `0.110.2`), but stops before breaking version `0.111.0` (`>=0.110.0, <0.111.0`).

> [!TIP]
> **Where to run these commands:**
> Run `poetry install` and `poetry shell` directly inside the **`backend/` folder** (where `pyproject.toml` is located). You do **NOT** need to create or navigate into a `venv/` folder — Poetry manages the virtual environment automatically behind the scenes!

#### Installing Dependencies with Poetry

In the `backend` folder, run:
```bash
# Step 1: Generate the lock file
# This reads pyproject.toml, resolves compatible versions of ALL packages
# (and their sub-dependencies), and writes the exact versions to poetry.lock.
# You only need to run this once, or after changing pyproject.toml.
poetry lock

# Step 2: Install ALL dependencies (production + dev)
# Poetry will automatically:
#   - Create a virtual environment for this project
#   - Read poetry.lock (the exact pinned versions)
#   - Install them into the virtual environment
poetry install

# Step 3: Activate the virtual environment
# This drops you INTO the isolated Python environment
poetry shell
# You'll see the prompt change — you're now inside the virtual env!

# Verify it worked:
python -c "import fastapi; print(f'FastAPI {fastapi.__version__} installed!')"
```

> [!IMPORTANT]
> **The `poetry.lock` file:** After running `poetry lock`, Poetry creates a `poetry.lock` file. This file records the EXACT version of every package (and every sub-dependency) that was resolved. **Commit this file to git!** When your teammate clones the repo and runs `poetry install`, they get the identical environment — no surprises. If you change `pyproject.toml` (add/remove a package), run `poetry lock` again to regenerate it.

#### Common Poetry Commands You'll Use

```bash
# Add a new package (e.g., if you later need a new library)
poetry add some-package

# Add a dev-only package (won't be installed in production)
poetry add --group dev some-test-tool

# Remove a package
poetry remove some-package

# Update all packages to their latest compatible versions
poetry update

# Run a command inside the virtual env (without activating it)
poetry run pytest
poetry run uvicorn app.main:app --reload

# Show all installed packages
poetry show
```

> [!TIP]
> **Alternative: Using pip (simpler but no lock file)**
>
> If you prefer not to install Poetry, you can use plain pip instead. Poetry's `pyproject.toml` format is not directly readable by pip, but you can export it:
> ```bash
> # Option A: Export to requirements.txt, then use pip
> poetry export -f requirements.txt --output requirements.txt
> pip install -r requirements.txt
>
> # Option B: Install directly (Poetry's build backend supports this)
> pip install .
> ```
> The trade-off: pip won't give you a lock file, so dependency versions may drift between machines.

### Application Configuration

Create the folders `app/db` and `app/models` inside `backend/`. 
Make sure every folder has an empty file called `__init__.py` in it so Python recognizes them as modules.

Create `backend/app/config.py`:

```python
# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# BaseSettings automatically reads from our .env file!
class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "LeaseGPT API"
    ENVIRONMENT: str = "development"
    API_SECRET_KEY: str = "change_me_in_prod"

    # Database Settings
    DATABASE_URL: str
    REDIS_URL: str

    # AI Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3.1:8b"
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # We define the dimension of our vector based on the model we use.
    # nomic-embed-text outputs a list of 768 numbers.
    VECTOR_DIMENSION: int = 768

    # This tells Pydantic to look for a file named .env in the parent directory
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

# Create a global instance of settings to use throughout our app
settings = Settings()
```
**What just happened?** We created a Configuration class. Pydantic looks at our `.env` file, grabs the values, ensures they are the right type (e.g. `VECTOR_DIMENSION` must be an integer), and makes them available securely to our Python code.

### Database Connection

Create `backend/app/db/session.py`:

```python
# backend/app/db/session.py

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# 1. Create the Engine
# The engine manages the connection pool to the database.
# We use create_async_engine because we want our server to be able to handle 
# thousands of requests simultaneously without waiting for the database to respond.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False, # Set to True to see all SQL queries printed in the terminal
    future=True
)

# 2. Create the Session Factory
# A session is a single "conversation" with the database.
# async_sessionmaker generates new sessions for us when we need them.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False # Prevents SQLAlchemy from wiping our variables after saving to DB
)

# 3. Dependency Injection Function
# We will use this function in FastAPI routes to get a database connection.
# The 'yield' keyword makes this a generator. It opens the connection, gives it to the route,
# and then automatically closes it when the route is finished.
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```
**What just happened?** We configured SQLAlchemy to connect to our PostgreSQL database asynchronously. Think of the `engine` as the telephone line to the database, and the `session` as an active phone call.

### Defining our Database Tables (Models)

Instead of writing raw SQL code (like `CREATE TABLE users...`), we write Python classes. SQLAlchemy translates these classes into SQL for us. This is called an ORM (Object Relational Mapper).

Create a base file for our models: `backend/app/models/base.py`:
```python
# backend/app/models/base.py

from sqlalchemy.orm import declarative_base

# All our future database models will inherit from this Base class
Base = declarative_base()
```

Now let's define the tables for our Leases. Create `backend/app/models/lease.py`:

```python
# backend/app/models/lease.py

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.models.base import Base
from app.config import settings

class LeaseDocument(Base):
    """
    Represents an uploaded lease PDF in our database.
    """
    __tablename__ = "lease_documents" # The actual name of the table in Postgres

    # We use UUIDs instead of standard 1,2,3 IDs for better security
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    s3_url = Column(String, nullable=True) # Where the physical file is stored in AWS
    status = Column(String, default="processing") # "processing", "completed", "failed"
    
    # Store extra flexible data (like page count, file size) in a JSON column
    metadata_ = Column("metadata", JSONB, default={}) 
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Establish a relationship with the chunks (One Lease has Many Chunks)
    chunks = relationship("LeaseChunk", back_populates="document", cascade="all, delete-orphan")


class LeaseChunk(Base):
    """
    When we process a 50-page lease, we break it into small "chunks" (e.g. 500 words each).
    We turn each chunk into a Vector Embedding.
    """
    __tablename__ = "lease_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link back to the parent LeaseDocument
    document_id = Column(UUID(as_uuid=True), ForeignKey("lease_documents.id"), nullable=False)
    
    # The actual text of this paragraph/chunk
    text_content = Column(String, nullable=False)
    
    # THE MAGIC HAPPENS HERE: This column stores our 768-dimension vector embedding!
    embedding = Column(Vector(settings.VECTOR_DIMENSION), nullable=False)
    
    # Extra data like {"page_number": 4, "section_title": "Pets"}
    chunk_metadata = Column(JSONB, default={})

    # Link back to the parent Document
    document = relationship("LeaseDocument", back_populates="chunks")
```
**What just happened?** We created two tables. `LeaseDocument` tracks the overall uploaded file. Because an LLM can't process an entire 50-page lease at once, we break the lease into smaller paragraphs called `LeaseChunk`s. We use `pgvector`'s `Vector` column to store the mathematical representation of that paragraph so we can search it semantically later.

### Database Migrations with Alembic

We have Python classes, but our PostgreSQL database doesn't know about them yet! We need to push these changes to the database. We use **Alembic** to generate migration scripts.

> [!TIP]
> **Reminder:** All Python commands (`alembic`, `pytest`, `uvicorn`, etc.) are installed inside Poetry's virtual environment, not globally on your computer. You must either:
> - **Option A:** Activate the shell first with `poetry shell`, then run commands normally (e.g., `alembic init alembic`)
> - **Option B:** Prefix every command with `poetry run` (e.g., `poetry run alembic init alembic`)
>
> The examples below use `poetry run` so they work regardless of whether your shell is activated.

In your `backend` folder, run:
```bash
poetry run alembic init alembic
```
This creates an `alembic` folder and an `alembic.ini` file.

Open `backend/alembic.ini` and find the `sqlalchemy.url` line. Change it to this (or comment it out, since we will set it in python):
```ini
# backend/alembic.ini (around line 58)
# We comment this out because we want to use our settings.DATABASE_URL from config.py
# sqlalchemy.url = driver://user:pass@localhost/dbname
```

Now open `backend/alembic/env.py` and modify it heavily to look like this. This connects Alembic to our asynchronous SQLAlchemy setup:

```python
# backend/alembic/env.py

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import our settings and base models
from app.config import settings
from app.models.base import Base
# IMPORTANT: You MUST import your models here so Alembic can see them!
import app.models.lease 

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic where our metadata is
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    # This is required for pgvector to work with Alembic!
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Now, let's create our first migration! In the terminal (ensure your Docker database is running):
```bash
# This creates a python script with the SQL commands needed to build our tables
poetry run alembic revision --autogenerate -m "Initial tables"

> [!IMPORTANT]
> **Check your generated migration script:** 
> Open the newly created file inside `backend/alembic/versions/` and make sure it includes:
> 1. `import pgvector.sqlalchemy` at the top of the file.
> 2. `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` at the beginning of the `upgrade()` function (so PostgreSQL enables vector search).

# This actually runs the script against the database
poetry run alembic upgrade head
```

> [!SUCCESS]
> Congratulations! You have successfully configured a robust, asynchronous, vector-ready database layer. 

In **Part 2**, we will build out the FastAPI server, create our API endpoints, and begin integrating the LlamaIndex RAG pipeline to actually chunk text and save vectors into this database!
