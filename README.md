# Multi-Agent HR Assistant

A sophisticated multi-agent AI system designed to handle HR operations through intelligent agents that specialize in different domains. Built with LangChain, LangGraph, FastAPI, and powered by Groq's LLM models.

## Overview

The Multi-Agent HR Assistant is an intelligent system that helps HR departments manage employee queries, leave requests, policy documentation, and support tickets. The system uses specialized AI agents that work together to understand user intent and provide appropriate responses.

### Key Components

- **FastAPI Backend** - RESTful API with real-time WebSocket support
- **Multi-Agent System** - Specialized agents for different HR tasks
- **Vector Store** - Chroma for policy document retrieval
- **Cache Layer** - Redis for state management and real-time events
- **Next.js Frontend** - Modern React-based UI
- **LLM Provider** - Groq integration for high-speed AI inference

---

## Architecture

### High-Level System Architecture

![High-Level System Architecture](./src/multi-agent-hr-assistant/pics/Complete%20System%20Architecture.png)

### Multi-Agent Workflow

![Multi-Agent Workflow Architecture](./src/multi-agent-hr-assistant/pics/Complete%20Agent%20Architecture.png)

---

## Agent Systems

### 1. **Supervisor Agent**

**Purpose**: Route and orchestrate user requests to appropriate specialized agents.

**Responsibilities**:

- Parse and understand user intent from natural language queries
- Decompose complex requests into specific tasks
- Route tasks to Clerk or Librarian agents based on intent
- Synthesize final responses from agent outputs
- Handle general chat and clarification requests

**Supported Intents**:

- `Policy_Query` → Librarian Agent
- `Leave_Request` → Clerk Agent
- `Complaint_Filing` → Clerk Agent
- `Clarification` → Supervisor Agent
- `General_Chat` → Supervisor Agent

**Flow**:

```
Query → Intent Classification → Task Decomposition →
Agent Selection → Execute Agents → Response Synthesis
```

![Supervisor Agent Graph](./src/multi-agent-hr-assistant/pics/supervisor_agent_graph.png)

---

### 2. **Clerk Agent**

**Purpose**: Handle HR transactions including leave management and ticket creation.

**Responsibilities**:

- Get user leave balance
- Process leave requests
- Create support tickets
- File complaints
- Provide general HR information

**Supported Actions**:

- `get_balance` - Fetch current leave balance
- `ticket_creation` - Create new support tickets
- `general_information` - Provide HR info

**Capabilities**:

- Real-time leave balance queries via Supabase
- Ticket creation with classification (complaint, help, leave)
- User verification and authorization checks
- Human-in-the-loop intervention for complex cases

**Flow**:

```
Task Classification → Validation → Execute Tool →
Response Generation → Human Approval (if needed) → Final Response
```

![Clerk Agent Graph](./src/multi-agent-hr-assistant/pics/clerk_agent_graph.png)

---

### 3. **Librarian Agent**

**Purpose**: Manage HR policy documentation and retrieval.

**Responsibilities**:

- Retrieve policies based on user queries
- Upload new policy documents
- Update existing policies
- Delete outdated policies
- Search policy database

**Supported Actions**:

- `retrieve_policy` - Search and retrieve relevant policies
- `upload_policy` - Add new policy documents
- `update_policy` - Modify existing policies
- `delete_policy` - Remove outdated policies

**Capabilities**:

- Vector similarity search for policy retrieval
- Document embedding with Chroma
- Policy versioning support
- Admin-only policy management operations

**Flow**:

```
Query → Embedding → Vector Search → Policy Retrieval →
Context Augmentation → Response Generation
```

![Librarian Agent Graph](./src/multi-agent-hr-assistant/pics/librarian_agent_graph.png)

---

## Features

### Core Features

- **Multi-Agent Orchestration** - LangGraph-based workflow system
- **Real-time Communication** - WebSocket support for live updates
- **Vector Search** - Semantic search for policy retrieval
- **Chat History** - Persistent conversation tracking
- **User Authentication** - Supabase integration
- **File Upload Support** - Document ingestion for policies
- **Admin Dashboard** - Policy management interface

### Technical Features

- **Async Processing** - Non-blocking request handling
- **Redis Caching** - State and event management
- **Error Handling** - Comprehensive error recovery
- **Logging** - Detailed request/response logging
- **Docker Support** - Full containerization
- **API Documentation** - Interactive Swagger UI

---

## Prerequisites

### System Requirements

