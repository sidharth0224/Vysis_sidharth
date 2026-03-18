from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("stopwords", quiet=True)

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


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[\n\r\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
        "golang": "go",
        "k8s": "kubernetes",
        "sklearn": "scikit-learn",
        "ci cd": "ci/cd",
        "node js": "node.js",
        "express js": "express.js",
        "vue js": "vue.js",
        "next js": "next.js",
        "nuxt js": "nuxt.js",
        "angular js": "angular",
        "rest api": "restful api",
        "google cloud platform": "gcp",
        "google cloud": "gcp",
        "amazon web services": "aws",
    }
    normalized: set[str] = set()
    for skill in found_skills:
        canonical = aliases.get(skill, skill)
        normalized.add(canonical)

    return normalized


def generate_summary(
    matched: list[str],
    missing: list[str],
    percentage: float,
) -> str:
    if percentage == 100:
        return (
            "🎯 Perfect match! The candidate possesses all the required skills "
            f"({', '.join(matched)}). Highly recommended for the role."
        )
    if percentage >= 80:
        return (
            f"✅ Strong match ({percentage:.0f}%). The candidate demonstrates "
            f"expertise in {', '.join(matched[:5])}. "
            f"Minor gaps in: {', '.join(missing)}."
        )
    if percentage >= 60:
        return (
            f"⚠️ Partial match ({percentage:.0f}%). The candidate has relevant skills "
            f"including {', '.join(matched[:4])}, but is missing key competencies: "
            f"{', '.join(missing[:5])}."
        )
    if percentage >= 30:
        return (
            f"🔶 Weak match ({percentage:.0f}%). The candidate covers some basics "
            f"({', '.join(matched[:3])}) but lacks several critical skills: "
            f"{', '.join(missing[:5])}. Significant upskilling required."
        )
    return (
        f"❌ Low match ({percentage:.0f}%). The candidate's profile does not align "
        f"well with the role requirements. Missing skills include: "
        f"{', '.join(missing[:6])}."
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Skill Matching API is running 🚀"}


@app.post("/match", response_model=MatchResponse)
def match_skills(request: MatchRequest):
    if not request.job_description.strip():
        raise HTTPException(status_code=400, detail="Job description cannot be empty.")
    if not request.candidate_profile.strip():
        raise HTTPException(
            status_code=400, detail="Candidate profile cannot be empty."
        )

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
