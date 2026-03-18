from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import os
import nltk
from nltk.tokenize import word_tokenize

nltk.data.path.append("/tmp/nltk_data")
nltk.download("punkt", download_dir="/tmp/nltk_data", quiet=True)
nltk.download("punkt_tab", download_dir="/tmp/nltk_data", quiet=True)
nltk.download("stopwords", download_dir="/tmp/nltk_data", quiet=True)
nltk.download("averaged_perceptron_tagger", download_dir="/tmp/nltk_data", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", download_dir="/tmp/nltk_data", quiet=True)

from nltk.corpus import stopwords

app = FastAPI(
    title="Skill Matching API",
    description="Compare job descriptions with candidate profiles",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MatchRequest(BaseModel):
    job_description: str
    candidate_profile: str


class MatchResponse(BaseModel):
    matched_skills: list[str]
    missing_skills: list[str]
    match_percentage: str
    summary: str


SKILLS_DATABASE: list[str] = [
    "natural language processing", "computer vision", "deep learning",
    "machine learning", "data science", "data analysis", "data engineering",
    "data visualization", "data mining", "data warehousing", "big data",
    "web development", "mobile development", "cloud computing",
    "software engineering", "software development", "project management",
    "product management", "agile methodology", "version control", "ci/cd",
    "ci cd", "unit testing", "test driven development",
    "object oriented programming", "functional programming",
    "distributed systems", "microservices architecture", "restful api",
    "rest api", "api development", "database management", "system design",
    "operating systems", "network security", "cyber security",
    "penetration testing", "ethical hacking", "power bi", "google cloud",
    "google cloud platform", "amazon web services", "neural networks",
    "recurrent neural networks", "convolutional neural networks",
    "generative ai", "large language models", "prompt engineering",
    "feature engineering", "model deployment", "spring boot", "ruby on rails",
    "react native", "node js", "node.js", "express js", "express.js",
    "vue js", "vue.js", "next js", "next.js", "nuxt js", "nuxt.js",
    "angular js", "asp.net",
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
    "golang", "rust", "swift", "kotlin", "scala", "r", "matlab", "php",
    "perl", "html", "css", "sass", "less", "sql", "nosql", "mysql",
    "postgresql", "mongodb", "redis", "cassandra", "elasticsearch",
    "dynamodb", "sqlite", "oracle", "firebase", "supabase", "graphql",
    "rest", "grpc", "kafka", "rabbitmq", "celery", "airflow", "spark",
    "hadoop", "hive", "flink", "tableau", "looker", "matplotlib", "seaborn",
    "plotly", "d3", "react", "angular", "vue", "svelte", "django", "flask",
    "fastapi", "express", "nestjs", "laravel", "rails", "spring",
    "hibernate", "tensorflow", "pytorch", "keras", "scikit-learn", "sklearn",
    "pandas", "numpy", "scipy", "opencv", "nltk", "spacy", "huggingface",
    "transformers", "langchain", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "jenkins", "github actions", "gitlab ci", "circleci", "aws",
    "azure", "gcp", "heroku", "vercel", "netlify", "linux", "bash",
    "powershell", "git", "github", "gitlab", "bitbucket", "jira",
    "confluence", "figma", "sketch", "photoshop", "illustrator", "selenium",
    "cypress", "jest", "mocha", "pytest", "junit", "postman", "swagger",
    "nginx", "apache", "oauth", "jwt", "blockchain", "solidity", "web3",
    "ethereum", "devops", "mlops", "etl", "scrum", "kanban", "leadership",
    "communication", "teamwork", "problem solving", "critical thinking",
    "time management", "excel", "word", "powerpoint",
]

SKILLS_DATABASE.sort(key=lambda s: len(s), reverse=True)
STOP_WORDS = set(stopwords.words("english"))

# ── Non-skill stop words: generic verbs, adjectives, filler words ─────────
NON_SKILL_WORDS: set[str] = {
    # common verbs / verb forms
    "looking", "seeking", "hiring", "required", "preferred", "must",
    "should", "will", "need", "needs", "work", "working", "worked",
    "build", "building", "built", "create", "creating", "design",
    "designing", "develop", "developing", "developed", "manage",
    "managing", "managed", "lead", "leading", "ensure", "ensuring",
    "support", "supporting", "maintain", "maintaining", "implement",
    "implementing", "deliver", "delivering", "drive", "driving",
    "collaborate", "collaborating", "communicate", "communicating",
    "provide", "providing", "understand", "understanding", "apply",
    "applying", "use", "using", "used", "help", "helping",
    "contribute", "contributing", "participate", "participating",
    "identify", "identifying", "improve", "improving", "analyze",
    "analyzing", "define", "defining", "review", "reviewing",
    "write", "writing", "test", "testing", "debug", "debugging",
    "deploy", "deploying", "monitor", "monitoring", "optimize",
    "optimizing", "operate", "operating", "run", "running",
    "perform", "performing", "track", "tracking", "report",
    "reporting", "plan", "planning", "research", "researching",
    "evaluate", "evaluating", "establish", "establishing",
    "integrate", "integrating", "assist", "assisting",
    "join", "joining", "grow", "growing",
    # generic nouns / filler
    "experience", "experiences", "ability", "abilities", "skill",
    "skills", "knowledge", "team", "teams", "role", "roles",
    "position", "positions", "company", "companies", "organization",
    "organizations", "environment", "environments", "solution",
    "solutions", "service", "services", "system", "systems",
    "platform", "platforms", "product", "products", "project",
    "projects", "process", "processes", "tool", "tools",
    "technology", "technologies", "application", "applications",
    "client", "clients", "customer", "customers", "user", "users",
    "stakeholder", "stakeholders", "partner", "partners",
    "candidate", "candidates", "member", "members", "level",
    "levels", "area", "areas", "field", "fields", "industry",
    "industries", "market", "markets", "business", "opportunity",
    "opportunities", "requirement", "requirements", "responsibility",
    "responsibilities", "qualification", "qualifications",
    "benefit", "benefits", "year", "years", "month", "months",
    "day", "days", "time", "practice", "practices", "standard",
    "standards", "framework", "frameworks", "model", "models",
    "approach", "approaches", "strategy", "strategies",
    "performance", "quality", "feature", "features", "function",
    "functions", "component", "components", "resource", "resources",
    "infrastructure", "code", "data", "information", "result",
    "results", "goal", "goals", "objective", "objectives",
    "value", "values", "growth", "success", "impact",
    "change", "changes", "issue", "issues", "problem", "problems",
    "task", "tasks", "activity", "activities", "effort", "efforts",
    "detail", "details", "example", "examples", "type", "types",
    "range", "part", "parts", "set", "sets", "way", "ways",
    "base", "end", "order", "case", "cases", "hand", "number",
    "group", "groups", "line", "lines", "point", "points",
    "step", "steps", "state", "form", "name", "key", "top",
    "new", "high", "low", "good", "best", "etc", "plus",
    # adjectives / adverbs
    "strong", "excellent", "good", "great", "deep", "solid",
    "proven", "hands-on", "extensive", "minimum", "maximum",
    "preferred", "desired", "ideal", "relevant", "similar",
    "various", "multiple", "complex", "large", "small",
    "fast", "quick", "efficient", "effective", "responsible",
    "able", "capable", "familiar", "proficient", "experienced",
    "additional", "full", "remote", "hybrid", "onsite",
    # misc
    "salary", "compensation", "bonus", "equity", "location",
    "job", "description", "title", "summary", "overview",
    "profile", "resume", "cv", "cover", "letter",
    "degree", "bachelor", "bachelors", "master", "masters",
    "phd", "certification", "certified", "equivalent",
    "engineering", "science", "computer", "mathematics",
    "related", "including", "include", "includes",
    "across", "within", "around", "also", "well",
    # role titles / generic labels
    "engineer", "developer", "manager", "analyst", "architect",
    "consultant", "specialist", "administrator", "coordinator",
    "director", "officer", "intern", "trainee", "junior",
    "senior", "staff", "principal", "head", "chief",
    "software", "hardware", "web", "cloud", "mobile",
    "frontend", "backend", "fullstack", "full-stack",
    "years", "experience", "methodology", "structures",
    "apis", "rate", "media", "content", "social",
    "manager role", "software engineer", "years experience",
    "cloud engineer", "data engineer", "devops engineer",
}


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_skills_dynamic(text: str) -> set[str]:
    """
    Use POS tagging to extract noun-phrase skill candidates
    that are NOT in the hardcoded SKILLS_DATABASE.
    """
    processed = preprocess_text(text)
    tokens = word_tokenize(processed)
    tagged = nltk.pos_tag(tokens)

    noun_tags = {"NN", "NNS", "NNP", "NNPS"}

    chunks: list[str] = []
    current_chunk: list[str] = []

    for token, tag in tagged:
        if tag in noun_tags:
            current_chunk.append(token)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    expanded: list[str] = []
    for chunk in chunks:
        expanded.append(chunk)
        parts = chunk.split()
        if len(parts) > 1:
            expanded.extend(parts)

    known_lower = {s.lower() for s in SKILLS_DATABASE}
    all_stop = STOP_WORDS | NON_SKILL_WORDS

    dynamic_skills: set[str] = set()
    for phrase in expanded:
        normalized = phrase.strip().lower()

        if len(normalized) <= 1 or normalized.isdigit():
            continue

        if normalized in all_stop:
            continue

        if normalized in known_lower:
            continue

        dynamic_skills.add(normalized)

    return dynamic_skills


def extract_skills(text: str) -> set[str]:
    processed = preprocess_text(text)
    found_skills: set[str] = set()

    for skill in SKILLS_DATABASE:
        if len(skill) <= 2:
            pattern = r"(?<![a-zA-Z])" + re.escape(skill) + r"(?![a-zA-Z])"
        else:
            pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, processed):
            found_skills.add(skill)

    aliases = {
        "golang": "go", "k8s": "kubernetes", "sklearn": "scikit-learn",
        "ci cd": "ci/cd", "node js": "node.js", "express js": "express.js",
        "vue js": "vue.js", "next js": "next.js", "nuxt js": "nuxt.js",
        "angular js": "angular", "rest api": "restful api",
        "google cloud platform": "gcp", "google cloud": "gcp",
        "amazon web services": "aws",
    }
    normalized: set[str] = set()
    for skill in found_skills:
        normalized.add(aliases.get(skill, skill))

    # ── Merge dynamically extracted skills ──
    dynamic = extract_skills_dynamic(text)
    normalized.update(dynamic)

    return normalized


def generate_summary(matched: list[str], missing: list[str], percentage: float) -> str:
    if percentage == 100:
        return (f"🎯 Perfect match! The candidate possesses all the required skills "
                f"({', '.join(matched)}). Highly recommended for the role.")
    if percentage >= 80:
        return (f"✅ Strong match ({percentage:.0f}%). The candidate demonstrates "
                f"expertise in {', '.join(matched[:5])}. "
                f"Minor gaps in: {', '.join(missing)}.")
    if percentage >= 60:
        return (f"⚠️ Partial match ({percentage:.0f}%). The candidate has relevant skills "
                f"including {', '.join(matched[:4])}, but is missing key competencies: "
                f"{', '.join(missing[:5])}.")
    if percentage >= 30:
        return (f"🔶 Weak match ({percentage:.0f}%). The candidate covers some basics "
                f"({', '.join(matched[:3])}) but lacks several critical skills: "
                f"{', '.join(missing[:5])}. Significant upskilling required.")
    return (f"❌ Low match ({percentage:.0f}%). The candidate's profile does not align "
            f"well with the role requirements. Missing skills include: "
            f"{', '.join(missing[:6])}.")


@app.get("/api/match")
def health():
    return {"status": "ok", "message": "Skill Matching API is running 🚀"}


@app.post("/api/match")
def match_skills(request: MatchRequest):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if not request.candidate_profile.strip():
        raise HTTPException(status_code=400, detail="Candidate profile cannot be empty.")

    job_skills = extract_skills(request.job_description)
    candidate_skills = extract_skills(request.candidate_profile)

    matched = sorted(job_skills & candidate_skills)
    missing = sorted(job_skills - candidate_skills)

    total_required = len(job_skills)
    if total_required == 0:
        raise HTTPException(
            status_code=400,
            detail="No recognisable skills found in the job description. "
                   "Please provide a more detailed description.",
        )

    percentage = (len(matched) / total_required) * 100
    summary = generate_summary(matched, missing, percentage)

    return MatchResponse(
        matched_skills=matched,
        missing_skills=missing,
        match_percentage=f"{percentage:.1f}%",
        summary=summary,
    )
