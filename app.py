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

@st.cache_data(ttl=600)
def load_all_data(_supabase_client):
    if _supabase_client is None: return (pd.DataFrame() for _ in range(6))
    try:
        servants = pd.DataFrame(_supabase_client.from_("Servant").select("*").execute().data)
        if 'password' not in servants.columns:
            servants['password'] = "pass123" 
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
    st.title("Church Data Platform Login")
    with st.form("login_form"):
        username = st.text_input("Username (Servant Name)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            user_data = st.session_state.servants[st.session_state.servants['servant_name'] == username]
            if not user_data.empty and password == user_data.iloc[0]['password']:
                st.session_state.authenticated = True
                st.session_state.user_role = user_data.iloc[0]['role']
                st.session_state.current_user_id = user_data.iloc[0]['servant_id']
                st.session_state.current_user_name = user_data.iloc[0]['servant_name']
                
                # NEW: Add a flag to show the welcome message only once
                st.session_state.show_welcome_message = True

                st.rerun()
            else:
                st.error("Incorrect username or password.")
    return False

# --- MAIN APP LOGIC ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.authenticated:
    supabase = init_connection()
    if supabase:
        _, servants_df, _, _, _, _ = load_all_data(supabase)
        st.session_state.servants = servants_df
        login_form()
    else:
        st.stop()
else:
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
    opportunity_roster_page = st.Page("views/opportunity_roster.py", title="Opportunity Roster", icon="⚖️")
    attendance_entry_page = st.Page("views/attendance_entry.py", title="Attendance Entry", icon="📝")
    admin_panel_page = st.Page("views/admin_panel.py", title="Admin Panel", icon="⚙️")
    
    pg = st.navigation({
        "Data Collection": [attendance_entry_page],
        "Data Analysis": [dashboard_page, attendance_analysis_page, target_analysis_page, student_profile_page, leaderboard_page, risk_analysis_page, opportunity_roster_page],
        "Data Management": [admin_panel_page],
    })

    # --- SHARED SIDEBAR CONTENT ---
    
    # --- MODIFIED: SPECIAL GREETING LOGIC ---
    # Show a prominent toast message the first time she logs in
    if st.session_state.get("show_welcome_message") and st.session_state.get("current_user_name") == "Deena Gergis":
        st.toast("Welcome Deena, the Egyptian Star in the Data Science Sky! ✨", icon="🎉")
        st.session_state.show_welcome_message = False # Ensure it only shows once per login

    # The sidebar message is now enhanced as well
    if st.session_state.get("current_user_name") == "Deena Gergis":
        st.sidebar.header("Welcome Deena! ✨")
        st.sidebar.markdown("Thank you for reviewing this project.")
    else:
        st.sidebar.success(f"Logged in as: **{st.session_state.user_role}**")
    
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # --- RUN THE APP ---
    pg.run()