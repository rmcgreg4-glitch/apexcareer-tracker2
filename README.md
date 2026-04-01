# AI Job Application Command Center

A beginner-friendly Flask web app for tracking job applications and generating local AI-style job support without any external API dependency.

## Features

- View all job applications in a clean dashboard
- Add a new job application with company, title, description, link, and date applied
- Automatically generate:
  - a job summary
  - interview questions
  - a follow-up email
- Compare a pasted resume against a saved job description
- View a match score, strengths, and missing skills
- View a full details page for each job
- Delete saved jobs
- Persist data in `jobs.json`

## Project Structure

```text
job-command-center/
├── app.py
├── jobs.json
├── README.md
├── requirements.txt
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    ├── add_job.html
    ├── index.html
    └── job_detail.html
```

## 1. Install Dependencies

Create a virtual environment if you want:

```bash
python -m venv venv
source venv/bin/activate
```

Install the project packages:

```bash
pip install -r requirements.txt
```

If you want the direct example command:

```bash
pip install flask
```

## 2. Optional Environment Variables

You do not need an OpenAI API key for this version of the project.

Optional: set a Flask secret key

```bash
export FLASK_SECRET_KEY="your_secret_key_here"
```

## 3. Run the Application Locally

Start the Flask server:

```bash
python app.py
```

Then open this address in your browser:

```text
http://127.0.0.1:5000
```

## How It Works

When you add a new job:

1. The form submits to Flask
2. Flask checks for duplicates
3. Flask analyzes the job description locally
4. The app returns:
   - a 3-bullet summary
   - 5 interview questions
   - a follow-up email
5. The app stores everything in `jobs.json`

The generated outputs are only created once when the job is first added. They are not regenerated every time a page loads.

## Notes for Beginners

- `templates/` contains the HTML pages
- `static/` contains the CSS and JavaScript
- `jobs.json` acts like a tiny database
- `app.py` contains the Flask routes, deterministic text generation logic, and resume analyzer
- The Resume Match Analyzer uses simple keyword comparison to estimate alignment between a resume and the job posting
