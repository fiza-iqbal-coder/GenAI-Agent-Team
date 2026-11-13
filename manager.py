import os
from dotenv import load_dotenv
from google import genai

from agents import ResearcherAgent, WriterAgent
from search_tool import web_search

load_dotenv()


class ManagerAgent:
    """Controls the fixed, sequential Researcher -> Writer workflow."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        # Streamlit Community Cloud stores secrets in st.secrets, not necessarily
        # as operating-system environment variables.
        if not api_key:
            try:
                import streamlit as st
                api_key = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                api_key = None

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is missing. Add it to your local .env file "
                "or to Streamlit Cloud > App settings > Secrets."
            )

        self.client = genai.Client(api_key=api_key)
        self.researcher = ResearcherAgent(self.client)
        self.writer = WriterAgent(self.client)

    def run(self, topic, status=None):
        # Task 1: Research
        self._log(status, "Manager: Task 1 assigned — Research the user's topic.")
        self._log(status, "Researcher Agent: Searching the web with DuckDuckGo...")

        try:
            sources = web_search(topic, max_results=8)
        except Exception as exc:
            self._log(status, f"Researcher Agent: Web search failed — {exc}")
            sources = []

        self._log(status, f"Researcher Agent: Search finished. {len(sources)} usable source(s) found.")
        self._log(status, "Researcher Agent: Extracting factual notes from the search results...")

        if sources:
            research = self.researcher.compile_research(topic, sources)
        else:
            research = "RESEARCH FAILED: DuckDuckGo did not return usable search results."

        self._log(status, "Manager: Research handoff received.")
        self._log(status, "Manager: Passing the complete research notes to the Writer Agent.")

        # Task 2: Write
        self._log(status, "Writer Agent: Drafting the approximately 500-word Markdown article...")
        article = self.writer.write_article(topic, research)
        self._log(status, "Writer Agent: Draft completed.")

        return {
            "research": research,
            "article": article,
            "sources": sources
        }

    @staticmethod
    def _log(status, message):
        print(message, flush=True)
        if status is not None:
            status.write(message)


def run_workflow(topic, status=None):
    manager = ManagerAgent()
    return manager.run(topic, status=status)
