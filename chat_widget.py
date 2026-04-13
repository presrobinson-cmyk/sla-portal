"""
SLA Portal — AI Chat Widget
Reusable chat component powered by Claude. Import and call render_chat() on any page.
Uses Streamlit's native chat UI (st.chat_input / st.chat_message).
Requires ANTHROPIC_API_KEY in Streamlit secrets.
"""

import streamlit as st
import requests
import json

from theme import (
    NAVY, GOLD, GOLD_MID, CARD_BG, TEXT1, TEXT2, TEXT3, BORDER2, BG,
    get_supabase_config, get_supabase_headers, CJ_SURVEYS, SURVEY_STATE,
)


# ── System prompt for the AI ──
SYSTEM_PROMPT = """You are the Second Look Alliance research assistant embedded in a criminal justice reform data portal.
You help advocates, funders, and media professionals understand polling data about criminal justice reform.

Your knowledge base:
- Survey data from 6 states: Oklahoma, Louisiana, North Carolina, Virginia, Massachusetts, New Jersey
- Topics include: public defender funding, community investment, bail reform, sentence review, record expungement, domestic violence policy, fines & fees, juvenile justice, and more
- Voter segments range from reform skeptics (bottom 20%) to reform champions (top 20%)
- Persuasion architecture: Entry tier (easiest sells) → Bridge (domestic violence wedge) → Downstream (policy payload) → Destination (hardest asks)

Guidelines:
- Use plain English. Never use internal codes like PD_FUNDING, BH, CB, Q1, Q5, MrP
- Refer to voter segments as "reform skeptics," "movable middle," "reform-leaning," and "reform champions"
- When citing numbers, say "support rate" not "favorability score"
- Be concise and actionable — these users want strategic insight, not methodology lectures
- If you don't know something specific, say so rather than guessing
- You're speaking to professionals: advocates, funders, journalists. Be direct.
"""

# Page-specific context additions
PAGE_CONTEXT = {
    "home": "The user is on the Home page viewing the US state map and navigation overview.",
    "issue_landscape": "The user is on the Issue Landscape page — a scatter plot showing reform topics by reach (how many people support it) and universality (whether support holds across voter segments). Topics in the upper-right are strongest.",
    "voter_segments": "The user is on the Voter Segments page — disposition-based quintile analysis of reform attitudes.",
    "persuasion_pathways": "The user is on the Persuasion Pathways page — topics organized into persuasion tiers (Entry → Bridge → Downstream → Destination). Each topic expands to show individual survey angles with support rates.",
    "cross_state": "The user is on the Cross-State Comparison page — side-by-side state-level data for the same reform topics.",
    "mediamaker": "The user is on the MediaMaker page — tools for generating media-ready content from the data.",
    "surveymaker": "The user is on the SurveyMaker page — tools for designing new survey instruments.",
    "ai_analysis": "The user is on the AI Analysis page — the dedicated analysis interface.",
    "state_report": "The user is on a State Report page — detailed breakdown of reform support for a specific state, with topic-level scores and individual question results.",
}


def _get_api_key():
    """Get Anthropic API key from secrets."""
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if key:
            return key
    except Exception:
        pass
    return ""


def _call_claude(messages: list, page_context: str = "") -> str:
    """Call the Anthropic Messages API directly via requests."""
    api_key = _get_api_key()
    if not api_key:
        return "AI chat is not yet configured. An API key needs to be added to the portal settings."

    system = SYSTEM_PROMPT
    if page_context:
        system += f"\n\nCurrent page context: {page_context}"

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": system,
        "messages": messages,
    }

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        # Extract text from content blocks
        text_parts = []
        for block in data.get("content", []):
            if block.get("type") == "text":
                text_parts.append(block["text"])
        return "\n".join(text_parts) if text_parts else "No response generated."
    except requests.exceptions.Timeout:
        return "The request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            return "AI chat API key is invalid. Please contact the portal administrator."
        return f"An error occurred connecting to the AI service. Please try again."
    except Exception as e:
        return "AI chat encountered an unexpected error. Please try again."


