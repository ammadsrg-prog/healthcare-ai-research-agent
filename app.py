"""
The web page. Start it with:  streamlit run app.py
"""

import requests
import streamlit as st
from botocore.exceptions import BotoCoreError, ClientError

from src.analyzer import compare_papers
from src.gap_checker import check_gaps
from src.openalex_client import search_papers
from src.report import build_report
from src.summarizer import summarize_paper

# The browser tab's title and icon, and a wide page that uses the whole screen.
# This must be the first Streamlit command in the file.
st.set_page_config(page_title="Healthcare AI Research Agent", page_icon="🩺", layout="wide")

# A little CSS (the language that styles web pages) for the coloured banner at the top.
st.markdown(
    """
    <style>
    .hero {
        background: linear-gradient(135deg, #0F766E 0%, #0EA5E9 100%);
        color: white;
        padding: 1.6rem 2rem;
        border-radius: 1rem;
        margin-bottom: 1.2rem;
    }
    .hero h1 { color: white; margin: 0; padding: 0; font-size: 2rem; }
    .hero p { color: #E0F2F1; margin: 0.4rem 0 0 0; font-size: 1.05rem; }
    </style>
    <div class="hero">
        <h1>🩺 Healthcare AI Research Agent</h1>
        <p>Find healthcare papers, summarize them with PICO, and check which research gaps are real.</p>
    </div>
    """,
    unsafe_allow_html=True,  # Allows our own HTML. Only ever used for our fixed text, never for paper data.
)

# The sidebar on the left: what the app does, and the safety note.
with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. **Search** healthcare papers from OpenAlex\n"
        "2. **Summarize** papers in PICO format\n"
        "3. **Compare** the summarized papers\n"
        "4. **Check gaps** against real research\n"
        "5. **Download** a report with real references"
    )
    st.divider()
    st.caption(
        "Searches healthcare research only. A tool for studying research, not medical advice. "
        "AI summaries can contain mistakes, so check the original paper."
    )
    st.caption("Papers: OpenAlex · AI: Amazon Bedrock")

# Streamlit re-runs this whole file after every click, so we keep
# results in session_state or they would disappear from the page.
if "papers" not in st.session_state:
    st.session_state.papers = []
    st.session_state.summaries = {}
if "topic" not in st.session_state:
    st.session_state.topic = ""
if "comparison" not in st.session_state:
    st.session_state.comparison = None
if "gaps" not in st.session_state:
    st.session_state.gaps = None

# A form groups the inputs, so pressing Enter in the text box also starts the search.
with st.form("search_form", border=True):
    search_column, limit_column = st.columns([4, 1])
    topic = search_column.text_input(
        "What healthcare topic do you want to research?",
        placeholder="e.g. diabetes mobile app",
    )
    limit = limit_column.number_input("Papers", min_value=1, max_value=25, value=10)
    searched = st.form_submit_button("Search papers", icon=":material/search:", type="primary")

if searched and topic:
    try:
        with st.spinner("Searching OpenAlex..."):
            st.session_state.papers = search_papers(topic, limit)
        st.session_state.topic = topic  # Saved for the report, because the text box can change later
        st.session_state.summaries = {}
        st.session_state.comparison = None
        st.session_state.gaps = None
    except requests.RequestException:
        st.error("Could not reach OpenAlex. Please wait a moment and try again.")
        st.stop()

    if not st.session_state.papers:
        st.info("No papers found. Try different words.")

if not st.session_state.papers:
    st.info("Type a healthcare topic above and click **Search papers** to begin.", icon=":material/lightbulb:")
    st.stop()  # Nothing else to show yet

summarized = sorted(st.session_state.summaries)

# Three numbers at a glance
papers_metric, summaries_metric, gaps_metric = st.columns(3)
papers_metric.metric("Papers found", len(st.session_state.papers))
summaries_metric.metric("Summarized", len(summarized))
gaps_metric.metric("Gaps checked", len(st.session_state.gaps) if st.session_state.gaps else 0)

# Tabs keep the page tidy: one tab for each job.
papers_tab, compare_tab, gaps_tab, report_tab = st.tabs(
    [
        ":material/article: Papers",
        ":material/compare_arrows: Compare",
        ":material/troubleshoot: Research gaps",
        ":material/description: Report",
    ]
)

