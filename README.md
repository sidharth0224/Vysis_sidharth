# Vysis_sidharth

## SkillMatch AI – Skill Matching Application

An AI-powered skill gap analysis tool that compares Job Descriptions with Candidate Profiles using NLP.

### 🌐 Live Demo

**[https://vysis.vercel.app](https://vysis.vercel.app)**

### Features

- 150+ skill keyword extraction with bigram/trigram matching
- Alias normalization (k8s → kubernetes, golang → go)
- Color-coded skill tags (green = matched, red = missing)
- Animated SVG score ring with match percentage
- Smart summary generation based on score ranges
- Loading spinner and error handling
- Responsive dark glassmorphism UI

### Tech Stack

- **Backend**: Python, FastAPI, NLTK
- **Frontend**: HTML, CSS, JavaScript
- **Deployment**: Vercel (Serverless Functions)

### Project Structure

```
├── api/index.py           → Vercel serverless function
├── backend/main.py        → Local FastAPI server
├── frontend/              → Original frontend (local dev)
├── index.html             → Root (Vercel static)
├── style.css              → Root (Vercel static)
├── script.js              → Root (auto-detects environment)
├── requirements.txt       → Python dependencies
└── vercel.json            → Vercel config
```

### Run Locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open `frontend/index.html` in your browser.

### API Endpoint

```
POST /match
{
  "job_description": "...",
  "candidate_profile": "..."
}
```

Response:
```json
{
  "matched_skills": [],
  "missing_skills": [],
  "match_percentage": "75.0%",
  "summary": "..."
}
```
