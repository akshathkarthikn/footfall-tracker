"""
Footfall Tracker - Main Application Entry Point

A LAN-based web application for tracking hourly footfall per floor
with real-time dashboards, historical comparisons, and admin management.
"""

import streamlit as st
from config import APP_NAME, APP_VERSION
from database.db import init_database
from auth.auth import (
    is_authenticated, require_auth, show_login_form, show_user_info, is_admin
)

# Page configuration - must be first Streamlit command
st.set_page_config(
    page_title=APP_NAME,
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on first run
init_database()


def main():
    """Main application entry point."""
    # Check authentication
    if not is_authenticated():
        st.markdown(f"# {APP_NAME}")
        st.markdown("Track hourly footfall per floor with ease.")
        st.markdown("---")
        show_login_form()
        return

    # Authenticated - show the app
    render_sidebar()
    render_main_content()


def render_sidebar():
    """Render the sidebar with navigation and user info."""
    with st.sidebar:
        st.markdown(f"## {APP_NAME}")
        st.caption(f"v{APP_VERSION}")

        st.markdown("---")

        # Navigation
        pages = ["Quick Entry", "Dashboard", "Compare", "Trends"]
        if is_admin():
            pages.append("Admin")

        # Get current page from session state or default
        if 'page' not in st.session_state:
            st.session_state['page'] = "Quick Entry"

        for page in pages:
            if st.button(page, use_container_width=True, type="primary" if st.session_state['page'] == page else "secondary"):
                st.session_state['page'] = page
                st.rerun()

        st.markdown("---")

        # Show user info and logout
        show_user_info()

        # Page-specific sidebar content
        render_page_sidebar()


def render_page_sidebar():
    """Render page-specific sidebar content."""
    current_page = st.session_state.get('page', 'Quick Entry')

    if current_page == "Quick Entry":
        from pages.quick_entry import render_quick_entry_sidebar
        render_quick_entry_sidebar()
    elif current_page == "Dashboard":
        from pages.live_dashboard import render_dashboard_sidebar
        render_dashboard_sidebar()
    elif current_page == "Compare":
        from pages.compare import render_compare_sidebar
        render_compare_sidebar()
    elif current_page == "Trends":
        from pages.trends import render_trends_sidebar
        render_trends_sidebar()
    elif current_page == "Admin":
        from pages.admin import render_admin_sidebar
        render_admin_sidebar()


def render_main_content():
    """Render the main content area based on selected page."""
    current_page = st.session_state.get('page', 'Quick Entry')

    if current_page == "Quick Entry":
        from pages.quick_entry import render_quick_entry_page
        render_quick_entry_page()
    elif current_page == "Dashboard":
        from pages.live_dashboard import render_live_dashboard_page
        render_live_dashboard_page()
    elif current_page == "Compare":
        from pages.compare import render_compare_page
        render_compare_page()
    elif current_page == "Trends":
        from pages.trends import render_trends_page
        render_trends_page()
    elif current_page == "Admin":
        from pages.admin import render_admin_page
        render_admin_page()


if __name__ == "__main__":
    main()
