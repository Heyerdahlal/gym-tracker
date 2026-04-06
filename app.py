import streamlit as st
import pandas as pd
import re
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go

# Set up the page layout
st.set_page_config(page_title="My Gym Tracker", page_icon="🏋️‍♂️", layout="centered")

# --- GOOGLE SHEETS SETUP ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

@st.cache_resource
def init_connection():
    creds = Credentials.from_service_account_file('secrets.json', scopes=SCOPES)
    return gspread.authorize(creds)

gc = init_connection()

try:
    sh = gc.open("Gym_Tracker_DB")
    worksheet = sh.sheet1
except gspread.exceptions.SpreadsheetNotFound:
    st.error("⚠️ **Error:** The bot could not find a spreadsheet named exactly `Gym_Tracker_DB`.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ **Google Connection Error:** {e}")
    st.stop()

# Your specific workout program parameters
PROGRAM = {
    "Day 1: Quad Focus & Verticality": [
        "Heels-Elevated Landmine Squat", "Neutral Grip Pull-Ups", "Band-Assisted Dips",
        "Bulgarian Split Squats", "Nordic Curls", "Banded Face Pulls",
        "Anchored Reverse Crunch", "Squat Wedge Dumbbell Calf Raises"
    ],
    "Day 2: Hinge Focus & Horizontal Load": [
        "Romanian Deadlift (RDL)", "Barbell Hip Thrusts", "T-Bar Landmine Row",
        "Dumbbell Bench Press", "Incline Bar Push-Ups", "Meadows Row",
        "Overhead Tricep Extension", "Banded Crossovers", "Ab-Wheel Rollouts"
    ],
    "Day 3: Hybrid Hypertrophy & Stability": [
        "Hex Bar Deadlift", "Landmine Press", "Chest-Supported Lateral Raise",
        "Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns",
        "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"
    ],
    "Thursday/Friday: The Engine Stack (Cardio)": [
        "4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"
    ]
}

REP_TARGETS = {
    "Heels-Elevated Landmine Squat": "3 Sets × 6–8 Reps",
    "Neutral Grip Pull-Ups": "4 Sets × 5–8 Reps",
    "Band-Assisted Dips": "4 Sets × 10–12 Reps",
    "Bulgarian Split Squats": "3 Sets × 8–10 Reps/leg",
    "Nordic Curls": "3 Sets × 5–8 Reps",
    "Banded Face Pulls": "3 Sets × 15–20 Reps",
    "Anchored Reverse Crunch": "3 Sets × 10–12 Reps",
    "Squat Wedge Dumbbell Calf Raises": "3 Sets × 10–12 Reps",
    "Romanian Deadlift (RDL)": "4 Sets × 6–8 Reps",
    "Barbell Hip Thrusts": "4 Sets × 10–12 Reps",
    "T-Bar Landmine Row": "4 Sets × 8–10 Reps",
    "Dumbbell Bench Press": "4 Sets × 8–10 Reps",
    "Incline Bar Push-Ups": "3 Sets × 10–15 Reps",
    "Meadows Row": "3 Sets × 10–12 Reps/arm",
    "Overhead Tricep Extension": "3 Sets × 12–15 Reps",
    "Banded Crossovers": "3 Sets × 15–20 Reps",
    "Ab-Wheel Rollouts": "3 Sets × 8–10 Reps",
    "Hex Bar Deadlift": "3 Sets × 8–10 Reps",
    "Landmine Press": "3 Sets × 8–10 Reps",
    "Chest-Supported Lateral Raise": "4 Sets × 15–20 Reps",
    "Incline Supinated Dumbbell Curls": "4 Sets × 10–12 Reps",
    "Banded Tricep Pushdowns": "4 Sets × 15–20 Reps",
    "Half-Kneeling Pallof Press": "3 Sets × 10–12 Reps/side",
    "Heavy Suitcase Holds": "3 Sets × 45 Seconds/side",
    "Front-Rack Kettlebell Marches": "3 Sets × 45 Seconds/side",
    "4x4 Rowing (Zone 4/5)": "4 Rounds (4m Work / 3m Rest)",
    "Zone 2 Spin Bike Flush": "60-90 Minutes"
}

BANDED_EXERCISES = [
    "Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls",
    "Overhead Tricep Extension", "Banded Crossovers", "Banded Tricep Pushdowns",
    "Half-Kneeling Pallof Press"
]

BAND_OPTIONS = ["Yellow (13.6kg)", "Red (22.6kg)", "Black (36.3kg)", "Purple (45.4kg)", "Green (68.0kg)", "Blue (88.5kg)", "Orange (113.4kg)"]

ALL_EXERCISES = [ex for day_list in PROGRAM.values() for ex in day_list]

@st.cache_data(ttl=600)
def load_data():
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km'])
    
    df = pd.DataFrame(records)
    # Ensure all missing columns exist to prevent errors
    if 'Distance_km' not in df.columns:
        df['Distance_km'] = 0.0
        
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(0)
    df['Set_Number'] = pd.to_numeric(df['Set_Number'], errors='coerce').fillna(1)
    df['Reps_or_Mins'] = pd.to_numeric(df['Reps_or_Mins'], errors='coerce').fillna(0)
    df['Distance_km'] = pd.to_numeric(df['Distance_km'], errors='coerce').fillna(0)
    return df

