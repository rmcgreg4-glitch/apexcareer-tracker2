import json
import os
import re
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for


BASE_DIR = Path(__file__).resolve().parent
JOBS_FILE = BASE_DIR / "jobs.json"

app = Flask(__name__)
# In a real production app, this should come from an environment variable.
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "you",
    "your",
    "will",
    "our",
    "this",
    "we",
    "they",
    "their",
    "who",
    "have",
    "has",
    "had",
    "into",
    "about",
    "using",
    "use",
    "work",
    "works",
    "working",
    "role",
    "job",
    "team",
    "ability",
    "experience",
    "years",
    "year",
    "skills",
    "skill",
    "including",
    "plus",
    "preferred",
    "required",
}


def ensure_jobs_file():
    """Create the JSON file if it does not exist yet."""
    if not JOBS_FILE.exists():
        JOBS_FILE.write_text("[]", encoding="utf-8")


def load_jobs():
    """Read all saved job applications from jobs.json."""
    ensure_jobs_file()

    try:
        with JOBS_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        # If the file becomes corrupted, the app will still load gracefully.
        return []


def save_jobs(jobs):
    """Write the latest job application data back to jobs.json."""
    with JOBS_FILE.open("w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2)


def normalize_text(value):
    """Normalize text so duplicate checks are more reliable."""
    return " ".join(value.strip().lower().split())


def is_duplicate_job(jobs, company, title, link):
    """Prevent saving the same job more than once."""
    normalized_company = normalize_text(company)
    normalized_title = normalize_text(title)
    normalized_link = normalize_text(link)

    for job in jobs:
        same_company = normalize_text(job.get("company", "")) == normalized_company
        same_title = normalize_text(job.get("title", "")) == normalized_title
        same_link = normalize_text(job.get("link", "")) == normalized_link

        if same_company and same_title and same_link:
            return True

    return False


def split_sentences(text):
    """Split free-form text into readable sentence-like chunks."""
    cleaned_text = " ".join(text.split())
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", cleaned_text)
        if sentence.strip()
    ]