- **OS**: Windows, macOS, or Linux
- **Python**: 3.9 or higher
- **Node.js**: 16 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 1.29+ (for multi-service setup)

### Required Services

- Groq API Account (for LLM access)
- Supabase Project (for database/authentication)
- Redis Instance (local or Docker)

---

## Installation

### Option 1: Local Development Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multi-agent-hr-assistant.git
cd multi-agent-hr-assistant
```

#### 2. Create Environment File

```bash
cp .env.example .env.local
```

#### 3. Configure Environment Variables

Edit `.env.local` with your actual values:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# Groq LLM Configuration
GROQ_API_KEY=your-groq-api-key

# Clerk Configuration (for mocking)
MOCK_API_KEY_CLERK=your-clerk-mock-key

# Redis Configuration (if running locally)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Frontend Configuration
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

#### 4. Install Python Dependencies

```bash
# Install backend dependencies
pip install -e .

# Install development tools (optional)
pip install -e ".[dev]"

# Install test dependencies
pip install -r tests/requirements-test.txt
```

#### 5. Install UI Dependencies

```bash
cd src/multi-agent-hr-assistant/ui
npm install
cd ../../../
```

### Option 2: Docker Setup (Recommended)

```bash
# Setup environment
cp .env.example .env.local
# Edit .env.local with your configuration

# Build images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## Quick Start

### Local Development

**Terminal 1 - Backend API**

```bash
# Install dependencies (first time only)
make install

# Run development server with hot-reload
make dev
```

Backend will be available at: http://localhost:8000

**Terminal 2 - Frontend UI**

```bash
cd src/multi-agent-hr-assistant/ui

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:3000

**Terminal 3 - Redis (if not running)**

```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or ensure your Redis instance is running
redis-cli ping  # Should return PONG
```

### Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Docker Deployment

```bash
# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

Services will be available at:

- **Backend**: http://localhost:8000
- **Redis**: localhost:6379

---

## Configuration

### Environment Variables

#### Backend Configuration

```env
# API Settings
BACKEND_PORT=8000
BACKEND_HOST=0.0.0.0

# LLM Configuration
GROQ_API_KEY=xxx                    # Groq API key
GROQ_MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct

# Database
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx                    # Anon key
SUPABASE_SERVICE_KEY=xxx            # Service role key

# Cache & Events
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Authentication
MOCK_API_KEY_CLERK=xxx              # Mock clerk API key
DATABASE_URL=postgresql://user:pass@localhost:5432/hrdb  # Optional
```

#### Frontend Configuration

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
NODE_ENV=development
```

### Configuration Files

- **`pyproject.toml`** - Python dependencies and project metadata
- **`docker-compose.yml`** - Container orchestration
- **`Dockerfile`** - Backend container definition
- **`.env.example`** - Environment variables template
- **`Makefile`** - Development commands

---

## Running the Project

### Make Commands (Recommended)

```bash
# Installation
make install              # Install all dependencies
make install-backend      # Backend only
make install-ui           # Frontend only

# Development
make dev                  # Backend (with hot-reload)
make dev-ui               # Frontend
make dev-all              # Instructions for both

# Testing
make test                 # Run all tests
make test-cov             # With coverage report
make lint                 # Code quality checks
make format               # Auto-format code
make format-check         # Check formatting

# Docker
make docker-build         # Build Docker images
make docker-up            # Start containers
make docker-down          # Stop containers
make docker-logs          # View logs

# Cleanup
make clean                # Remove caches and temp files
```

### Manual Commands

#### Backend

```bash
# Development
cd src/multi-agent-hr-assistant
uvicorn main:combined_app --reload --port 8000

# Production
gunicorn -w 4 -b 0.0.0.0:8000 "main:combined_app"
```

#### Frontend

```bash
cd src/multi-agent-hr-assistant/ui

# Development
npm run dev

# Production build
npm run build
npm start
```

#### Redis

```bash
# Docker
docker run -d -p 6379:6379 --name redis redis:latest

# Or if installed locally
redis-server
```

---

## API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### Process User Query

```http
POST /process_query
Content-Type: application/json

{
  "query": "What is my leave balance?",
  "conversation_id": "conv-123",
  "auth_token": "user-token",
  "user_id": "user-456",
  "attachment_url": null,
  "attachment_name": null,
  "UploadedText": null,
  "isAdmin": false
}

Response:
{
  "final_response": "You have 15 days of leave remaining..."
}
```

#### Get Leave Balance

```http
GET /leave_balance
Authorization: Bearer {token}

