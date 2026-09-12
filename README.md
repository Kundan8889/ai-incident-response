# AI Engineering Incident Response & Autonomous Debugging Platform

An intelligent, autonomous platform for real-time engineering incident triage, root cause analysis, automated remediation workflows, and post-mortem generation.

## Current Architecture (Phase 0 Foundation)

\ai-incident-response/
├── frontend/          # Next.js 15+ App Router, Tailwind CSS, TypeScript
├── backend/           # FastAPI, Uvicorn, Pydantic
├── infrastructure/    # Future infrastructure configurations
└── docs/              # Architectural specs and documentation
\
### Components

- **Frontend**: Lightweight Next.js dashboard configured with App Router, TypeScript, and Tailwind CSS.
- **Backend**: Python FastAPI application exposing core REST endpoints (including \/health\).
- **Infrastructure**: Placeholder for future deployment modules.
- **Docs**: Documentation and roadmap specifications.

---

## Getting Started

### Prerequisites
- Node.js >= 18.x
- Python >= 3.10
- npm / pnpm / yarn

---

### Running the Backend

1. Navigate to the backend directory:
   \\ash
   cd backend
   \2. Create and activate a virtual environment:
   \\ash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   \3. Install dependencies:
   \\ash
   pip install -r requirements.txt
   \4. Copy the environment variables:
   \\ash
   cp .env.example .env
   \5. Run the development server:
   \\ash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   \6. Verify the health check:
   - Health check: [http://localhost:8000/health](http://localhost:8000/health)
   - Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Running the Frontend

1. Navigate to the frontend directory:
   \\ash
   cd frontend
   \2. Install dependencies:
   \\ash
   npm install
   \3. Copy the environment variables:
   \\ash
   cp .env.example .env.local
   \4. Start the development server:
   \\ash
   npm run dev
   \5. Access the application in your browser at [http://localhost:3000](http://localhost:3000).
