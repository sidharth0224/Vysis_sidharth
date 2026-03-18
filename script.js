/* ═══════════════════════════════════════════════════════════════
   VISYS SkillMatch – Frontend Logic
   Constellation network background + Skill matching API calls
   ═══════════════════════════════════════════════════════════════ */

/* ── API Configuration ── */
const API_BASE_URL = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "";

/* ── DOM Elements ── */
const form            = document.getElementById("matchForm");
const submitBtn       = document.getElementById("submitBtn");
const spinner         = document.getElementById("spinner");
const jobDescEl       = document.getElementById("jobDescription");
const candidateEl     = document.getElementById("candidateProfile");
const resultsSection  = document.getElementById("results");
const errorMessageEl  = document.getElementById("errorMessage");
const matchedSkillsEl = document.getElementById("matchedSkills");
const missingSkillsEl = document.getElementById("missingSkills");
const matchedCountEl  = document.getElementById("matchedCount");
const missingCountEl  = document.getElementById("missingCount");
const scoreValueEl    = document.getElementById("scoreValue");
const scoreCircleEl   = document.getElementById("scoreCircle");
const summaryTextEl   = document.getElementById("summaryText");

const CIRCLE_CIRCUMFERENCE = 2 * Math.PI * 52;

/* ═══════════════════════════════════════════════════════════════
   Constellation Network Canvas
   ═══════════════════════════════════════════════════════════════ */
(function initNetwork() {
    const canvas = document.getElementById("networkCanvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let width, height, particles;
    const PARTICLE_COUNT = 80;
    const CONNECTION_DIST = 150;
    const MOUSE_RADIUS = 200;
    let mouse = { x: -9999, y: -9999 };

    function resize() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    }

    function createParticles() {
        particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.4,
                vy: (Math.random() - 0.5) * 0.4,
                r: Math.random() * 1.5 + 0.5,
                alpha: Math.random() * 0.5 + 0.3,
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);

        // Update & draw particles
        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            // Wrap around edges
            if (p.x < 0) p.x = width;
            if (p.x > width) p.x = 0;
            if (p.y < 0) p.y = height;
            if (p.y > height) p.y = 0;

            // Draw particle
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 180, 255, ${p.alpha})`;
            ctx.fill();

            // Draw connections
            for (let j = i + 1; j < particles.length; j++) {
                const q = particles[j];
                const dx = p.x - q.x;
                const dy = p.y - q.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < CONNECTION_DIST) {
                    const opacity = (1 - dist / CONNECTION_DIST) * 0.15;
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(q.x, q.y);
                    ctx.strokeStyle = `rgba(0, 180, 255, ${opacity})`;
                    ctx.lineWidth = 0.6;
                    ctx.stroke();
                }
            }

            // Mouse interaction: brighten near cursor
            const mdx = p.x - mouse.x;
            const mdy = p.y - mouse.y;
            const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
            if (mDist < MOUSE_RADIUS) {
                const glow = (1 - mDist / MOUSE_RADIUS) * 0.6;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r * 2, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 212, 255, ${glow})`;
                ctx.fill();
            }
        }

        requestAnimationFrame(animate);
    }

    window.addEventListener("resize", () => {
        resize();
    });

    document.addEventListener("mousemove", (e) => {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });

    resize();
    createParticles();
    animate();
})();

/* ═══════════════════════════════════════════════════════════════
   Form Submission
   ═══════════════════════════════════════════════════════════════ */
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

/* ═══════════════════════════════════════════════════════════════
   Render Results
   ═══════════════════════════════════════════════════════════════ */
function renderResults(data) {
    // Matched skills
    matchedSkillsEl.innerHTML = data.matched_skills.length
        ? data.matched_skills.map((s, i) => skillTag(s, "matched", i)).join("")
        : '<span class="tag tag--none">No matching skills found</span>';

    // Missing skills
    missingSkillsEl.innerHTML = data.missing_skills.length
        ? data.missing_skills.map((s, i) => skillTag(s, "missing", i)).join("")
        : '<span class="tag tag--none">No missing skills – perfect match!</span>';

    // Update counts
    matchedCountEl.textContent = data.matched_skills.length;
    missingCountEl.textContent = data.missing_skills.length;

    // Score ring
    const percentage = parseFloat(data.match_percentage);
    animateScore(percentage);

    // Summary
    summaryTextEl.textContent = data.summary;

    // Show & scroll
    resultsSection.style.display = "block";
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

function skillTag(skill, type, index) {
    const delay = index * 0.05;
    return `<span class="tag tag--${type}" style="animation-delay:${delay}s">${capitalize(skill)}</span>`;
}

function animateScore(percentage) {
    const offset = CIRCLE_CIRCUMFERENCE - (percentage / 100) * CIRCLE_CIRCUMFERENCE;

    // Color based on score: red → yellow → green → cyan
    let color;
    if (percentage >= 80)      color = "#00e676";
    else if (percentage >= 60) color = "#00d4ff";
    else if (percentage >= 40) color = "#ffab00";
    else                       color = "#ff5252";

    scoreCircleEl.style.stroke = color;
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

/* ── Helpers ── */
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
