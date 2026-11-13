import streamlit as st
from manager import run_workflow

st.set_page_config(
    page_title="GenAI Agent Team",
    page_icon="🤝",
    layout="wide"
)

st.title("GenAI Agent Team")
st.caption("A multi-agent research and blog-writing system powered by Gemini and DuckDuckGo.")

with st.sidebar:
    st.header("About this project")
    st.write("The Manager delegates research to the Researcher, then passes the collected evidence to the Writer.")
    st.markdown("**Agents**")
    st.write("1. Manager / Router")
    st.write("2. Researcher — web search")
    st.write("3. Writer — blog generation")
    st.divider()
    st.caption("The Writer does not have access to web-search tools.")

topic = st.text_input(
    "Enter a topic to research",
    placeholder="Example: Latest developments in artificial intelligence in 2026"
)
run_button = st.button("Research and write blog", type="primary", use_container_width=True)

if run_button:
    if not topic.strip():
        st.warning("Please enter a research topic.")
    else:
        log_area = st.container()
        with st.status("Manager is starting the agent workflow...", expanded=True) as status:
            try:
                result = run_workflow(topic.strip(), status=st)
                status.update(label="All agents completed successfully.", state="complete", expanded=False)

                st.subheader("Final blog post")
                st.markdown(result["article"])

                st.download_button(
                    "Download blog as Markdown",
                    data=result["article"],
                    file_name="research_blog.md",
                    mime="text/markdown"
                )

                st.subheader("Research sources")
                for index, source in enumerate(result["sources"], start=1):
                    st.markdown(f"{index}. [{source['title']}]({source['url']})")
                    if source.get("snippet"):
                        st.caption(source["snippet"])

                with st.expander("View raw research handoff"):
                    st.text(result["research"])
            except Exception as exc:
                status.update(label="Workflow failed.", state="error", expanded=True)
                st.error(str(exc))
                st.info("Check your API key, internet connection, and terminal logs.")