def save_data(df):
    df_to_save = df.fillna('')
    worksheet.clear()
    # By explicitly stating values= and range_name="A1", we force Google to overwrite everything
    worksheet.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
    st.cache_data.clear()

def get_target_reps_and_sets(exercise_name):
    target_str = REP_TARGETS.get(exercise_name, "")
    sets_match = re.search(r'(\d+)\s*Sets', target_str, re.IGNORECASE)
    reps_match = re.search(r'–(\d+)\s*Reps', target_str, re.IGNORECASE)
    
    target_sets = int(sets_match.group(1)) if sets_match else 3
    top_rep = int(reps_match.group(1)) if reps_match else 8
    return target_sets, top_rep

df = load_data()

st.title("🏋️‍♂️ The Daily System Tracker")

if not df.empty:
    first_workout_date = datetime.strptime(df['Date'].min(), "%Y-%m-%d").date()
    days_since_start = (date.today() - first_workout_date).days
    if days_since_start >= 42:
        st.warning(f"⏳ **Deload Alert:** It has been {days_since_start // 7} weeks since you started this cycle. Remember to take a Deload week soon (2 sets, 70% weight).")

tab1, tab2, tab3 = st.tabs(["📝 Log Workout", "📈 View Progress", "⚙️ Manage Data"])

# --- TAB 1: LOGGING A WORKOUT ---
with tab1:
    st.subheader("Log Your Sets & Cardio")
    
    date_input = st.date_input("Date", date.today())
    workout_day = st.selectbox("Select Workout Day", list(PROGRAM.keys()))
    exercise = st.selectbox("Select Exercise", PROGRAM[workout_day])
    
    st.info(f"**Target:** {REP_TARGETS.get(exercise, 'Not set')}")
    
    is_cardio = "Cardio" in workout_day
    uses_band = exercise in BANDED_EXERCISES
    target_sets, top_rep = get_target_reps_and_sets(exercise)
    
    if is_cardio:
        col1, col2 = st.columns(2)
        with col1:
            duration = st.number_input("Duration (Minutes)", min_value=1, value=60, step=5)
        with col2:
            distance = st.number_input("Distance (km)", min_value=0.0, value=10.0, step=0.5)
            
        if st.button("Log Cardio", type="primary"):
            new_row = pd.DataFrame({'Date': [date_input.strftime("%Y-%m-%d")], 'Workout_Day': [workout_day], 'Exercise': [exercise], 'Set_Number': [1], 'Weight': [0], 'Band': ['None'], 'Reps_or_Mins': [duration], 'Distance_km': [distance]})
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            speed = distance / (duration / 60) if duration > 0 else 0
            st.success(f"Logged: {distance}km in {duration} mins. Average Speed: {speed:.1f} km/h!")
            st.rerun()
            
    else:
        st.write("---")
        
        if uses_band:
            c1, c2, c3, c4 = st.columns([1, 2, 2, 3])
            c1.markdown("**Set**")
            c2.markdown("**Kg**")
            c3.markdown("**Reps**")
            c4.markdown("**Band**")
        else:
            c1, c2, c3 = st.columns([1, 2, 2])
            c1.markdown("**Set**")
            c2.markdown("**Kg**")
            c3.markdown("**Reps**")
            
        weights = {}
        reps = {}
        bands = {}
        
        for i in range(1, target_sets + 1):
            if uses_band:
                c1, c2, c3, c4 = st.columns([1, 2, 2, 3])
                c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                weights[i] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{exercise}_{i}", label_visibility="collapsed")
                reps[i] = c3.number_input("Reps", min_value=1, value=top_rep, step=1, key=f"r_{exercise}_{i}", label_visibility="collapsed")
                bands[i] = c4.selectbox("Band", BAND_OPTIONS, key=f"b_{exercise}_{i}", label_visibility="collapsed")
            else:
                c1, c2, c3 = st.columns([1, 2, 2])
                c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                weights[i] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{exercise}_{i}", label_visibility="collapsed")
                reps[i] = c3.number_input("Reps", min_value=1, value=top_rep, step=1, key=f"r_{exercise}_{i}", label_visibility="collapsed")
        
        st.write("---")
        
        if st.button("Save All Sets", type="primary", use_container_width=True):
            new_rows = []
            for i in range(1, target_sets + 1):
                band_val = bands[i] if uses_band else "None"
                new_rows.append({
                    'Date': date_input.strftime("%Y-%m-%d"),
                    'Workout_Day': workout_day,
                    'Exercise': exercise,
                    'Set_Number': i,
                    'Weight': weights[i],
                    'Band': band_val,
                    'Reps_or_Mins': reps[i],
                    'Distance_km': 0.0
                })
            
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_data(df)
            st.success(f"Logged all {target_sets} sets for {exercise}!")
            st.rerun()

