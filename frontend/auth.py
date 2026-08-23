"""Shared login gate for both Streamlit apps: a hardcoded user directory and a
styled, role-aware login screen (gradient background, centered glass card)."""

import streamlit as st

from app.config import ADMIN_PASSWORD

USERS = {
    "noah@company.com": {"password": "noah", "role": "employee", "display_name": "Noah"},
    "james@company.com": {"password": "james", "role": "employee", "display_name": "James"},
    "william@company.com": {"password": "william", "role": "employee", "display_name": "William"},
    "sophia@company.com": {"password": "sophia", "role": "employee", "display_name": "Sophia"},
    "emma@company.com": {"password": "emma", "role": "employee", "display_name": "Emma"},
    "admin@admin.com": {"password": ADMIN_PASSWORD, "role": "admin", "display_name": "Admin"},
}

EMPLOYEE_GRADIENT = "linear-gradient(135deg, #f3d1f4 0%, #cdb6ef 30%, #a9c9ef 68%, #9aeadd 100%)"
ADMIN_GRADIENT = "linear-gradient(135deg, #fde3c7 0%, #fbd2ab 32%, #f8c39a 66%, #f5b285 100%)"

# Dark navy strokes/text so everything reads clearly against the light pastel
# gradients and the translucent glass panel (white icons/text were invisible).
INK = "%2314335e"  # '#14335e' percent-encoded for use inside SVG data URIs

MAIL_ICON_DATA_URI = (
    f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
    f"fill='none' stroke='{INK}' stroke-width='1.8' stroke-linecap='round' "
    f"stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='14' rx='2'%3E%3C/rect%3E"
    f"%3Cpath d='M3 7l9 6 9-6'%3E%3C/path%3E%3C/svg%3E"
)

LOCK_ICON_DATA_URI = (
    f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' "
    f"fill='none' stroke='{INK}' stroke-width='1.8' stroke-linecap='round' "
    f"stroke-linejoin='round'%3E%3Crect x='5' y='11' width='14' height='9' rx='2' ry='2'"
    f"%3E%3C/rect%3E%3Cpath d='M8 11V7a4 4 0 0 1 8 0v4'%3E%3C/path%3E%3C/svg%3E"
)


def _build_css(gradient_css: str) -> str:
    return f"""
<style>
    .stApp {{
        background: {gradient_css};
        min-height: 100vh;
    }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    div[data-testid="stToolbar"] {{ display: none !important; }}
    [data-testid="stMainBlockContainer"] {{ padding-top: 9vh !important; }}

    /* Horizontal centering uses Streamlit's own st.columns() — the header
       markdown and the form panel both live inside the same middle column,
       so they are guaranteed to stack as one vertical block by Streamlit's
       own (well-tested) column layout, rather than a custom CSS hack. */
    .login-col {{ text-align: center; }}
    .login-welcome {{
        font-weight: 700;
        font-size: 28px;
        line-height: 1.25;
        color: #14335e;
        margin-bottom: 16px;
    }}
    .login-icon {{
        width: 64px;
        height: 64px;
        margin: 0 auto 10px;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    .login-icon svg {{ width: 32px; height: 32px; }}
    .login-title {{
        font-weight: 300;
        font-size: 17px;
        color: #14335e;
        opacity: 0.75;
        letter-spacing: 0.5px;
        text-align: center;
        margin: 4px 0 0;
    }}

    /* Inner glass panel: purely visual, holds only the actual form. Capped
       width + auto margin so it stays a fixed card size and centers within
       whatever width the middle column happens to be. */
    .st-key-login_form_panel {{
        max-width: 380px;
        margin: 26px auto 0;
        padding: 34px 32px 30px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
    }}

    /* Text inputs: the bordered box is stTextInputRootElement (verified from
       Streamlit's compiled source), not a generic child div. Force identical
       sizing on both fields and dark, clearly-readable text/placeholder. */
    .st-key-login_form_panel div[data-testid="stTextInput"] {{
        width: 100% !important;
        margin-bottom: 16px;
    }}
    .st-key-login_form_panel div[data-testid="stTextInput"] label {{ display: none; }}
    .st-key-login_form_panel [data-testid="stTextInputRootElement"] {{
        width: 100% !important;
        height: 46px !important;
        box-sizing: border-box !important;
        background: transparent !important;
        border: none !important;
        border-bottom: 1.5px solid rgba(20, 51, 94, 0.35) !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        /* BaseWeb reserves 14px of right padding on the password field's
           Root for the show/hide icon (confirmed via computed styles) —
           the username Root has 0px here. Hiding the button alone doesn't
           remove this, so it's overridden explicitly on both (harmless on
           the username field, which is already 0). */
        padding-right: 0 !important;
    }}
    /* Hide the built-in show/hide-password toggle. It's a BaseWeb button
       with no Streamlit testid, identified by its aria-label instead. It's
       a flex sibling of the actual <input> (confirmed via the real DOM),
       not a parent of it, so hiding it directly is safe. */
    .st-key-login_form_panel button[aria-label="Show password text"],
    .st-key-login_form_panel button[aria-label="Hide password text"] {{
        display: none !important;
    }}
    .st-key-login_form_panel [data-testid="stTextInputRootElement"] input {{
        width: 100% !important;
        height: 100% !important;
        box-sizing: border-box !important;
        background-color: transparent !important;
        color: #14335e !important;
        font-weight: 400 !important;
        padding-left: 30px !important;
        background-repeat: no-repeat;
        background-position: left center;
        background-size: 18px 18px;
    }}
    .st-key-login_form_panel [data-testid="stTextInputRootElement"] input::placeholder {{
        color: rgba(20, 51, 94, 0.55) !important;
    }}
    .st-key-login_form_panel .st-key-login_email input {{
        background-image: url("{MAIL_ICON_DATA_URI}");
    }}
    .st-key-login_form_panel input[type="password"] {{
        background-image: url("{LOCK_ICON_DATA_URI}");
    }}

    /* Submit button: force white text on every descendant (BaseWeb wraps the
       label in its own span/p with an inline color that would otherwise win). */
    .st-key-login_form_panel div[data-testid="stForm"] {{ border: none; background: transparent; padding: 0; }}
    .st-key-login_form_panel div[data-testid="stFormSubmitButton"] {{ display: flex; justify-content: center; }}
    .st-key-login_form_panel div[data-testid="stFormSubmitButton"] button {{
        width: 100%;
        margin-top: 14px;
        background-color: #14335e !important;
        border: none !important;
        border-radius: 8px;
        padding: 12px 0;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }}
    .st-key-login_form_panel div[data-testid="stFormSubmitButton"] button,
    .st-key-login_form_panel div[data-testid="stFormSubmitButton"] button * {{
        color: #ffffff !important;
    }}
    .st-key-login_form_panel div[data-testid="stFormSubmitButton"] button:hover {{
        background-color: #1c4677 !important;
    }}
</style>
"""