Response:
{
  "leave_balance": {
    "used": 5,
    "remaining": 15,
    "total": 20
  }
}
```

#### Create Ticket

```http
POST /ticket_creation
Content-Type: application/json

{
  "auth_token": "user-token",
  "conversation_id": "conv-123",
  "ticket_type": "complaint",
  "description": "Issue description",
  "attachment_url": null
}

Response:
{
  "ticket_id": "ticket-789",
  "status": "created",
  "timestamp": "2024-03-15T10:30:00Z"
}
```

#### Get Chat History

```http
GET /get_chat_history?conversation_id=conv-123
Authorization: Bearer {token}

Response:
{
  "messages": [
    {"role": "user", "content": "What is policy?"},
    {"role": "assistant", "content": "Policy is..."}
  ]
}
```

---

## Project Structure

```
multi-agent-hr-assistant/
├── src/
│   └── multi-agent-hr-assistant/
│       ├── application/                 # Application logic
│       │   ├── agents/                  # Agent implementations
│       │   │   ├── supervisor.py        # Supervisor agent
│       │   │   ├── clerk.py             # Clerk agent
│       │   │   └── librarian.py         # Librarian agent
│       │   ├── workflow.py              # Workflow orchestration
│       │   ├── states.py                # LangGraph state definitions
│       │   └── services/
│       │       └── ingestion.py         # Document ingestion
│       │
│       ├── domain/                      # Domain layer
│       │   ├── entities.py              # Data models
│       │   ├── intents.py               # Intent types
│       │   ├── ports.py                 # Port interfaces
│       │   ├── prompts/                 # LLM prompts
│       │   └── tools/                   # Agent tools
│       │
│       ├── infrastructure/              # Infrastructure layer
│       │   ├── adapters/                # External service adapters
│       │   ├── llm_providers/           # LLM integrations
│       │   ├── redis/                   # Redis client
│       │   ├── supabase/                # Supabase client
│       │   ├── vector_store/            # Chroma client
│       │   └── socket/                  # WebSocket handlers
│       │
│       ├── data/                        # Data storage
│       │   └── policies/                # Policy documents
│       │       └── chroma.sqlite3       # Vector store
│       │
│       ├── pics/                        # Architecture diagrams
│       │   ├── supervisor_agent_graph.png
│       │   ├── clerk_agent_graph.png
│       │   └── librarian_agent_graph.png
│       │
│       ├── ui/                          # Next.js frontend
│       │   ├── src/
│       │   │   ├── app/                 # Next.js app directory
│       │   │   ├── components/          # React components
│       │   │   ├── lib/                 # Utilities
│       │   │   └── types/               # TypeScript types
│       │   ├── public/                  # Static assets
│       │   └── package.json
│       │
│       ├── main.py                      # FastAPI entry point
│       ├── config.py                    # Configuration
│       └── __init__.py
│
├── tests/                               # Test suite
│   ├── test_agents.py
│   ├── test_adapters.py
│   ├── test_integration.py
│   └── requirements-test.txt
│
├── Dockerfile                           # Backend container
├── docker-compose.yml                   # Container orchestration
├── pyproject.toml                       # Python project config
├── Makefile                             # Development commands
├── .env.example                         # Environment template
└── README.md                            # This file
```

---

## Agent Interaction Flow

### Example: User Asks "What's my leave balance?"

```
1. User Query
   Input: "What's my leave balance?"

2. Supervisor Agent
   - Recognizes intent: LEAVE_REQUEST
   - Decomposes task: "Fetch leave balance for user"
   - Routes to: Clerk Agent

3. Clerk Agent
   - Classifies action type: get_balance
   - Calls: fetch_user_leave_balance(user_id)
   - Retrieves: {"used": 5, "remaining": 15, "total": 20}
   - Generates response: "You have 15 days of leave remaining..."

4. Response Flow
   - Clerk Agent → Supervisor Agent
   - Supervisor synthesizes final response
   - Response sent to user via WebSocket
   - Message saved to chat history
```

### Example: User Asks "Show me policies for remote work"

```
1. User Query
   Input: "Show me policies regarding remote work"

2. Supervisor Agent
   - Recognizes intent: POLICY_QUERY
   - Decomposes task: "Retrieve remote work policies"
   - Routes to: Librarian Agent

3. Librarian Agent
   - Classifies action: retrieve_policy
   - Creates embedding of query
   - Searches Chroma vector store
   - Retrieves relevant policy documents
   - Generates contextual response

