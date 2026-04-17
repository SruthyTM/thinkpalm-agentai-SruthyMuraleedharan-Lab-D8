# GitHub PR Review & Documentation Assistant (Pro Edition)

An elite, multi-agent AI pipeline designed for automated code auditing, security scanning, and technical documentation generation.



## 🎯 Overview

This system leverages **LangGraph** to orchestrate a sophisticated multi-agent team. It automates the "Shift Left" security philosophy by analyzing code early in the development lifecycle, identifying vulnerabilities before they reach production, and ensuring every module is documented to a senior-engineering standard.

## 🏗️ Architecture & Agents

The pipeline follows a Directed Acyclic Graph (DAG) pattern, ensuring a rigorous, step-by-step review process:

1.  **🔍 Critic Agent (The Auditor)**: Performs deep static analysis using AST tools. It scans for security vulnerabilities (SQLi, Shell injection), computes Cyclomatic Complexity (McCabe), and evaluates PEP 8 compliance.
2.  **✍️ Scribe Agent (The Writer)**: Analyzes the codebase structure to generate professional Markdown documentation skeletons, including class/function signatures and high-level summaries.
3.  **🏷️ Labeler Agent (The Gatekeeper)**: Evaluates the combined findings from the previous agents to issue a final governance verdict: **"Safe"** or **"Needs Work."**

## 🌟 Key Technical Features

-   **🧠 Persistent Memory**: Utilizes an SQLite checkpointer to maintain thread state across multiple interactions.
-   **🛠️ Sophisticated Tooling**: Custom Python-based tools for AST analysis, regex security scanning, and dependency auditing.
-   **💎 Modern Dashboard**: A high-performance Web UI for real-time interaction with the agent pipeline.
-   **🐳 Containerized**: Fully orchestrated using Docker and Docker Compose for easy deployment.

## 🛠️ Tech Stack

-   **Language**: Python 3.10+
-   **Orchestration**: LangGraph, LangChain
-   **API Framework**: FastAPI
-   **Models**: GPT-4o / Claude 3.5 (Configurable via Environment)
-   **Database**: SQLite (built-in checkpointer)
-   **Deployment**: Docker, Nginx, Uvicorn

## 🚀 Getting Started

### 1. Configuration
Create a `.env` file from the provided example:
```bash
cp .env.example .env
```
Add your `OPENAI_API_KEY` or preferred provider credentials.

### 2. Fast Launch (Docker)
The entire stack (Frontend + Backend) can be launched with a single command:
```bash
docker-compose up --build
```
- **Dashboard**: `http://localhost:8080`
- **Backend API**: `http://localhost:8000`

### 3. Manual Launch
**Backend**:
```bash
pip install -r requirements.txt
python -m src.main
```
**Frontend**: Serve `frontend/index.html` via any HTTP server (e.g., `python -m http.server 8080`).

## 📁 Repository Structure

-   `/src`: All agentic pipeline source code (Agents, Graph, Tools).
-   `/frontend`: Premium dashboard files.
-   `Dockerfile` & `docker-compose.yml`: Containerization settings.

**POST** `/review`
```json
{
  "code": "def example(): pass",
  "filename": "auth.py"
}
```

---
*Developed for the Multi-Agent Pipeline Mini-Project Track.*
