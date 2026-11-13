
import os
import time
from dotenv import load_dotenv
from google import genai


# ============================================================
# 1. CONFIGURATION
# ============================================================

load_dotenv()

MODEL_NAME = "gemini-3.8-flash"

MAX_RETRIES = 3


# ============================================================
# 2. GET GEMINI API KEY
# ============================================================

def get_api_key():

    # First, check environment variables.
    api_key = os.getenv("GEMINI_API_KEY")

    if api_key:
        return api_key

    # Then, check Streamlit Cloud secrets.
    try:
        import streamlit as st

        api_key = st.secrets.get("GEMINI_API_KEY")

        if api_key:
            return api_key

    except Exception:
        pass

    raise ValueError(
        "GEMINI_API_KEY not found. "
        "Add it to your .env file or Streamlit Cloud Secrets."
    )


# ============================================================
# 3. INITIALIZE GEMINI CLIENT
# ============================================================

def get_gemini_client():

    api_key = get_api_key()

    return genai.Client(api_key=api_key)


# ============================================================
# 4. GEMINI CALL WITH AUTOMATIC RETRIES
# ============================================================

def generate_with_retry(prompt, agent_name="Agent"):

    client = get_gemini_client()

    for attempt in range(MAX_RETRIES):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response or not response.text:
                raise ValueError(
                    f"{agent_name} received an empty response from Gemini."
                )

            return response.text.strip()

        except Exception as error:

            error_message = str(error).upper()

            temporary_errors = [
                "503",
                "UNAVAILABLE",
                "429",
                "RESOURCE_EXHAUSTED",
                "500",
                "INTERNAL",
                "502",
                "504"
            ]

            is_temporary = any(
                error_code in error_message
                for error_code in temporary_errors
            )

            if is_temporary and attempt < MAX_RETRIES - 1:

                wait_seconds = 5 * (attempt + 1)

                print(
                    f"{agent_name}: Temporary Gemini error. "
                    f"Retrying in {wait_seconds} seconds..."
                )

                time.sleep(wait_seconds)

            else:

                raise RuntimeError(
                    f"{agent_name} failed after "
                    f"{attempt + 1} attempt(s): {error}"
                ) from error

    raise RuntimeError(
        f"{agent_name} could not complete the request."
    )


# ============================================================
# 5. FORMAT SEARCH RESULTS
# ============================================================

def format_search_results(search_results):

    if not search_results:
        return ""

    formatted_sources = []

    for index, item in enumerate(search_results, start=1):

        if isinstance(item, dict):

            title = (
                item.get("title")
                or item.get("heading")
                or "Untitled source"
            )

            url = (
                item.get("href")
                or item.get("url")
                or item.get("link")
                or "URL not provided"
            )

            description = (
                item.get("body")
                or item.get("snippet")
                or item.get("description")
                or item.get("content")
                or ""
            )

            source_text = (
                f"Source {index}\n"
                f"Title: {title}\n"
                f"URL: {url}\n"
                f"Information: {description}"
            )

        else:

            source_text = f"Source {index}\n{str(item)}"

        formatted_sources.append(source_text)

    return "\n\n".join(formatted_sources)


# ============================================================
# 6. RESEARCHER AGENT
# ============================================================