# --- TAB 2: VIEWING PROGRESS & COACHING ALERTS ---
with tab2:
    st.subheader("Interactive Analytics Dashboard")
    
    if df.empty:
        st.info("No data yet! Log your first workout to see trends.")
    else:
        exercise_to_view = st.selectbox("Select Exercise to Analyze", ALL_EXERCISES)
        ex_df = df[df['Exercise'] == exercise_to_view].copy()
        
        if ex_df.empty:
            st.warning(f"No data found for {exercise_to_view}.")
        else:
            is_cardio_view = "Rowing" in exercise_to_view or "Bike" in exercise_to_view
            
            if is_cardio_view:
                # Calculate speed for cardio
                ex_df['Speed_kmh'] = ex_df.apply(lambda row: row['Distance_km'] / (row['Reps_or_Mins'] / 60) if row['Reps_or_Mins'] > 0 else 0, axis=1)
                daily_stats = ex_df.groupby('Date').agg({'Speed_kmh': 'max', 'Distance_km': 'max', 'Reps_or_Mins': 'max'}).reset_index()
                
                # Cardio Metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("Max Distance", f"{daily_stats['Distance_km'].max():.2f} km")
                c2.metric("Best Avg Speed", f"{daily_stats['Speed_kmh'].max():.1f} km/h")
                c3.metric("Longest Session", f"{daily_stats['Reps_or_Mins'].max():.0f} min")
                
                # Cardio Speed Plotly Chart
                fig = px.line(daily_stats, x='Date', y='Speed_kmh', markers=True, title='Average Speed Trend (km/h)')
                fig.update_traces(line_color='#FF4B4B', marker=dict(size=8))
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                # Lifting Math
                ex_df['Est_1RM'] = ex_df['Weight'] * (1 + ex_df['Reps_or_Mins'] / 30)
                ex_df['Volume'] = ex_df['Weight'] * ex_df['Reps_or_Mins']
                
                daily_stats = ex_df.groupby('Date').agg(
                    Est_1RM=('Est_1RM', 'max'),
                    Total_Volume=('Volume', 'sum')
                ).reset_index()
                
                # Progression Alert Logic
                target_sets, top_rep = get_target_reps_and_sets(exercise_to_view)
                latest_date = ex_df['Date'].max()
                latest_session = ex_df[ex_df['Date'] == latest_date]
                
                if target_sets > 0 and top_rep > 0:
                    sets_completed = len(latest_session)
                    hit_top_reps = all(r >= top_rep for r in latest_session['Reps_or_Mins'])
                    if sets_completed >= target_sets and hit_top_reps:
                        st.success(f"🟢 **PROGRESSION ACHIEVED!** Hit {top_rep} reps for all sets on {latest_date}. Increase weight next time!")
                
                # Lifting Metrics
                c1, c2, c3 = st.columns(3)
                c1.metric("All-Time 1RM", f"{daily_stats['Est_1RM'].max():.1f} kg")
                c2.metric("Max Session Volume", f"{daily_stats['Total_Volume'].max():.0f} kg")
                c3.metric("Sessions Tracked", f"{len(daily_stats)}")
                
                # Combo Chart: Volume & 1RM
                fig = go.Figure()
                fig.add_trace(go.Bar(x=daily_stats['Date'], y=daily_stats['Total_Volume'], name='Tonnage (kg)', opacity=0.5, marker_color='#1f77b4'))
                fig.add_trace(go.Scatter(x=daily_stats['Date'], y=daily_stats['Est_1RM'], name='Est 1RM (kg)', mode='lines+markers', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
                fig.update_layout(
                    title="Volume vs. 1RM Progression",
                    yaxis=dict(title='Total Volume (kg)', side='left'),
                    yaxis2=dict(title='Estimated 1RM (kg)', side='right', overlaying='y', showgrid=False),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Fatigue Scatter Chart
                fig2 = px.line(ex_df, x='Date', y='Reps_or_Mins', color='Set_Number', markers=True, title="Set-by-Set Endurance Drop-off")
                fig2.update_layout(yaxis_title="Reps Completed")
                st.plotly_chart(fig2, use_container_width=True)
                
            st.write("**Recent Session Logs:**")
            st.dataframe(ex_df[['Date', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km']].sort_values(by=['Date', 'Set_Number'], ascending=[False, True]).head(15))

# --- TAB 3: MANAGE DATA (DELETE/EDIT) ---
with tab3:
    st.subheader("Edit or Delete Logs")
    
    if not df.empty:
        st.write("### Option 1: Quick Undo")
        if st.button("⏪ Delete Last Logged Set", type="secondary"):
            df = df.iloc[:-1] 
            save_data(df)
            st.success("Last set deleted!")
            st.rerun()
            
        st.write("---")
        st.write("### Option 2: The Spreadsheet Editor")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="data_editor")
        
        if st.button("Save Spreadsheet Changes", type="primary"):
            save_data(edited_df)
            st.success("Database updated successfully!")
            st.rerun()
    else:
        st.info("Your database is currently empty.")