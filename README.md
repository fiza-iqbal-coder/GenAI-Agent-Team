# GenAI-Agent-Team — Week 6

A sequential multi-agent system built with Python, Gemini, DuckDuckGo Search, and Streamlit.

## Agents

1. **Manager Agent:** controls the workflow and passes data between agents.
2. **Researcher Agent:** searches the web and extracts factual notes from the returned search results.
3. **Writer Agent:** creates an approximately 500-word Markdown blog using only the research handoff. It has no search tool.

## Workflow

User topic -> Manager -> Researcher -> Raw research notes -> Manager handoff -> Writer -> Markdown blog

The workflow runs once, sequentially. There is no agent-to-agent loop.

## Setup

1. Install Python 3.10 or newer.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:

   Windows PowerShell:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Copy `.env.example` to `.env`.
6. Add your Gemini API key in `.env`:

   ```env
   GEMINI_API_KEY=your_actual_key
   ```

7. Run the application:

   ```powershell
   streamlit run app.py
   ```

## Streamlit Cloud deployment

1. Push this project to a new GitHub repository named `GenAI-Agent-Team`.
2. Create a Streamlit Community Cloud app connected to that repository.
3. Set the main file path to `app.py`.
4. In Streamlit app settings, open Secrets and add:

   ```toml
   GEMINI_API_KEY = "your_actual_key"
   ```

5. Save secrets and allow the app to restart.

Do not upload `.env` or publish your API key.

## Troubleshooting log

### 1. Agent loops
**Risk:** Agents may repeatedly send tasks to one another without completing the workflow.

**Control:** The Manager uses a fixed sequence: one research task followed by one writing task. There is no recursive delegation, retry loop, or agent debate.

### 2. Context overflow
**Risk:** Too many search results or excessively long research notes can exceed the model context limit.

**Control:** The Researcher receives at most eight search results. The Writer receives only the research notes for the requested topic, not the entire conversation or unrelated history.

### 3. Research failure
**Risk:** Search may return no usable results or the search service may be unavailable.

**Control:** The Manager passes an explicit `RESEARCH FAILED` message. The Writer is instructed not to invent facts and instead reports that research could not be completed.

### 4. Unsupported claims
**Risk:** An LLM may generate details that are not supported by search snippets.

**Control:** The Researcher is instructed to use only supplied search results and retain URLs. The Writer is instructed to use only the Researcher handoff. Search snippets are evidence leads, not guaranteed verification; important claims should be checked against the linked sources.

### 5. API and deployment errors
- Confirm `GEMINI_API_KEY` is set correctly.
- Confirm all packages in `requirements.txt` are installed.
- Check that Streamlit Cloud Secrets use valid TOML syntax.
- Check the Streamlit logs if the app fails to start.

## Project files

- `app.py` — Streamlit user interface
- `manager.py` — orchestration and state handoff
- `agents.py` — Researcher and Writer personas
- `search_tool.py` — DuckDuckGo search integration
- `requirements.txt` — dependencies
- `.env.example` — environment variable template
