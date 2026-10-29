# Career Compass

AI-powered career guidance and job matching platform.

## Overview

Intelligent career assistant that helps users navigate career paths, discover job matches, and prepare for interviews using AI.

## Features

- **Career Path Recommendations**: Based on skills, interests, experience
- **Job Matching**: AI-powered job recommendations
- **Skill Gap Analysis**: Identify missing skills for target roles
- **Interview Preparation**: AI mock interviews, question banks
- **Resume Optimization**: ATS-friendly resume suggestions
- **Learning Paths**: Curated courses for skill development
- **Salary Insights**: Market rate data

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React + TypeScript |
| Backend | Python/FastAPI |
| AI/ML | LLM (OpenAI/HF), Embeddings |
| Vector DB | Pinecone / FAISS |
| Database | PostgreSQL |
| Auth | NextAuth / Clerk |
| Deployment | Vercel + Railway |

## Project Structure

```
career-compass/
├── frontend/
│   ├── app/                  # Next.js app router
│   ├── components/
│   ├── lib/
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── services/         # Business logic
│   │   ├── models/           # Pydantic/SQLAlchemy
│   │   └── ai/               # AI agents
│   ├── requirements.txt
│   └── alembic/              # Migrations
├── shared/
└── README.md
```

## Getting Started

```bash
git clone https://github.com/hemateja566/career-compass.git
cd career-compass

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd ../backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## AI Features

### Career Recommendation Engine
- User profile analysis
- Market trend integration
- Personalized role suggestions

### Interview Coach
- Role-specific question generation
- Answer evaluation with feedback
- STAR method guidance

### Resume Analyzer
- ATS compatibility scoring
- Keyword optimization
- Format suggestions

## API Endpoints (Planned)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/career/analyze` | Analyze profile & recommend paths |
| POST | `/api/jobs/match` | Find matching jobs |
| POST | `/api/interview/mock` | Start mock interview |
| POST | `/api/resume/analyze` | Analyze & improve resume |
| GET | `/api/skills/gap` | Identify skill gaps |

## Status

🚧 **Active Development** - Core AI features in progress

## License

MIT License