_PERSON_ICON_SVG = """
<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none'
     stroke='#14335e' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'>
    <circle cx='12' cy='8' r='4'></circle>
    <path d='M4 21c0-4 4-6 8-6s8 2 8 6'></path>
</svg>
"""


def render_login_gate(
    allowed_roles: set[str],
    title: str = "User Login",
    welcome_text: str = "Welcome back",
    welcome_icon: str = "👋",
    gradient_css: str = EMPLOYEE_GRADIENT,
) -> None:
    """Renders a styled login screen and blocks the rest of the page (via st.stop())
    until a user with a role in `allowed_roles` successfully authenticates. If
    already authenticated with a permitted role, returns immediately as a no-op."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_role = None
        st.session_state.display_name = None

    if st.session_state.authenticated and st.session_state.user_role in allowed_roles:
        return

    st.session_state.authenticated = False
    st.markdown(_build_css(gradient_css), unsafe_allow_html=True)

    # Streamlit's own column mechanism guarantees everything placed inside
    # `center` renders as a single vertical stack in that one horizontally
    # centered column — the header and the form panel can no longer end up
    # in visually separate places the way the previous custom-CSS/fixed-
    # position container did.
    _, center, _ = st.columns([1, 1.3, 1])
    with center:
        st.markdown(
            f'<div class="login-col">'
            f'<div class="login-welcome">{welcome_icon} {welcome_text}</div>'
            f'<div class="login-icon">{_PERSON_ICON_SVG}</div>'
            f'<div class="login-title">{title}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
        with st.container(key="login_form_panel"):
            with st.form("login_form", border=False):
                email = st.text_input(
                    "Username", placeholder="Username", label_visibility="collapsed", key="login_email"
                )
                password = st.text_input(
                    "Password", type="password", placeholder="Password", label_visibility="collapsed"
                )
                submitted = st.form_submit_button("Login")

            if submitted:
                normalized_email = email.strip().lower()
                user = USERS.get(normalized_email)
                if user is None or user["password"] != password:
                    st.error("Invalid username or password.")
                elif user["role"] not in allowed_roles:
                    st.error("This account doesn't have access to this application.")
                else:
                    st.session_state.authenticated = True
                    st.session_state.user_email = normalized_email
                    st.session_state.user_role = user["role"]
                    st.session_state.display_name = user["display_name"]
                    st.rerun()

    st.stop()
