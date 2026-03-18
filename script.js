const API_BASE_URL = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "";

const form            = document.getElementById("matchForm");
const submitBtn       = document.getElementById("submitBtn");
const spinner         = document.getElementById("spinner");
const jobDescEl       = document.getElementById("jobDescription");
const candidateEl     = document.getElementById("candidateProfile");
const resultsSection  = document.getElementById("results");
const errorMessageEl  = document.getElementById("errorMessage");
const matchedSkillsEl = document.getElementById("matchedSkills");
const missingSkillsEl = document.getElementById("missingSkills");
const scoreValueEl    = document.getElementById("scoreValue");
const scoreCircleEl   = document.getElementById("scoreCircle");
const summaryTextEl   = document.getElementById("summaryText");

const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * 52;

form.addEventListener("submit", handleSubmit);

async function handleSubmit(e) {
    e.preventDefault();
    hideError();
    hideResults();
    setLoading(true);

    const jobDescription   = jobDescEl.value.trim();
    const candidateProfile = candidateEl.value.trim();

    if (!jobDescription || !candidateProfile) {
        showError("Please fill in both fields before analysing.");
        setLoading(false);
        return;
    }

    try {
        const matchPath = API_BASE_URL ? "/match" : "/api/match";
        const response = await fetch(`${API_BASE_URL}${matchPath}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                job_description: jobDescription,
                candidate_profile: candidateProfile,
            }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => null);
            throw new Error(
                err?.detail || `Server responded with status ${response.status}`
            );
        }

        const data = await response.json();
        renderResults(data);
    } catch (error) {
        if (error.message.includes("Failed to fetch") || error.message.includes("NetworkError")) {
            showError(
                "Cannot reach the backend server. Make sure it is running on " +
                API_BASE_URL +
                " (run: uvicorn main:app --reload)"
            );
        } else {
            showError(error.message);
        }
    } finally {
        setLoading(false);
    }
}

function renderResults(data) {
    matchedSkillsEl.innerHTML = data.matched_skills.length
        ? data.matched_skills.map((s, i) => skillTag(s, "matched", i)).join("")
        : '<span class="tag tag--none">No matching skills found</span>';

    missingSkillsEl.innerHTML = data.missing_skills.length
        ? data.missing_skills.map((s, i) => skillTag(s, "missing", i)).join("")
        : '<span class="tag tag--none">No missing skills – perfect match!</span>';

    const percentage = parseFloat(data.match_percentage);
    animateScore(percentage);

    summaryTextEl.textContent = data.summary;

    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function skillTag(skill, type, index) {
    const delay = index * 0.06;
    return `<span class="tag tag--${type}" style="animation-delay:${delay}s">${capitalize(skill)}</span>`;
}

function animateScore(percentage) {
    const offset = CIRCLE_CIRCUMFERENCE - (percentage / 100) * CIRCLE_CIRCUMFERENCE;
    const hue = percentage * 1.2;
    scoreCircleEl.style.stroke = `hsl(${hue}, 80%, 55%)`;
    scoreCircleEl.style.strokeDashoffset = offset;
    animateCounter(scoreValueEl, 0, percentage, 1000);
}

function animateCounter(element, start, end, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - (1 - progress) * (1 - progress);
        const current = Math.round(start + (end - start) * eased);
        element.textContent = `${current}%`;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.classList.toggle("btn--loading", isLoading);
}

function showError(message) {
    errorMessageEl.textContent = message;
    errorMessageEl.style.display = "block";
}

function hideError() {
    errorMessageEl.style.display = "none";
    errorMessageEl.textContent = "";
}

function hideResults() {
    resultsSection.style.display = "none";
}

function capitalize(str) {
    return str.replace(/\b\w/g, (c) => c.toUpperCase());
}
