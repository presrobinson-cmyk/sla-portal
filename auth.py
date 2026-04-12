"""
Authentication module for Actionable Intel & SLA Portal
Individual user accounts with password hashing.
Accounts stored in Streamlit secrets for simplicity.
"""

import streamlit as st
import hashlib
import time


def hash_password(password: str) -> str:
    """Hash a password with SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_credentials(username: str, password: str, user_store: dict) -> bool:
    """Verify username/password against the user store."""
    if username in user_store:
        return user_store[username] == hash_password(password)
    return False


def get_user_store() -> dict:
    """Load user accounts from Streamlit secrets."""
    try:
        return dict(st.secrets.get("users", {}))
    except Exception:
        # Fallback demo accounts if secrets not configured
        return {
            "admin": hash_password("actionable2026"),
            "preston": "22b30fdf16b5772fbf941f4d04b9f589388bf1847135f8267b4fe68a9c7c65d8",
        }


def login_screen(app_name: str = "Actionable Intel", accent_color: str = "#3b82f6"):
    """
    Render the login screen. Returns True if authenticated, False otherwise.
    Call this at the top of your app — if it returns False, stop rendering.
    """

    # Already logged in?
    if st.session_state.get("authenticated"):
        return True

    # Custom CSS for the login page
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

        .login-container {{
            max-width: 420px;
            margin: 8vh auto;
            padding: 2.5rem;
            background: #1a1d29;
            border: 1px solid #2a2d3a;
            border-radius: 16px;
        }}
        .login-logo {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .login-title {{
            font-family: 'DM Sans', sans-serif;
            font-size: 1.6rem;
            font-weight: 700;
            color: #e8e8ed;
            text-align: center;
            margin-bottom: 0.25rem;
        }}
        .login-subtitle {{
            font-family: 'DM Sans', sans-serif;
            font-size: 0.85rem;
            color: #8b8fa3;
            text-align: center;
            margin-bottom: 1.5rem;
        }}
        .login-error {{
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: #ef4444;
            font-size: 0.85rem;
            text-align: center;
            margin-top: 0.5rem;
        }}
        .login-footer {{
            text-align: center;
            color: #8b8fa3;
            font-size: 0.75rem;
            margin-top: 1.5rem;
        }}
        /* Hide the default Streamlit menu and footer on login page */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

    # Center the form
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div class="login-logo">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{"🔬" if "Intel" in app_name else "⚖️"}</div>
            <div class="login-title">{app_name}</div>
            <div class="login-subtitle">Sign in to continue</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button(
                "Sign In",
                use_container_width=True,
                type="primary",
            )

            if submitted:
                user_store = get_user_store()
                if check_credentials(username, password, user_store):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.session_state["login_time"] = time.time()
                    st.rerun()
                else:
                    st.markdown(
                        '<div class="login-error">Invalid username or password</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown(
            '<div class="login-footer">Contact admin for account access</div>',
            unsafe_allow_html=True,
        )

    return False


def logout_button():
    """Render a logout button in the sidebar."""
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.get('username', 'unknown')}")
        if st.button("Sign Out", use_container_width=True):
            for key in ["authenticated", "username", "login_time"]:
                st.session_state.pop(key, None)
            st.rerun()


def require_auth(app_name: str = "Actionable Intel", accent_color: str = "#3b82f6"):
    """
    Gate the entire app behind authentication.
    Call at the top of every page. Returns the username if authenticated.
    """
    if not login_screen(app_name, accent_color):
        st.stop()
    logout_button()
    return st.session_state.get("username", "unknown")
