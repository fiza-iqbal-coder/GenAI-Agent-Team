
import time
from google import genai


# ============================================================
# 1. MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "gemini-3.8-flash"

MAX_RETRIES = 3


# ============================================================
# 2. SHARED GEMINI GENERATION FUNCTION
# ============================================================

def generate_with_retry(client, prompt, agent_name):

    for attempt in range(MAX_RETRIES):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            if not response or not response.text:
                raise ValueError("Gemini returned an empty response.")

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
                code in error_message
                for code in temporary_errors
            )

            if is_temporary and attempt < MAX_RETRIES - 1:

                wait_seconds = 5 * (attempt + 1)

                print(
                    f"{agent_name}: Temporary Gemini error. "
                    f"Retrying in {wait_seconds} seconds...",
                    flush=True
                )

                time.sleep(wait_seconds)

            else:

                raise RuntimeError(
                    f"{agent_name} failed: {error}"
                ) from error

    raise RuntimeError(
        f"{agent_name} could not complete the request."
    )


# ============================================================
# 3. FORMAT RESEARCH SOURCES
# ============================================================

def format_sources(sources):

    formatted = []

    for index, source in enumerate(sources, start=1):

        if isinstance(source, dict):

            title = (
                source.get("title")
                or source.get("heading")
                or "Untitled source"
            )

            url = (
                source.get("href")
                or source.get("url")
                or source.get("link")
                or "URL unavailable"
            )

            description = (
                source.get("body")
                or source.get("snippet")
                or source.get("description")
                or source.get("content")
                or ""
            )

            formatted.append(
                f"""
Source {index}
Title: {title}
URL: {url}
Information: {description}
"""
            )

        else:

            formatted.append(
                f"Source {index}: {str(source)}"
            )

    return "\n\n".join(formatted)


# ============================================================
# 4. RESEARCHER AGENT
# ============================================================

class ResearcherAgent:
    """
    Researcher Agent:
    Extracts factual information from supplied web sources.
    """

    def __init__(self, client):

        self.client = client

    def compile_research(self, topic, sources):

        if not sources:

            return (
                "RESEARCH FAILED: "
                "No usable search sources were provided."
            )

        source_information = format_sources(sources)

        prompt = f"""
You are the Researcher Agent in a multi-agent system.

Your responsibility is to collect and organize factual
information for the Writer Agent.

USER TOPIC:
{topic}

SEARCH RESULTS:
{source_information}

YOUR TASK:

1. Extract relevant factual information.
2. Identify important developments and findings.
3. Include dates and statistics only when supported.
4. Do not invent facts or statistics.
5. Identify the organizations and technologies mentioned.
6. Preserve source titles and URLs.
7. Mention conflicting information when sources disagree.
8. Do not write the final blog article.
9. Do not use information outside the supplied sources.

OUTPUT FORMAT:

# Research Notes

## 1. Topic Overview

## 2. Important Facts

## 3. Recent Developments

## 4. Statistics and Evidence

## 5. Key Findings

## 6. Source References

## 7. Research Limitations

Your research notes will be passed to the Writer Agent.
Make them clear, factual, and well organized.

Return only the research notes.
"""

        try:

            research = generate_with_retry(
                self.client,
                prompt,
                "Researcher Agent"
            )

            return research

        except Exception as error:

            print(
                f"Researcher Agent Error: {error}",
                flush=True
            )

            return (
                "RESEARCH FAILED\n\n"
                "The Researcher Agent could not complete "
                "the research because Gemini was unavailable.\n\n"
                f"Error: {error}\n\n"
                "The Writer Agent must not invent facts."
            )


# ============================================================
# 5. WRITER AGENT
# ============================================================

class WriterAgent:
    """
    Writer Agent:
    Creates a professional blog using only research notes.
    It does not perform internet searches.
    """

    def __init__(self, client):

        self.client = client

    def write_article(self, topic, research):

        if not research:

            return (
                "# Article Not Generated\n\n"
                "The Researcher Agent did not provide "
                "research notes."
            )

        if "RESEARCH FAILED" in research.upper():

            return (
                "# Article Not Generated\n\n"
                "The Researcher Agent could not complete "
                "the research. Therefore, the Writer Agent "
                "will not invent facts or generate an "
                "unsupported article."
            )

        prompt = f"""
You are the Writer Agent in a multi-agent system.

Your task is to write a professional blog article
of approximately 500 words.

TOPIC:
{topic}

RESEARCH NOTES PROVIDED BY THE RESEARCHER:
{research}

IMPORTANT RULES:

1. Use only the research notes above.
2. You do not have internet access.
3. Do not perform web searches.
4. Do not invent facts, dates, statistics, or events.
5. Do not add unsupported information.
6. Write in professional and natural English.
7. Avoid unnecessary repetition.
8. Make the article informative and readable.
9. Target approximately 500 words.
10. If information is missing, do not make it up.

ARTICLE STRUCTURE:

# Attractive Blog Title

## Introduction

Introduce the topic and explain its importance.

## Main Developments

Explain important research findings.

## Real-World Impacts and Applications

Discuss supported real-world applications.

## Challenges and Limitations

Explain challenges found in the research.

## Future Outlook

Discuss future possibilities only when supported
by the research notes.

## Conclusion

Summarize the main points.

## References

Include source titles and URLs from the research notes.

Return the final article in Markdown format.
Do not include your internal reasoning.
"""

        try:

            article = generate_with_retry(
                self.client,
                prompt,
                "Writer Agent"
            )

            return article

        except Exception as error:

            print(
                f"Writer Agent Error: {error}",
                flush=True
            )

            return (
                "# Article Generation Failed\n\n"
                "The Writer Agent could not generate "
                "the article after multiple attempts.\n\n"
                f"Error: {error}"
            )