def _chat_css():
    """Inject CSS for the chat widget styling."""
    st.markdown(f"""
    <style>
        /* Chat container styling */
        .chat-header {{
            background: linear-gradient(135deg, {NAVY} 0%, #1a3260 100%);
            color: #e8e8ed;
            padding: 0.75rem 1rem;
            border-radius: 10px;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .chat-header-title {{
            font-family: 'Playfair Display', serif;
            font-weight: 700;
            font-size: 0.95rem;
            color: #ffffff;
        }}
        .chat-header-sub {{
            font-size: 0.72rem;
            color: #8b8fa3;
        }}
        .chat-suggestion {{
            background: rgba(184,135,10,0.08);
            border: 1px solid rgba(184,135,10,0.2);
            border-radius: 20px;
            padding: 0.5rem 1rem;
            font-size: 0.82rem;
            color: {NAVY};
            cursor: pointer;
            transition: all 0.15s ease;
            text-align: center;
        }}
        .chat-suggestion:hover {{
            background: rgba(184,135,10,0.15);
            border-color: {GOLD_MID};
        }}

        /* Make chat input box visible against light background */
        [data-testid="stChatInput"] {{
            background: {CARD_BG} !important;
            border: 2px solid {BORDER2} !important;
            border-radius: 10px !important;
        }}
        [data-testid="stChatInput"] textarea {{
            color: {TEXT1} !important;
            background: {CARD_BG} !important;
        }}
        [data-testid="stChatInput"] textarea::placeholder {{
            color: {TEXT3} !important;
        }}
        /* Chat message styling */
        [data-testid="stChatMessage"] {{
            background: {CARD_BG} !important;
            border: 1px solid {BORDER2} !important;
            border-radius: 10px !important;
        }}
    </style>
    """, unsafe_allow_html=True)


# Starter questions per page
STARTER_QUESTIONS = {
    "home": [
        "What states have the strongest reform support?",
        "Give me the 30-second overview of our data",
        "What should I look at first?",
    ],
    "issue_landscape": [
        "Which issues are strongest across all voter types?",
        "What topics only work with reform supporters?",
        "Which issues should we lead with in messaging?",
    ],
    "voter_segments": [
        "How big is the movable middle?",
        "What do reform skeptics actually agree with?",
        "How different are the top and bottom segments?",
    ],
    "persuasion_pathways": [
        "Explain the Entry → Bridge → Downstream sequence",
        "Why does domestic violence work as a bridge?",
        "Which downstream topics unlock first?",
    ],
    "cross_state": [
        "Which state is most receptive to reform?",
        "Are there issues that work in every state?",
        "What are the biggest state-to-state differences?",
    ],
    "mediamaker": [
        "Help me write a headline about public defender funding",
        "What data point would grab a reporter's attention?",
        "Draft a one-paragraph summary for a press release",
    ],
    "surveymaker": [
        "What topics haven't been tested enough?",
        "Which states need more data?",
        "Suggest questions for a new survey",
    ],
    "ai_analysis": [
        "Which messages are safe to use everywhere?",
        "Explain the persuasion pathway in plain English",
        "What should we tell funders about these results?",
    ],
    "state_report": [
        "What are the strongest topics in this state?",
        "Any surprising results here?",
        "How does this state compare to the national picture?",
    ],
}


def render_chat(page_key: str = "home"):
    """
    Render the AI chat widget. Call this on every page.

    Args:
        page_key: One of the keys in PAGE_CONTEXT / STARTER_QUESTIONS
    """
    _chat_css()

    # Initialize chat history in session state (shared across pages)
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    st.divider()

    # Chat header
    st.markdown("""
    <div class="chat-header">
        <div style="font-size:1.3rem;">💬</div>
        <div>
            <div class="chat-header-title">Ask the Data</div>
            <div class="chat-header-sub">AI-powered research assistant · Ask anything about the polling data</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show starter suggestions if no messages yet
    starters = STARTER_QUESTIONS.get(page_key, STARTER_QUESTIONS["home"])
    if not st.session_state.chat_messages:
        cols = st.columns(len(starters))
        for i, (col, q) in enumerate(zip(cols, starters)):
            with col:
                if st.button(q, key=f"starter_{page_key}_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": q})
                    # Get AI response
                    context = PAGE_CONTEXT.get(page_key, "")
                    api_messages = [{"role": m["role"], "content": m["content"]}
                                    for m in st.session_state.chat_messages]
                    response = _call_claude(api_messages, context)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    st.rerun()

    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask about the data...", key=f"chat_input_{page_key}"):
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        context = PAGE_CONTEXT.get(page_key, "")
        api_messages = [{"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_messages]
        response = _call_claude(api_messages, context)

        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

    # Clear chat button (small, at the bottom)
    if st.session_state.chat_messages:
        col1, col2, col3 = st.columns([4, 1, 4])
        with col2:
            if st.button("Clear chat", key=f"clear_{page_key}", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