4. Response Flow
   - Librarian Agent → Supervisor Agent
   - Supervisor synthesizes with context
   - Response sent to user
   - Message persisted to database
```

---

## Testing

### Run All Tests

```bash
make test
```

### Run with Coverage Report

```bash
make test-cov
```

This generates an HTML report in `htmlcov/index.html`

### Run Specific Test File

```bash
cd tests
pytest test_agents.py -v
pytest test_integration.py -v
```

### Run with Markers

```bash
pytest -m "not slow"           # Skip slow tests
pytest -m "unit"               # Only unit tests
pytest -m "integration"        # Only integration tests
```

### Test Files

- **`test_agents.py`** - Agent logic tests
- **`test_adapters.py`** - External service adapter tests
- **`test_integration.py`** - End-to-end workflow tests
- **`test_entities.py`** - Data model tests
- **`test_utilities.py`** - Utility function tests

---

## Docker Deployment

### Build Docker Images

```bash
make docker-build
```

### Start Services

```bash
make docker-up
```

This starts:

- **Backend API** on port 8000
- **Redis** on port 6379

### Environment Variables

Docker reads from `.env.local`:

```bash
REDIS_PASSWORD=your-password
SUPABASE_URL=your-url
GROQ_API_KEY=your-key
# etc...
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f redis
```

### Shell Access

```bash
# Access backend container
docker exec -it agent-backend-prod bash

# Access Redis CLI
docker exec -it agent-redis-prod redis-cli -a <password>
```

### Stop Services

```bash
make docker-down
```

### Clean Everything

```bash
make docker-clean
```

---

## Development

### Code Quality

#### Format Code

```bash
make format
```

Commands:

- Black (Python formatting)
- isort (import sorting)

#### Check Formatting

```bash
make format-check
```

#### Lint Code

```bash
make lint
```

Uses pylint for code quality analysis

### IDE Setup

#### VSCode

1. Install extensions:
   - Python
   - Pylance
   - Black Formatter
   - isort

2. Add to `.vscode/settings.json`:

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  }
}
```

#### PyCharm

- Create virtual environment from `pyproject.toml`
- Mark `src/` as Sources Root
- Configure Black and isort in Settings

### Adding New Features

1. **Create branch**

   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes**
   - Update `pyproject.toml` if adding dependencies
   - Follow existing code structure

3. **Test locally**

   ```bash
   make format
   make lint
   make test
   ```

4. **Commit**

   ```bash
   git add -A
   git commit -m "feat: description of changes"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   ```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'xxx'"

**Solution**:

```bash
# Reinstall dependencies
pip install -e . --force-reinstall

# Or specific package
pip install langchain
```

### Issue: Redis Connection Refused

**Solution**:

```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
docker run -d -p 6379:6379 redis:latest

# Or for local Redis
redis-server
```

### Issue: "Cannot connect to Supabase"

**Solution**:

1. Verify `.env.local` has correct values:

   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   ```

2. Test connection:

   ```bash
   curl -H "Authorization: Bearer $SUPABASE_KEY" \
        $SUPABASE_URL/rest/v1/
   ```

3. Check Supabase project is online

### Issue: Port Already in Use

**Solution**:

```bash
# Find process using port
lsof -i :8000

# Or change port
BACKEND_PORT=8001 make docker-up
```

### Issue: Frontend Can't Connect to Backend

**Solution**:

1. Check backend is running:

   ```bash
   curl http://localhost:8000/docs
   ```

2. Update frontend env:

   ```bash
   # Edit .env.local
   NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
   ```

3. Restart frontend:
   ```bash
   npm run dev
   ```

### Issue: "permission denied" on docker-entrypoint.sh

**Solution**:

```bash
# Make script executable
chmod +x docker-entrypoint.sh

# Rebuild Docker image
make docker-build
```

---

## Additional Resources

### Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [Docker Docs](https://docs.docker.com/)
- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)

### API References

- [Groq API Docs](https://console.groq.com/docs/speech-text)
- [Chroma Docs](https://docs.trychroma.com/)
- [Redis Docs](https://redis.io/documentation)

### Learning Resources

- LangChain Tutorials
- Building with LLMs courses
- Multi-agent Systems patterns

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request

### Code Standards

- Follow PEP 8 guidelines
- Write unit tests for new features
- Update documentation
- Use meaningful commit messages

---

## License

This project is licensed under the MIT License - see LICENSE file for details.

---

## Support

For issues, questions, or suggestions:

- Open an GitHub Issue
- Check existing documentation
- Review troubleshooting section
