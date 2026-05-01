"""
AI Job Agent - AI Resume Rewriter
Uses OpenAI GPT-4o to tailor your resume for each job description.
"""

import logging
from typing import Dict

from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """You are an expert resume writer and ATS (Applicant Tracking System) specialist.

The candidate is a Python backend developer with 4 years of experience in Django and Django REST Framework,
targeting remote roles at tech startups and e-commerce companies in the US, Canada, and Saudi Arabia.
They are specifically interested in roles involving AI integrations, agentic AI, LLM tooling, and API development.

Your task is to rewrite their resume to maximally match the provided job description.

Rules you MUST follow:
1. Do NOT invent facts, companies, dates, metrics, or skills the candidate doesn't have.
2. Every bullet point must start with a strong action verb (Built, Designed, Integrated, Optimised, Led, etc.).
3. Mirror the exact keywords and terminology from the job description — especially any AI/ML/LLM terms.
4. If the role mentions AI integrations, LLMs, or agentic workflows AND the candidate has relevant experience,
   surface and highlight those experiences prominently.
5. Keep all truthful achievements intact — rephrase to align with the role's language.
6. Maintain professional formatting: clear sections (Summary, Experience, Skills, Education).
7. Output plain text only — no markdown, no bullet symbols like *, just plain dashes (-) for bullets.
8. The output must be ATS-friendly: no tables, no columns, no special characters.
9. Rewrite the Summary section to speak directly to this specific role and company.
10. Reorder Skills to put the most relevant ones for this job first.
11. Keep the resume concise — ideally 1 page worth of content.
12. For remote roles: do NOT add location requirements to the candidate's profile.
"""


def rewrite_resume_for_job(
    resume_text: str,
    job: Dict,
    model: str = OPENAI_MODEL,
) -> str:
    """
    Use GPT-4o to rewrite a resume tailored to a specific job.

    Args:
        resume_text: Raw text of the candidate's resume.
        job: Dict with keys: title, company, description, location, job_url, date_posted

    Returns:
        Rewritten resume as plain text.
    """
    job_title = job.get("title", "")
    company = job.get("company", "")
    job_description = job.get("description", "")

    user_message = f"""
Here is the candidate's current resume:

--- RESUME START ---
{resume_text}
--- RESUME END ---

Here is the job description they are applying to:

--- JOB DESCRIPTION START ---
Company: {company}
Role: {job_title}

{job_description}
--- JOB DESCRIPTION END ---

Please rewrite the resume to be perfectly tailored for this role.
Remember: do not invent anything. Every fact must come from the original resume.
Output ONLY the rewritten resume text with no additional commentary.
"""

    logger.info(f"Rewriting resume for: {job_title} @ {company} ...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.4,
            max_tokens=2000,
        )

        rewritten = response.choices[0].message.content.strip()
        logger.info(f"  ✓ Resume rewritten ({len(rewritten)} chars)")
        return rewritten

    except Exception as e:
        logger.error(f"OpenAI API error for '{job_title} @ {company}': {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Quick test with dummy data
    sample_resume = """
John Doe
john@example.com | linkedin.com/in/johndoe

SUMMARY
Experienced software engineer with 5 years building scalable web applications.

EXPERIENCE
Software Engineer — Acme Corp (2020–Present)
- Built REST APIs serving 1M+ requests/day using Python and FastAPI
- Led migration from monolith to microservices, reducing latency by 40%
- Mentored 3 junior engineers

SKILLS
Python, FastAPI, Docker, Kubernetes, PostgreSQL, AWS, React

EDUCATION
B.S. Computer Science — State University, 2019
"""

    sample_job = {
        "title": "Senior Backend Engineer",
        "company": "TechStartup",
        "description": "We need a Python expert to build scalable APIs. Experience with FastAPI, Docker, and AWS required. Must have mentorship experience.",
        "location": "Remote",
        "job_url": "https://linkedin.com/jobs/view/123",
        "date_posted": "2026-04-08",
    }

    result = rewrite_resume_for_job(sample_resume, sample_job)
    print("\n" + "="*60)
    print("REWRITTEN RESUME:")
    print("="*60)
    print(result)
