from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.8-flash"


class ResearcherAgent:
    """Searches the web and converts search snippets into evidence-based research notes."""

    SYSTEM_PROMPT = """
You are the Researcher Agent in a multi-agent system.
Your only responsibility is to collect and organize factual information from the
provided web-search results.

Rules:
- Use ONLY the supplied search results.
- Do not add facts from your own memory.
- Do not write a blog post, introduction, conclusion, or opinion.
- Do not invent dates, numbers, quotations, or source details.
- If the results do not contain enough evidence, clearly say so.
- Keep source URLs beside the facts they support.
- Return concise factual research notes, not a polished article.
"""

    def __init__(self, client):
        self.client = client

    def compile_research(self, topic, search_results):
        if not search_results:
            return "RESEARCH FAILED: The web search returned no results. No factual research can be provided."

        formatted_results = []
        for i, item in enumerate(search_results, start=1):
            formatted_results.append(
                f"RESULT {i}\n"
                f"Title: {item.get('title', 'Untitled')}\n"
                f"URL: {item.get('url', '')}\n"
                f"Search snippet: {item.get('snippet', '')}\n"
            )

        prompt = (
            f"Research topic: {topic}\n\n"
            "Extract factual notes supported by the search results below. "
            "Include source URLs with relevant facts. If evidence is insufficient, say so.\n\n"
            + "\n".join(formatted_results)
        )

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_PROMPT,
                temperature=0.2
            )
        )
        return response.text or "RESEARCH FAILED: The Researcher returned an empty response."


class WriterAgent:
    """Writes a blog using only the research handoff; it has no search capability."""

    SYSTEM_PROMPT = """
You are the Writer Agent in a professional content team.
You do not have internet access or search tools. You must use only the research
notes supplied by the Manager.

Rules:
- Write a professional, clear Markdown blog post of approximately 500 words.
- Use a suitable title, introduction, descriptive headings, and conclusion.
- Do not invent facts, statistics, dates, quotations, or sources.
- Keep claims consistent with the supplied research.
- Include source links in a short Sources section when URLs are provided.
- If the research says it failed, or contains insufficient evidence, do NOT write
  a factual article. Instead, clearly report that research failed and explain
  that more reliable source material is needed.
- Never pretend that you independently verified information.
"""

    def __init__(self, client):
        self.client = client

    def write_article(self, topic, research_notes):
        if research_notes.strip().startswith("RESEARCH FAILED:"):
            return (
                f"# Research Could Not Be Completed: {topic}\n\n"
                "The Researcher Agent could not collect usable web information for this topic. "
                "To avoid inventing facts, the Writer Agent has not generated a factual blog post. "
                "Please try again with a more specific topic or check the internet connection."
            )

        prompt = (
            f"Topic: {topic}\n\n"
            "Research handoff from the Researcher Agent:\n"
            "--------------------------------------------\n"
            f"{research_notes}\n"
            "--------------------------------------------\n\n"
            "Write the requested approximately 500-word Markdown blog post using only this handoff."
        )

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self.SYSTEM_PROMPT,
                temperature=0.5
            )
        )
        return response.text or "The Writer Agent returned an empty response."
