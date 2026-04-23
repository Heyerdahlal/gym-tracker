import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import date, datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
import json

st.set_page_config(page_title="My Gym Tracker", page_icon="🏋️‍♂️", layout="wide") # Changed to wide layout for dashboards

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
except Exception as e:
    st.error(f"⚠️ **Google Connection Error:** {e}")
    st.stop()

# --- PROGRAM & MUSCLE DICTIONARY ---
PROGRAM = {
    "Day 1: Quad Focus & Verticality": ["Heels-Elevated Landmine Squat", "Neutral Grip Pull-Ups", "Band-Assisted Dips", "Bulgarian Split Squats", "Nordic Curls", "Banded Face Pulls", "Anchored Reverse Crunch", "Glute-Focused Roman Chair Extension", "Squat Wedge Dumbbell Calf Raises"],
    "Day 2: Hinge Focus & Horizontal Load": ["Romanian Deadlift (RDL)", "Barbell Hip Thrusts", "T-Bar Landmine Row", "Dumbbell Bench Press", "Incline Bar Push-Ups", "Meadows Row", "Overhead Tricep Extension", "Banded Crossovers", "Ab-Wheel Rollouts"],
    "Day 3: Hybrid Hypertrophy & Stability": ["Erector-Focused Roman Chair Extension", "Landmine Press", "Chest-Supported Lateral Raise", "Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"],
    "Thursday/Friday: Cardio": ["4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"]
}

# Muscle Heatmap Multipliers (Primary = 1.0, Secondary = 0.5)
MUSCLE_MAP = {
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0, "Erectors": 0.5},
    "Dumbbell Bench Press": {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5},
    "Neutral Grip Pull-Ups": {"Lats": 1.0, "Biceps": 0.5},
    # Add your other exercises here to build out the full heatmap!
}

UNILATERAL_EXERCISES = ["Bulgarian Split Squats", "Meadows Row", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
ALL_EXERCISES = [ex for day_list in PROGRAM.values() for ex in day_list]

@st.cache_data(ttl=600)
def load_data():
    records = worksheet.get_all_records()
    if not records:
        return pd.DataFrame(columns=['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RPE'])
    
    df = pd.DataFrame(records)
    for col in ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RPE']:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    if 'Side' not in df.columns: df['Side'] = 'Both'
    
    df['Side'] = df['Side'].replace('', 'Both').fillna('Both')
    df['Volume'] = df['Weight'] * df['Reps_or_Mins']
    df['Epley_1RM'] = df['Weight'] * (1 + df['Reps_or_Mins'] / 30)
    df['Brzycki_1RM'] = df['Weight'] * (36 / (37 - df['Reps_or_Mins']))
    
    # Ensure Date is a datetime object for rolling averages
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def save_data(df):
    df_to_save = df.drop(columns=['Volume', 'Epley_1RM', 'Brzycki_1RM'], errors='ignore').copy()
    df_to_save['Date'] = df_to_save['Date'].dt.strftime('%Y-%m-%d') # Convert back to string for Google Sheets
    df_to_save = df_to_save.fillna('')
    worksheet.clear()
    worksheet.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
    st.cache_data.clear()

df = load_data()

st.title("🔬 Sports Science Dashboard")

tab1, tab2, tab3 = st.tabs(["📝 Data Collection", "📊 Analytics Engine", "⚙️ Database"])

# --- TAB 1: DATA COLLECTION ---
with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        date_input = st.date_input("Date", date.today())
        bw_input = st.number_input("Daily Bodyweight (kg)", value=80.0, step=0.5)
    with col2:
        workout_day = st.selectbox("Select Workout Day", list(PROGRAM.keys()))
        selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day], default=[PROGRAM[workout_day][0]])
    
    st.write("---")
    
    if selected_exercises and "Cardio" not in workout_day:
        weights, reps, reps_l, reps_r, rpes = {}, {}, {}, {}, {}
        
        for exercise in selected_exercises:
            st.markdown(f"### {exercise}")
            is_unilateral = exercise in UNILATERAL_EXERCISES
            
            c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
            c1.markdown("**Set**"); c2.markdown("**Kg**"); c3.markdown("**Reps (L/R)**" if is_unilateral else "**Reps**"); c4.markdown("**RPE (1-10)**")
                
            for i in range(1, 4): # Defaulting to 3 sets for UI cleanliness
                key = f"{exercise}_{i}" 
                c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
                c1.markdown(f"<div style='margin-top: 8px;'><b>{i}</b></div>", unsafe_allow_html=True)
                weights[key] = c2.number_input("Kg", min_value=0.0, step=2.5, key=f"w_{key}", label_visibility="collapsed")
                
                if is_unilateral:
                    sc1, sc2 = c3.columns(2)
                    reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}", label_visibility="collapsed")
                    reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}", label_visibility="collapsed")
                else:
                    reps[key] = c3.number_input("Reps", min_value=0, step=1, key=f"r_{key}", label_visibility="collapsed")
                
                rpes[key] = c4.slider("RPE", 1.0, 10.0, 8.0, 0.5, key=f"rpe_{key}", label_visibility="collapsed")
            st.write("---")
            
        if st.button("Save To Database", type="primary"):
            new_rows = []
            for exercise in selected_exercises:
                is_unilateral = exercise in UNILATERAL_EXERCISES
                for i in range(1, 4):
                    key = f"{exercise}_{i}"
                    # Only save if reps were logged
                    if (is_unilateral and (reps_l[key] > 0 or reps_r[key] > 0)) or (not is_unilateral and reps[key] > 0):
                        base_data = {'Date': date_input, 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': 'None', 'Distance_km': 0.0, 'Bodyweight': bw_input, 'RPE': rpes[key]}
                        if is_unilateral:
                            if reps_l[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_l[key], 'Side': 'Left'})
                            if reps_r[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_r[key], 'Side': 'Right'})
                        else:
                            new_rows.append({**base_data, 'Reps_or_Mins': reps[key], 'Side': 'Both'})
            
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save_data(df)
            st.success(f"Logged {len(new_rows)} rows!")
            st.rerun()

