import streamlit as st
import pandas as pd
import re
from datetime import date, datetime
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
import json

# Set up the page layout
st.set_page_config(page_title="My Gym Tracker", page_icon="🏋️‍♂️", layout="centered")

# --- GOOGLE SHEETS SETUP ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
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

# --- THE UPDATED PROGRAM ---
PROGRAM = {
    "Day 1: Quad Focus & Verticality": [
        "Heels-Elevated Landmine Squat", "Neutral Grip Pull-Ups", "Band-Assisted Dips",
        "Bulgarian Split Squats", "Nordic Curls", "Banded Face Pulls",
        "Anchored Reverse Crunch", "Glute-Focused Roman Chair Extension", "Squat Wedge Dumbbell Calf Raises"
    ],
    "Day 2: Hinge Focus & Horizontal Load": [
        "Romanian Deadlift (RDL)", "Barbell Hip Thrusts", "T-Bar Landmine Row",
        "Dumbbell Bench Press", "Incline Bar Push-Ups", "Meadows Row",
        "Overhead Tricep Extension", "Banded Crossovers", "Ab-Wheel Rollouts"
    ],
    "Day 3: Hybrid Hypertrophy & Stability": [
        "Erector-Focused Roman Chair Extension", "Landmine Press", "Chest-Supported Lateral Raise",
        "Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns",
        "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"
    ],
    "Thursday/Friday: The Engine Stack (Cardio)": [
        "4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"
    ],
    "🧬 Life Event (Sick/Travel)": [
        "Rest / Recovery / Frozen Week"
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
    "Glute-Focused Roman Chair Extension": "3 Sets × 12–15 Reps",
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
    "Erector-Focused Roman Chair Extension": "3 Sets × 8–10 Reps",
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

UNILATERAL_EXERCISES = [
    "Bulgarian Split Squats", 
    "Meadows Row", 
    "Half-Kneeling Pallof Press", 
    "Heavy Suitcase Holds", 
    "Front-Rack Kettlebell Marches"
]

BAND_OPTIONS = ["Yellow (13.6kg)", "Red (22.6kg)", "Black (36.3kg)", "Purple (45.4kg)", "Green (68.0kg)", "Blue (88.5kg)", "Orange (113.4kg)"]

ALL_EXERCISES = [ex for day_list in PROGRAM.values() for ex in day_list if ex != "Rest / Recovery / Frozen Week"]

@st.cache_data(ttl=600)
def load_data():
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side'])
    
    df = pd.DataFrame(records)
    if 'Distance_km' not in df.columns:
        df['Distance_km'] = 0.0
    if 'Side' not in df.columns:
        df['Side'] = 'Both'
        
    df['Weight'] = pd.to_numeric(df['Weight'], errors='coerce').fillna(0)
    df['Set_Number'] = pd.to_numeric(df['Set_Number'], errors='coerce').fillna(1)
    df['Reps_or_Mins'] = pd.to_numeric(df['Reps_or_Mins'], errors='coerce').fillna(0)
    df['Distance_km'] = pd.to_numeric(df['Distance_km'], errors='coerce').fillna(0)
    df['Side'] = df['Side'].replace('', 'Both').fillna('Both')
    
    # Calculate Volume right away for XP tracking
    df['Volume'] = df['Weight'] * df['Reps_or_Mins']
    return df

def save_data(df):
    # Drop the calculated Volume column before saving so it doesn't break the Google Sheet structure
    df_to_save = df.drop(columns=['Volume'], errors='ignore').fillna('')
    worksheet.clear()
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
    real_workouts = df[df['Workout_Day'] != '🧬 Life Event (Sick/Travel)']
    if not real_workouts.empty:
        first_workout_date = datetime.strptime(real_workouts['Date'].min(), "%Y-%m-%d").date()
        days_since_start = (date.today() - first_workout_date).days
        if days_since_start >= 42:
            st.warning(f"⏳ **Deload Alert:** It has been {days_since_start // 7} weeks since you started this cycle. Remember to take a Deload week soon.")

tab1, tab2, tab3, tab4 = st.tabs(["📝 Log", "📈 Trends", "🏆 Trophy Room", "⚙️ Data"])

# --- TAB 1: LOGGING A WORKOUT ---
with tab1:
    st.subheader("Log Your Session")
    
    date_input = st.date_input("Date", date.today())
    workout_day = st.selectbox("Select Workout Day", list(PROGRAM.keys()))
    
    if "Life Event" in workout_day:
        st.info("🧊 **Streak Frozen.** Take the time you need to recover or travel. Your momentum will be waiting for you when you get back.")
        if st.button("Log Rest Week", type="primary"):
            new_row = pd.DataFrame({'Date': [date_input.strftime("%Y-%m-%d")], 'Workout_Day': [workout_day], 'Exercise': ["Rest / Recovery / Frozen Week"], 'Set_Number': [1], 'Weight': [0], 'Band': ['None'], 'Reps_or_Mins': [0], 'Distance_km': [0.0], 'Side': ['Both']})
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("Life Event logged securely.")
            st.rerun()
            
    else:
        is_cardio = "Cardio" in workout_day
        
        if is_cardio:
            exercise = st.selectbox("Select Cardio", PROGRAM[workout_day])
            col1, col2 = st.columns(2)
            with col1:
                duration = st.number_input("Duration (Minutes)", min_value=1, value=60, step=5)
            with col2:
                distance = st.number_input("Distance (km)", min_value=0.0, value=10.0, step=0.5)
                
            if st.button("Log Cardio", type="primary"):
                new_row = pd.DataFrame({'Date': [date_input.strftime("%Y-%m-%d")], 'Workout_Day': [workout_day], 'Exercise': [exercise], 'Set_Number': [1], 'Weight': [0], 'Band': ['None'], 'Reps_or_Mins': [duration], 'Distance_km': [distance], 'Side': ['Both']})
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("Cardio logged!")
                st.rerun()
                
        else:
            selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day], default=[PROGRAM[workout_day][0]])
            
            if not selected_exercises:
                st.info("👆 Please select at least one exercise to log.")
            else:
                st.write("---")
                weights, reps, reps_l, reps_r, bands = {}, {}, {}, {}, {}
                
                for exercise in selected_exercises:
                    st.markdown(f"### {exercise}")
                    st.caption(f"**Target:** {REP_TARGETS.get(exercise, 'Not set')}")
                    
                    uses_band = exercise in BANDED_EXERCISES
                    is_unilateral = exercise in UNILATERAL_EXERCISES
                    target_sets, top_rep = get_target_reps_and_sets(exercise)
                    
                    if is_unilateral and uses_band:
                        c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.5, 1.5, 2])
                        c1.markdown("**Set**"); c2.markdown("**Kg**"); c3.markdown("**L**"); c4.markdown("**R**"); c5.markdown("**Band**")
                    elif is_unilateral and not uses_band:
                        c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
                        c1.markdown("**Set**"); c2.markdown("**Kg**"); c3.markdown("**L**"); c4.markdown("**R**")
                    elif not is_unilateral and uses_band:
                        c1, c2, c3, c4 = st.columns([1, 2, 2, 3])
                        c1.markdown("**Set**"); c2.markdown("**Kg**"); c3.markdown("**Reps**"); c4.markdown("**Band**")
                    else:
                        c1, c2, c3 = st.columns([1, 2, 2])
                        c1.markdown("**Set**"); c2.markdown("**Kg**"); c3.markdown("**Reps**")
                        
                    for i in range(1, target_sets + 1):
                        key = f"{exercise}_{i}" 
                        
                        if is_unilateral and uses_band:
                            c1, c2, c3, c4, c5 = st.columns([1, 1.5, 1.5, 1.5, 2])
                            c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                            weights[key] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{key}", label_visibility="collapsed")
                            reps_l[key] = c3.number_input("L", min_value=1, value=top_rep, step=1, key=f"rl_{key}", label_visibility="collapsed")
                            reps_r[key] = c4.number_input("R", min_value=1, value=top_rep, step=1, key=f"rr_{key}", label_visibility="collapsed")
                            bands[key] = c5.selectbox("Band", BAND_OPTIONS, key=f"b_{key}", label_visibility="collapsed")
                        elif is_unilateral and not uses_band:
                            c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
                            c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                            weights[key] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{key}", label_visibility="collapsed")
                            reps_l[key] = c3.number_input("L", min_value=1, value=top_rep, step=1, key=f"rl_{key}", label_visibility="collapsed")
                            reps_r[key] = c4.number_input("R", min_value=1, value=top_rep, step=1, key=f"rr_{key}", label_visibility="collapsed")
                        elif not is_unilateral and uses_band:
                            c1, c2, c3, c4 = st.columns([1, 2, 2, 3])
                            c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                            weights[key] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{key}", label_visibility="collapsed")
                            reps[key] = c3.number_input("Reps", min_value=1, value=top_rep, step=1, key=f"r_{key}", label_visibility="collapsed")
                            bands[key] = c4.selectbox("Band", BAND_OPTIONS, key=f"b_{key}", label_visibility="collapsed")
                        else:
                            c1, c2, c3 = st.columns([1, 2, 2])
                            c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                            weights[key] = c2.number_input("Kg", min_value=0.0, value=20.0, step=2.5, key=f"w_{key}", label_visibility="collapsed")
                            reps[key] = c3.number_input("Reps", min_value=1, value=top_rep, step=1, key=f"r_{key}", label_visibility="collapsed")
                    
                    st.write("---")
                
                if st.button("Save All Selected Sets", type="primary", use_container_width=True):
                    new_rows = []
                    for exercise in selected_exercises:
                        uses_band = exercise in BANDED_EXERCISES
                        is_unilateral = exercise in UNILATERAL_EXERCISES
                        target_sets, top_rep = get_target_reps_and_sets(exercise)
                        
                        for i in range(1, target_sets + 1):
                            key = f"{exercise}_{i}"
                            band_val = bands[key] if uses_band else "None"
                            
                            if is_unilateral:
                                new_rows.append({'Date': date_input.strftime("%Y-%m-%d"), 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': band_val, 'Reps_or_Mins': reps_l[key], 'Distance_km': 0.0, 'Side': 'Left'})
                                new_rows.append({'Date': date_input.strftime("%Y-%m-%d"), 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': band_val, 'Reps_or_Mins': reps_r[key], 'Distance_km': 0.0, 'Side': 'Right'})
                            else:
                                new_rows.append({'Date': date_input.strftime("%Y-%m-%d"), 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': band_val, 'Reps_or_Mins': reps[key], 'Distance_km': 0.0, 'Side': 'Both'})
                    
                    df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
                    save_data(df)
                    st.success(f"Logged {len(new_rows)} rows securely to your database!")
                    st.rerun()

# --- TAB 2: DAILY TRENDS ---
with tab2:
    st.subheader("Daily Analytics")
    if df.empty or len(df[df['Exercise'] != "Rest / Recovery / Frozen Week"]) == 0:
        st.info("Log your first workout to see analytics.")
    else:
        exercise_to_view = st.selectbox("Select Exercise", ALL_EXERCISES, key="tab2_ex")
        ex_df = df[df['Exercise'] == exercise_to_view].copy()
        
        if ex_df.empty:
            st.warning("No data found.")
        else:
            if "Rowing" in exercise_to_view or "Bike" in exercise_to_view:
                ex_df['Speed_kmh'] = ex_df.apply(lambda row: row['Distance_km'] / (row['Reps_or_Mins'] / 60) if row['Reps_or_Mins'] > 0 else 0, axis=1)
                daily_stats = ex_df.groupby('Date').agg({'Speed_kmh': 'max'}).reset_index()
                fig = px.line(daily_stats, x='Date', y='Speed_kmh', markers=True, title='Average Speed Trend (km/h)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                ex_df['Est_1RM'] = ex_df['Weight'] * (1 + ex_df['Reps_or_Mins'] / 30)
                daily_stats = ex_df.groupby('Date').agg(Est_1RM=('Est_1RM', 'max'), Total_Volume=('Volume', 'sum')).reset_index()
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=daily_stats['Date'], y=daily_stats['Total_Volume'], name='Tonnage (kg)', opacity=0.5, marker_color='#1f77b4'))
                fig.add_trace(go.Scatter(x=daily_stats['Date'], y=daily_stats['Est_1RM'], name='Est 1RM (kg)', mode='lines+markers', yaxis='y2', line=dict(color='#FF4B4B', width=3)))
                fig.update_layout(yaxis=dict(title='Volume (kg)', side='left'), yaxis2=dict(title='Est 1RM (kg)', side='right', overlaying='y', showgrid=False), hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: THE TROPHY ROOM (GAMIFICATION) ---
with tab3:
    st.subheader("🏆 The Trophy Room")
    if df.empty:
        st.info("Complete workouts to earn XP and unlock stats!")
    else:
        lifting_df = df[~df['Exercise'].isin(["Rest / Recovery / Frozen Week", "4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"])].copy()
        lifting_df['Month'] = pd.to_datetime(lifting_df['Date']).dt.strftime('%Y-%m')
        
        # Grand Total XP
        total_xp = lifting_df['Volume'].sum()
        st.markdown(f"### **Total Lifetime XP:** {total_xp:,.0f} kg moved")
        st.progress(min(total_xp / 100000, 1.0)) # Visual bar up to 100,000kg
        st.caption("Bar fills up every 100,000kg moved.")
        st.write("---")
        
        # Monthly Comparison
        st.markdown("#### 📅 Month-over-Month XP")
        monthly_xp = lifting_df.groupby('Month')['Volume'].sum().reset_index()
        fig_month = px.bar(monthly_xp, x='Month', y='Volume', text='Volume', color_discrete_sequence=['#FF4B4B'])
        fig_month.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_month.update_layout(yaxis_title="Total Volume (XP)", xaxis_title="")
        st.plotly_chart(fig_month, use_container_width=True)
        st.write("---")
        
        # Volume Mastery (The Longevity Skill Tree)
        st.markdown("#### ⚔️ Exercise Mastery Levels")
        st.write("*Gain +1 Level for every 5,000kg (5 tons) moved.*")
        
        ex_xp = lifting_df.groupby('Exercise')['Volume'].sum().reset_index()
        ex_xp['Level'] = (ex_xp['Volume'] // 5000) + 1
        ex_xp = ex_xp.sort_values(by='Level', ascending=False)
        
        # Display as a clean dataframe
        st.dataframe(
            ex_xp[['Exercise', 'Level', 'Volume']].rename(columns={'Volume': 'Total XP'}),
            column_config={
                "Level": st.column_config.ProgressColumn("Mastery Level", format="Lvl %d", min_value=0, max_value=20),
                "Total XP": st.column_config.NumberColumn("Total XP (kg)", format="%d")
            },
            hide_index=True, use_container_width=True
        )

# --- TAB 4: MANAGE DATA ---
with tab4:
    st.subheader("Edit or Delete Logs")
    if not df.empty:
        st.write("### Option 1: Quick Undo")
        if st.button("⏪ Delete Last Logged Row", type="secondary"):
            df = df.iloc[:-1] 
            save_data(df)
            st.success("Last row deleted!")
            st.rerun()
            
        st.write("---")
        st.write("### Option 2: The Spreadsheet Editor")
        edited_df = st.data_editor(df.drop(columns=['Volume'], errors='ignore'), num_rows="dynamic", use_container_width=True, key="data_editor")
        if st.button("Save Spreadsheet Changes", type="primary"):
            save_data(edited_df)
            st.success("Database updated successfully!")
            st.rerun()
    else:
        st.info("Your database is currently empty.")
