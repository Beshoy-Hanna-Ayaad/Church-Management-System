import streamlit as st
from supabase import create_client
import pandas as pd

st.set_page_config(
    page_title="Church App",
    layout="wide"
)

# --- DATABASE CONNECTION & DATA LOADING ---
@st.cache_resource(ttl=600)
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None

# IMPORTANT: Ensure your "Servant" table has a 'password' column (text type)
@st.cache_data(ttl=600)
def load_all_data(_supabase_client):
    if _supabase_client is None: return (pd.DataFrame() for _ in range(6))
    try:
        # NOTE: The select("*") assumes you've added a 'password' column in Supabase
        servants = pd.DataFrame(_supabase_client.from_("Servant").select("*").execute().data)
        if 'password' not in servants.columns:
            # Handle case where password column doesn't exist yet, to prevent crashing
            servants['password'] = "pass123" # Default password for demo purposes
            st.warning("Warning: 'password' column not found in Servant table. Using a default password for demonstration.")

        departments = pd.DataFrame(_supabase_client.from_("Department").select("*").execute().data)
        classes = pd.DataFrame(_supabase_client.from_("Class").select("*").execute().data)
        students = pd.DataFrame(_supabase_client.from_("Student").select("*").execute().data)
        activities = pd.DataFrame(_supabase_client.from_("Activity").select("*").execute().data)
        attendance = pd.DataFrame(_supabase_client.from_("Attendance").select("*").execute().data)
        return departments, servants, classes, students, activities, attendance
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return (pd.DataFrame() for _ in range(6))

# --- AUTHENTICATION LOGIC ---
def login_form():
    """Displays the login form and returns True if authentication is successful."""
    st.title("Church Data Platform Login")
    with st.form("login_form"):
        username = st.text_input("Username (Servant Name)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            # Check credentials against the loaded servant data
            user_data = st.session_state.servants[st.session_state.servants['servant_name'] == username]
            if not user_data.empty and password == user_data.iloc[0]['password']:
                st.session_state.authenticated = True
                st.session_state.user_role = user_data.iloc[0]['role']
                st.session_state.current_user_id = user_data.iloc[0]['servant_id']
                st.success("Login successful!")
                st.rerun() # Rerun the script to show the main app
            else:
                st.error("Incorrect username or password.")
    return False

# --- MAIN APP LOGIC ---

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False


# The Gatekeeper: Show login form or the main app
if not st.session_state.authenticated:
    # Load data needed for login
    supabase = init_connection()
    if supabase:
        _, servants_df, _, _, _, _ = load_all_data(supabase)
        st.session_state.servants = servants_df
        login_form()
    else:
        st.stop()
else:
    # --- This code runs ONLY after a successful login ---
    
    # Load all data if it hasn't been loaded yet
    if not st.session_state.data_loaded:
        supabase = init_connection()
        if supabase:
            data_tuple = load_all_data(supabase)
            (st.session_state.departments, st.session_state.servants, st.session_state.classes, 
             st.session_state.students, st.session_state.activities, st.session_state.attendance) = data_tuple
            st.session_state.supabase = supabase
            st.session_state.data_loaded = True
        else:
            st.stop()

    # --- PAGE DEFINITIONS & NAVIGATION ---
    dashboard_page = st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True)
    attendance_analysis_page = st.Page("views/attendance_analysis.py", title="Attendance Analysis", icon="📈")
    target_analysis_page = st.Page("views\\terget_analysis.py", title="Target Analysis", icon="🎯")
    student_profile_page = st.Page("views/student_profile.py", title="Student Profile", icon="👤")
    leaderboard_page = st.Page("views/leaderboard.py", title="Leaderboard", icon="🏆")
    risk_analysis_page = st.Page("views/risk_analysis.py", title="Students at Risk", icon="⚠️")
    attendance_entry_page = st.Page("views/attendance_entry.py", title="Attendance Entry", icon="📝")
    admin_panel_page = st.Page("views/admin_panel.py", title="Admin Panel", icon="⚙️")
    opportunity_roster_page = st.Page("views/opportunity_roster.py", title="Opportunity Roster", icon="⚖️")

    
    pg = st.navigation({
        "Data Collection": [attendance_entry_page],
        "Data Analysis": [dashboard_page, attendance_analysis_page, target_analysis_page, student_profile_page, leaderboard_page, risk_analysis_page],
        "Data Management": [admin_panel_page, opportunity_roster_page],
    })

    # --- SHARED SIDEBAR CONTENT ---
    st.sidebar.success(f"Logged in as: **{st.session_state.user_role}**")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        # Clear sensitive data on logout
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- RUN THE APP ---
    pg.run()