def researcher_agent(topic, search_results, log_callback=None):

    if log_callback:
        log_callback(
            "Researcher Agent: Extracting factual information..."
        )

    if not search_results:

        return (
            "RESEARCH FAILED\n"
            "No usable search results were provided. "
            "The Writer Agent must not invent facts."
        )

    sources = format_search_results(search_results)

    prompt = f"""
You are the Researcher Agent in a multi-agent system.

YOUR TASK:
Research the user's topic using ONLY the supplied search results.

USER TOPIC:
{topic}

SEARCH RESULTS:
{sources}

INSTRUCTIONS:

1. Extract accurate and relevant factual information.
2. Identify important developments, dates, statistics,
   organizations, technologies, and findings when available.
3. Do not invent facts, statistics, dates, or quotations.
4. Do not use information that is not supported by the sources.
5. If sources disagree, clearly mention the disagreement.
6. Keep the original source titles and URLs.
7. Prefer reliable and authoritative sources.
8. Remove irrelevant search-result information.
9. Organize the research notes using clear headings.
10. Do not write the final blog article.

OUTPUT FORMAT:

# Research Notes

## 1. Topic Overview
Explain the topic using supported information.

## 2. Important Facts
List the important factual findings.

## 3. Recent Developments
Describe recent developments only when supported
by the provided sources.

## 4. Statistics and Evidence
Include statistics only when they appear in the sources.
Mention the source for each statistic.

## 5. Key Findings
Summarize the most important research findings.

## 6. Source References
List the source titles and URLs.

## 7. Research Limitations
Mention missing, unclear, or conflicting information.

IMPORTANT:
Your output will be passed to another AI agent.
The Writer Agent must be able to understand your notes
without accessing the internet.

Return research notes only.
"""

    try:

        research_notes = generate_with_retry(
            prompt,
            agent_name="Researcher Agent"
        )

        if "RESEARCH FAILED" in research_notes.upper():
            return research_notes

        return research_notes

    except Exception as error:

        return (
            "RESEARCH FAILED\n\n"
            f"The Researcher Agent could not complete its task.\n"
            f"Reason: {str(error)}\n\n"
            "The Writer Agent must not invent facts or "
            "write an article using unsupported information."
        )


# ============================================================
# 7. WRITER AGENT
# ============================================================

def writer_agent(topic, research_notes, log_callback=None):

    if log_callback:
        log_callback(
            "Writer Agent: Preparing the blog article..."
        )

    if not research_notes:

        return (
            "The article could not be written because "
            "the Researcher Agent did not provide research notes."
        )

    if "RESEARCH FAILED" in research_notes.upper():

        return (
            "# Article Not Generated\n\n"
            "The Researcher Agent could not complete the research. "
            "The Writer Agent will not invent facts or create "
            "an article without reliable research."
        )

    prompt = f"""
You are the Writer Agent in a multi-agent system.

YOUR TASK:
Write a professional blog article of approximately 500 words.

USER TOPIC:
{topic}

RESEARCH NOTES FROM THE RESEARCHER AGENT:
{research_notes}

IMPORTANT RULES:

1. Use ONLY the research notes provided above.
2. You do NOT have internet access.
3. Do NOT perform web searches.
4. Do NOT invent statistics, dates, events, or facts.
5. Do NOT add unsupported information from your own knowledge.
6. If information is missing, do not make it up.
7. Write in clear, professional, natural English.
8. Avoid unnecessary repetition.
9. Make the article informative and easy to understand.
10. Keep the article approximately 500 words.

ARTICLE STRUCTURE:

# Attractive Blog Title

## Introduction
Introduce the topic and explain its importance.

## Main Developments
Explain the important findings from the research.

## Key Impacts and Applications
Discuss supported real-world effects and applications.

## Challenges and Limitations
Explain challenges mentioned in the research notes.

## Future Outlook
Discuss future possibilities only when supported by
the research notes.

## Conclusion
Provide a clear summary.

## References
List the source titles and URLs supplied by the Researcher.

Return the final article in Markdown format.
Do not include your internal reasoning.
"""

    try:

        article = generate_with_retry(
            prompt,
            agent_name="Writer Agent"
        )

        return article

    except Exception as error:

        return (
            "# Article Generation Failed\n\n"
            "The Writer Agent could not generate the article "
            "because of a temporary or unexpected Gemini error.\n\n"
            f"Error details: {str(error)}"
        )


# ============================================================
# 8. ALTERNATIVE FUNCTION NAMES
# ============================================================
# These aliases allow other project files to call the agents
# using common function names.

run_researcher = researcher_agent
run_writer = writer_agent
research_agent = researcher_agent
write_agent = writer_agent
