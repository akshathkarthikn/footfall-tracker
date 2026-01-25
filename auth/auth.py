"""
Authentication module for login, logout, and session management.
"""

import streamlit as st
import bcrypt
from datetime import datetime
from database.db import get_db_session
from database.models import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def authenticate_user(username: str, password: str) -> User | None:
    """Authenticate a user and return the User object if successful."""
    with get_db_session() as db:
        user = db.query(User).filter(
            User.username == username,
            User.active == True
        ).first()

        if user and verify_password(password, user.password_hash):
            user.last_login = datetime.utcnow()
            db.commit()
            # Return a dict with user data to avoid detached session issues
            return {
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role,
                'full_name': user.full_name
            }
    return None


def login(username: str, password: str) -> bool:
    """Attempt to log in a user."""
    user_data = authenticate_user(username, password)
    if user_data:
        st.session_state['authenticated'] = True
        st.session_state['user'] = user_data
        return True
    return False


def logout():
    """Log out the current user."""
    st.session_state['authenticated'] = False
    st.session_state['user'] = None


def is_authenticated() -> bool:
    """Check if the current user is authenticated."""
    return st.session_state.get('authenticated', False)


def get_current_user() -> dict | None:
    """Get the current logged-in user data."""
    if is_authenticated():
        return st.session_state.get('user')
    return None


def get_current_user_id() -> int | None:
    """Get the current logged-in user's ID."""
    user = get_current_user()
    return user['user_id'] if user else None


def is_admin() -> bool:
    """Check if the current user is an admin."""
    user = get_current_user()
    return user and user.get('role') == 'admin'


def require_auth():
    """Require authentication to continue. Returns False if not authenticated."""
    if not is_authenticated():
        show_login_form()
        return False
    return True


def require_admin():
    """Require admin role to continue. Returns False if not admin."""
    if not require_auth():
        return False
    if not is_admin():
        st.error("Access denied. Admin privileges required.")
        return False
    return True


def show_login_form():
    """Display the login form."""
    st.markdown("## Login")
    st.markdown("Please log in to access the Footfall Tracker.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            if username and password:
                if login(username, password):
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please enter both username and password.")

    st.markdown("---")
    st.caption("Default credentials: admin / admin123")


def show_user_info():
    """Display current user info in the sidebar."""
    user = get_current_user()
    if user:
        st.sidebar.markdown(f"**Logged in as:** {user['full_name'] or user['username']}")
        st.sidebar.markdown(f"**Role:** {user['role'].title()}")
        if st.sidebar.button("Logout", use_container_width=True):
            logout()
            st.rerun()


def create_user(username: str, password: str, role: str = 'entry', full_name: str = None) -> bool:
    """Create a new user."""
    with get_db_session() as db:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False

        password_hash = hash_password(password)
        new_user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            full_name=full_name
        )
        db.add(new_user)
        db.commit()
        return True


def update_user_password(user_id: int, new_password: str) -> bool:
    """Update a user's password."""
    with get_db_session() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if user:
            user.password_hash = hash_password(new_password)
            db.commit()
            return True
        return False


def get_all_users() -> list:
    """Get all users."""
    with get_db_session() as db:
        users = db.query(User).order_by(User.username).all()
        return [
            {
                'user_id': u.user_id,
                'username': u.username,
                'role': u.role,
                'full_name': u.full_name,
                'active': u.active,
                'last_login': u.last_login
            }
            for u in users
        ]