# --- TAB 2: ANALYTICS ENGINE ---
with tab2:
    if df.empty:
        st.info("Awaiting Data...")
    else:
        # Filter out rest/cardio for lifting metrics
        lift_df = df[df['Reps_or_Mins'] > 0].copy()
        lift_df = lift_df[~lift_df['Exercise'].str.contains("Rowing|Bike|Rest", na=False)]
        
        at1, at2, at3, at4 = st.tabs(["👻 The Ghost", "📈 e1RM Velocity", "🔥 INOL & Volume", "🦵 Muscle Heatmap"])
        
        with at1:
            st.subheader("Historical Milestones")
            # Calculate exactly 1 year ago
            one_year_ago = pd.to_datetime(date.today()) - pd.DateOffset(years=1)
            # Find the closest workout around that time (within a 14 day window)
            past_workouts = lift_df[(lift_df['Date'] >= one_year_ago - pd.Timedelta(days=7)) & (lift_df['Date'] <= one_year_ago + pd.Timedelta(days=7))]
            
            if not past_workouts.empty:
                st.success(f"**Exactly one year ago:** You were grinding. Look at how far you've come.")
                st.dataframe(past_workouts[['Date', 'Exercise', 'Weight', 'Reps_or_Mins', 'Epley_1RM']].sort_values(by='Date').head(10))
            else:
                st.info("No data from exactly one year ago found yet. Keep building the database!")
                
            st.markdown("### All-Time PRs by Rep Range")
            pr_ex = st.selectbox("Select Exercise for PRs", lift_df['Exercise'].unique())
            pr_df = lift_df[lift_df['Exercise'] == pr_ex]
            
            c1, c2, c3, c4 = st.columns(4)
            try:
                c1.metric("1RM (Epley)", f"{pr_df['Epley_1RM'].max():.1f} kg")
                c2.metric("3RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 3]['Weight'].max():.1f} kg")
                c3.metric("5RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 5]['Weight'].max():.1f} kg")
                c4.metric("10RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 10]['Weight'].max():.1f} kg")
            except:
                st.warning("Not enough data for all rep ranges yet.")

        with at2:
            st.subheader("Progression Velocity & Plateaus")
            vel_ex = st.selectbox("Select Exercise", lift_df['Exercise'].unique(), key='vel_ex')
            v_df = lift_df[lift_df['Exercise'] == vel_ex].groupby('Date')['Epley_1RM'].max().reset_index()
            
            # Rolling Average (Plateau Detection) - Needs at least 3 sessions
            v_df['3_Session_Avg'] = v_df['Epley_1RM'].rolling(window=3).mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['Epley_1RM'], mode='markers', name='Daily e1RM', opacity=0.5))
            fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['3_Session_Avg'], mode='lines', name='Trend (Rolling Avg)', line=dict(color='#FF4B4B', width=3)))
            fig.update_layout(title="Plateau Detector (Smoothing out the noise)")
            st.plotly_chart(fig, use_container_width=True)

        with at3:
            st.subheader("INOL & Fatigue Curves")
            st.markdown("*(Intensity Number of Lifts)*")
            
            inol_ex = st.selectbox("Analyze Exercise", lift_df['Exercise'].unique(), key='inol_ex')
            i_df = lift_df[lift_df['Exercise'] == inol_ex].copy()
            
            # Approximate Max e1RM to calculate Intensity %
            global_max = i_df['Epley_1RM'].max()
            i_df['Intensity_%'] = (i_df['Weight'] / global_max) * 100
            # INOL Formula
            i_df['INOL'] = i_df['Reps_or_Mins'] / (100 - i_df['Intensity_%'])
            
            daily_inol = i_df.groupby('Date')['INOL'].sum().reset_index()
            
            fig2 = px.bar(daily_inol, x='Date', y='INOL', title="Daily Session INOL Score", color='INOL', color_continuous_scale='RdYlGn_r')
            fig2.add_hline(y=2.0, line_dash="dot", annotation_text="Overreaching Zone (>2.0)", annotation_position="top right")
            st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown("### Fatigue Degradation (Intra-Workout)")
            fatigue_df = i_df.groupby(['Date', 'Set_Number'])['Reps_or_Mins'].max().reset_index()
            fig3 = px.line(fatigue_df, x='Set_Number', y='Reps_or_Mins', color='Date', markers=True, title="Rep Drop-off Across Sets")
            st.plotly_chart(fig3, use_container_width=True)

        with at4:
            st.subheader("Muscle Volume Heatmap (Beta)")
            st.write("This maps your total tonnage directly to the primary/secondary muscles worked over the last 30 days.")
            
            # Filter for last 30 days
            recent_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=30)]
            
            muscle_vols = {}
            for index, row in recent_df.iterrows():
                ex = row['Exercise']
                vol = row['Volume']
                if ex in MUSCLE_MAP:
                    for muscle, multiplier in MUSCLE_MAP[ex].items():
                        muscle_vols[muscle] = muscle_vols.get(muscle, 0) + (vol * multiplier)
            
            if muscle_vols:
                heat_df = pd.DataFrame(list(muscle_vols.items()), columns=['Muscle', 'Total Load (kg)']).sort_values(by='Total Load (kg)')
                fig4 = px.bar(heat_df, x='Total Load (kg)', y='Muscle', orientation='h', color='Total Load (kg)', color_continuous_scale='Viridis')
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("Update the `MUSCLE_MAP` dictionary in your code to see the heatmap!")

# --- TAB 3: DATABASE ---
with tab3:
    edited_df = st.data_editor(df.drop(columns=['Volume', 'Epley_1RM', 'Brzycki_1RM'], errors='ignore'), num_rows="dynamic", use_container_width=True)
    if st.button("Save Changes"):
        save_data(edited_df)
        st.success("Database Saved!")
        st.rerun()
