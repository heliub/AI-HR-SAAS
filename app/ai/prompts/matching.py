"""
Matching prompt templates
"""

MATCHING_PROMPT = """You are an expert HR recruiter. Analyze the following job requirements and candidate resume to determine if they are a good match.

Job Requirements:
{job_requirements}

Candidate Resume:
{resume_data}

Evaluate the match based on:
1. Required skills and experience
2. Educational background
3. Work experience relevance
4. Cultural fit indicators

Provide:
- score: 0-100 numerical score
- result: excellent (>80), good (60-80), fair (40-60), or poor (<40)
- reasoning: detailed explanation of the match assessment
- details: specific points about skills match, experience, gaps, etc.

Return a JSON response with these fields.
"""


BATCH_MATCHING_PROMPT = """Analyze multiple candidate resumes against the given job requirements.

Job Requirements:
{job_requirements}

Candidates:
{candidates_data}

For each candidate, provide a match assessment with score, result, and reasoning.
Return JSON array with results for each candidate.
"""