def extract_keywords(text, limit=12):
    """Return the most useful repeated keywords from a text block."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z0-9+#.\-]{2,}\b", text.lower())
    counts = {}

    for word in words:
        if word in STOP_WORDS:
            continue
        counts[word] = counts.get(word, 0) + 1

    sorted_keywords = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )
    return [keyword for keyword, _ in sorted_keywords[:limit]]


def format_keyword_list(keywords, fallback):
    """Turn keywords into a human-friendly comma-separated string."""
    if not keywords:
        return fallback
    if len(keywords) == 1:
        return keywords[0]
    if len(keywords) == 2:
        return f"{keywords[0]} and {keywords[1]}"
    return f"{', '.join(keywords[:-1])}, and {keywords[-1]}"


def generate_ai_outputs(company, title, description):
    """
    Generate stable local outputs so the app can be tested without API access.

    The logic is intentionally simple and deterministic for beginner readability.
    """
    sentences = split_sentences(description)
    keywords = extract_keywords(description, limit=8)
    keyword_list = format_keyword_list(keywords[:4], "core technical and teamwork skills")

    summary = []

    for sentence in sentences[:3]:
        summary.append(sentence.rstrip(".") + ".")

    while len(summary) < 3:
        if len(summary) == 0:
            summary.append(
                f"This {title.lower()} role at {company} emphasizes {keyword_list}."
            )
        elif len(summary) == 1:
            summary.append(
                f"The posting highlights day-to-day collaboration, ownership, and practical problem solving."
            )
        else:
            summary.append(
                f"Candidates should be ready to demonstrate relevant experience with {keyword_list}."
            )

    question_starters = [
        f"What experiences have prepared you for this {title} role at {company}?",
        f"How have you used {keywords[0] if keywords else 'your technical skills'} in a recent project?",
        f"Describe a time you collaborated with others to solve a difficult problem.",
        f"How would you approach the main responsibilities described in this job posting?",
        f"What interests you most about joining {company} in this position?",
    ]

    followup_email = (
        f"Subject: Follow-Up on {title} Application\n\n"
        f"Dear {company} Hiring Team,\n\n"
        f"I recently applied for the {title} role and wanted to share my continued interest "
        f"in the opportunity. The position's focus on {keyword_list} especially stood out to me.\n\n"
        f"If there are any updates on next steps or additional materials I can provide, "
        f"I would be happy to help.\n\n"
        f"Thank you for your time and consideration.\n\n"
        f"Best regards,\n"
        f"[Your Name]"
    )

    return {
        "summary": summary,
        "interview_questions": question_starters,
        "followup_email": followup_email,
    }


def analyze_resume_match(job_description, resume_text):
    """Compare resume keywords against the job description with simple keyword logic."""
    job_keywords = extract_keywords(job_description, limit=14)
    resume_keywords = set(extract_keywords(resume_text, limit=40))

    matched_keywords = [keyword for keyword in job_keywords if keyword in resume_keywords]
    missing_keywords = [keyword for keyword in job_keywords if keyword not in resume_keywords]

    if job_keywords:
        match_score = round((len(matched_keywords) / len(job_keywords)) * 100)
    else:
        match_score = 0

    strengths = [
        f"Your resume already reflects experience with {keyword}."
        for keyword in matched_keywords[:5]
    ]

    if not strengths:
        strengths = [
            "Your resume includes relevant background, but it could be aligned more directly to the posting.",
            "You already have resume content to work with; the next step is making the job-specific skills more explicit.",
        ]

    missing_skills = [
        f"Consider adding evidence of {keyword} if you have worked with it."
        for keyword in missing_keywords[:5]
    ]

    if not missing_skills:
        missing_skills = [
            "Your resume covers the main keywords from this posting.",
            "Focus on quantifying impact so the alignment is even clearer.",
        ]

    return {
        "match_score": max(0, min(match_score, 100)),
        "strengths": strengths,
        "missing_skills": missing_skills,
    }


def parse_date_safe(date_string):
    """Parse ISO-style dates without raising if the value is missing or invalid."""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def build_dashboard_insight(jobs):
    """Create a simple career insight from the saved applications."""
    if not jobs:
        return (
            "You have not added any applications yet. Start with a few target roles so the "
            "platform can surface more tailored AI guidance."
        )

    words = []
    for job in jobs:
        words.extend(extract_keywords(job.get("description", ""), limit=6))

    counts = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1

    top_keywords = [
        keyword
        for keyword, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:3]
    ]
    focus = format_keyword_list(top_keywords, "role-specific skills")

    return (
        f"You have applied to {len(jobs)} roles. Consider emphasizing {focus} "
        f"to improve your interview readiness and resume alignment."
    )


def build_analytics(jobs):
    """Build simple analytics summaries for the analytics page."""
    applications_count = len(jobs)
    interviews_count = sum(1 for job in jobs if job.get("status") == "Interview")
    offers_count = sum(1 for job in jobs if job.get("status") == "Offer")

    interview_conversion_rate = (
        round((interviews_count / applications_count) * 100, 1)
        if applications_count
        else 0
    )
    offer_rate = (
        round((offers_count / interviews_count) * 100, 1)
        if interviews_count
        else 0
    )

    month_counter = Counter()
    company_counter = Counter()

    for job in jobs:
        parsed_date = parse_date_safe(job.get("date_applied"))
        if parsed_date:
            month_counter[parsed_date.strftime("%b %Y")] += 1
        company_counter[job.get("company", "Unknown")] += 1

    monthly_applications = [
        {"label": label, "value": value}
        for label, value in sorted(
            month_counter.items(),
            key=lambda item: datetime.strptime(item[0], "%b %Y"),
        )
    ]

    top_companies = [
        {"label": company, "value": count}
        for company, count in company_counter.most_common(5)
    ]

    return {
        "applications": applications_count,
        "interviews": interviews_count,
        "offers": offers_count,
        "interview_conversion_rate": interview_conversion_rate,
        "offer_rate": offer_rate,
        "monthly_applications": monthly_applications,
        "top_companies": top_companies,
    }


@app.route("/")
def root():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
def dashboard():
    jobs = load_jobs()
    # Show newest applications first for a better dashboard experience.
    jobs = sorted(jobs, key=lambda job: job.get("date_applied", ""), reverse=True)
    recent_jobs = jobs[:5]
    insight = build_dashboard_insight(jobs)
    return render_template(
        "dashboard.html",
        jobs=jobs,
        recent_jobs=recent_jobs,
        insight=insight,
        active_page="dashboard",
    )


@app.route("/applications")
def applications():
    jobs = load_jobs()
    jobs = sorted(jobs, key=lambda job: job.get("date_applied", ""), reverse=True)
    selected_filter = request.args.get("filter", "all").strip().lower()
    return render_template(
        "applications.html",
        jobs=jobs,
        active_page="applications",
        selected_filter=selected_filter,
    )


@app.route("/ai-tools")
def ai_tools():
    return render_template("ai_tools.html", active_page="ai_tools")


@app.route("/analytics")
def analytics():
    jobs = load_jobs()
    jobs = sorted(jobs, key=lambda job: job.get("date_applied", ""), reverse=True)
    analytics_data = build_analytics(jobs)
    return render_template(
        "analytics.html",
        jobs=jobs,
        analytics_data=analytics_data,
        active_page="analytics",
    )


@app.route("/settings")
def settings():
    profile = {
        "name": "Alex Student",
        "email": "alex@example.com",
        "school": "State University",
        "major": "Computer Science",
        "graduation_year": "2027",
    }
    return render_template("settings.html", profile=profile, active_page="settings")


@app.route("/add", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        company = request.form.get("company", "").strip()
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        link = request.form.get("link", "").strip()
        date_applied = request.form.get("date_applied", "").strip()

        if not all([company, title, description, link, date_applied]):
            flash("Please fill in every field before submitting.", "error")
            return render_template(
                "add_job.html",
                form_data=request.form,
                active_page="add",
            )

        jobs = load_jobs()

        if is_duplicate_job(jobs, company, title, link):
            flash(
                "This job application already exists in your command center.",
                "error",
            )
            return render_template(
                "add_job.html",
                form_data=request.form,
                active_page="add",
            )

        try:
            ai_outputs = generate_ai_outputs(company, title, description)
        except Exception as error:
            flash(f"AI generation failed: {error}", "error")
            return render_template(
                "add_job.html",
                form_data=request.form,
                active_page="add",
            )

        new_job = {
            "id": str(uuid.uuid4()),
            "company": company,
            "title": title,
            "description": description,
            "link": link,
            "date_applied": date_applied,
            "summary": ai_outputs["summary"],
            "interview_questions": ai_outputs["interview_questions"],
            "followup_email": ai_outputs["followup_email"],
            "status": "Applied",
            "notes": request.form.get("notes", "").strip(),
        }

        jobs.append(new_job)
        save_jobs(jobs)

        flash("Job application added successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_job.html", form_data={}, active_page="add")


@app.route("/job/<job_id>", methods=["GET", "POST"])
def job_detail(job_id):
    jobs = load_jobs()
    job = next((job for job in jobs if job["id"] == job_id), None)

    if not job:
        flash("That job application could not be found.", "error")
        return redirect(url_for("applications"))

    analysis = None
    resume_text = ""

    if request.method == "POST":
        resume_text = request.form.get("resume_text", "").strip()

        if not resume_text:
            flash("Paste your resume text to run the Resume Match Analyzer.", "error")
        else:
            analysis = analyze_resume_match(job["description"], resume_text)

    return render_template(
        "job_detail.html",
        job=job,
        analysis=analysis,
        resume_text=resume_text,
        active_page="applications",
    )


@app.route("/update-status/<job_id>", methods=["POST"])
def update_status(job_id):
    jobs = load_jobs()
    new_status = request.form.get("status", "").strip()
    valid_statuses = {"Applied", "Interview", "Offer", "Rejected"}

    if new_status not in valid_statuses:
        flash("Invalid status selected.", "error")
        return redirect(url_for("applications"))

    updated = False
    for job in jobs:
        if job["id"] == job_id:
            job["status"] = new_status
            updated = True
            break

    if updated:
        save_jobs(jobs)
        flash("Application status updated.", "success")
    else:
        flash("That job application could not be found.", "error")

    return redirect(url_for("applications", filter=new_status.lower()))


@app.route("/update-notes/<job_id>", methods=["POST"])
def update_notes(job_id):
    jobs = load_jobs()
    notes = request.form.get("notes", "").strip()

    updated = False
    for job in jobs:
        if job["id"] == job_id:
            job["notes"] = notes
            updated = True
            break

    if updated:
        save_jobs(jobs)
        flash("Application notes updated.", "success")
    else:
        flash("That job application could not be found.", "error")

    return redirect(url_for("job_detail", job_id=job_id))


@app.route("/delete/<job_id>", methods=["POST"])
def delete_job(job_id):
    jobs = load_jobs()
    updated_jobs = [job for job in jobs if job["id"] != job_id]

    if len(updated_jobs) == len(jobs):
        flash("That job application could not be found.", "error")
    else:
        save_jobs(updated_jobs)
        flash("Job application deleted.", "success")

    return redirect(url_for("applications"))


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