with papers_tab:
    for index, paper in enumerate(st.session_state.papers):
        # A bordered container draws each paper as a card
        with st.container(border=True):
            st.subheader(paper.title)

            # Show only the first 3 authors, so long author lists don't fill the card
            authors = ", ".join(paper.authors[:3]) or "Unknown authors"
            if len(paper.authors) > 3:
                authors += " et al."
            st.caption(f"📅 {paper.year or 'Year unknown'}  ·  📈 Cited by {paper.citation_count}  ·  👥 {authors}")

            with st.expander("Read abstract"):
                st.write(paper.abstract or "No abstract available.")

            # Each summary costs money, so we only ask the AI when the button is
            # clicked, and we keep the answer so the same paper is never paid for twice.
            if index in st.session_state.summaries:
                st.success("AI summary (PICO)", icon=":material/auto_awesome:")
                st.markdown(st.session_state.summaries[index])

            open_column, summarize_column, _ = st.columns([1, 1, 3])
            if paper.url:
                open_column.link_button("Open paper", paper.url, icon=":material/open_in_new:")

            if index in st.session_state.summaries:
                pass  # Already summarized, so no button
            elif not paper.abstract:
                summarize_column.caption("No abstract to summarize.")
            elif summarize_column.button("Summarize", key=f"summarize_{index}", icon=":material/auto_awesome:"):
                try:
                    with st.spinner("The AI is reading the abstract..."):
                        st.session_state.summaries[index] = summarize_paper(paper)
                    # A new summary makes the old comparison and gaps out of date
                    st.session_state.comparison = None
                    st.session_state.gaps = None
                    st.rerun()
                except (ClientError, BotoCoreError):
                    st.error("Could not reach the AI. Please wait a moment and try again.")
                except ValueError:
                    st.error("The AI's answer was incomplete. Please click Summarize again.")

with compare_tab:
    if st.session_state.comparison:
        with st.container(border=True):
            st.markdown(st.session_state.comparison)
        st.caption("Paper numbers match the summarized papers, in order from the top of the Papers tab.")
    elif len(summarized) < 2:
        st.info(f"Summarize at least 2 papers in the Papers tab to compare them. You have {len(summarized)} so far.")
    elif st.button(f"Compare {len(summarized)} summarized papers", type="primary", icon=":material/compare_arrows:"):
        try:
            with st.spinner("The AI is comparing the papers..."):
                st.session_state.comparison = compare_papers(
                    [st.session_state.papers[i] for i in summarized],
                    [st.session_state.summaries[i] for i in summarized],
                )
            st.rerun()
        except (ClientError, BotoCoreError):
            st.error("Could not reach the AI. Please wait a moment and try again.")
        except ValueError:
            st.error("The AI's answer was incomplete. Please click Compare again.")

with gaps_tab:
    st.caption(
        "The AI suggests gaps, then we search OpenAlex to see if papers already cover them. "
        "This is a strong hint, not proof: papers that use different words can be missed."
    )

    if st.session_state.gaps:
        for gap in st.session_state.gaps:
            with st.container(border=True):
                st.markdown(f"#### {gap['verdict']}")
                st.markdown(gap["gap"])
                st.caption(f"🔎 Searched for: `{gap['search']}`  ·  Healthcare papers found: **{gap['count']}**")
                if gap["examples"]:
                    with st.expander("Example papers"):
                        for example in gap["examples"]:
                            st.markdown(f"- [{example.title}]({example.url}) ({example.year or 'year unknown'})")
    elif len(summarized) < 2:
        st.info("Summarize at least 2 papers in the Papers tab to check for gaps.")
    elif st.button(
        f"Find and check gaps in {len(summarized)} summarized papers", type="primary", icon=":material/troubleshoot:"
    ):
        try:
            with st.spinner("The AI is suggesting gaps, then we search for each one..."):
                st.session_state.gaps = check_gaps(
                    [st.session_state.papers[i] for i in summarized],
                    [st.session_state.summaries[i] for i in summarized],
                )
            st.rerun()
        except (ClientError, BotoCoreError):
            st.error("Could not reach the AI. Please wait a moment and try again.")
        except requests.RequestException:
            st.error("Could not reach OpenAlex to check the gaps. Please wait a moment and try again.")
        except ValueError:
            st.error("The AI's answer could not be read. Please click the button again.")

with report_tab:
    if not summarized:
        st.info("Summarize at least 1 paper in the Papers tab to make a report.")
    else:
        # Built fresh on every rerun from saved results. No AI is used, so it's free.
        report = build_report(
            st.session_state.topic,
            [st.session_state.papers[i] for i in summarized],
            [st.session_state.summaries[i] for i in summarized],
            st.session_state.comparison,
            st.session_state.gaps,
        )

        # Tell the user which parts are missing, so they can add them first if they want
        if not st.session_state.comparison or not st.session_state.gaps:
            st.caption("Tip: run Compare and Research gaps first to include them in the report.")

        # Turn the topic into a safe file name, like "diabetes-mobile-app-report.md"
        file_name = "-".join("".join(c for c in st.session_state.topic.lower() if c.isalnum() or c == " ").split())
        st.download_button(
            "Download report (.md)",
            data=report,
            file_name=f"{file_name or 'research'}-report.md",
            mime="text/markdown",
            type="primary",
            icon=":material/download:",
        )

        with st.container(border=True):
            st.markdown(report)  # A preview of the report on the page
