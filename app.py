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

st.set_page_config(page_title="My Gym Tracker", page_icon="🏋️‍♂️", layout="wide")

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

# --- PROGRAM & DICTIONARIES ---
PROGRAM = {
    "Day 1: Quad Focus & Verticality": ["Heels-Elevated Landmine Squat", "Neutral Grip Pull-Ups", "Band-Assisted Dips", "Bulgarian Split Squats", "Nordic Curls", "Banded Face Pulls", "Anchored Reverse Crunch", "Glute-Focused Roman Chair Extension", "Squat Wedge Dumbbell Calf Raises"],
    "Day 2: Hinge Focus & Horizontal Load": ["Romanian Deadlift (RDL)", "Barbell Hip Thrusts", "T-Bar Landmine Row", "Dumbbell Bench Press", "Incline Bar Push-Ups", "Meadows Row", "Overhead Tricep Extension", "Banded Crossovers", "Ab-Wheel Rollouts"],
    "Day 3: Hybrid Hypertrophy & Stability": ["Erector-Focused Roman Chair Extension", "Landmine Press", "Chest-Supported Lateral Raise", "Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"],
    "Thursday/Friday: Cardio": ["4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"]
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
    "Landmine Press": "3 Sets × 8–10 Reps",
    "Chest-Supported Lateral Raise": "4 Sets × 15–20 Reps",
    "Incline Supinated Dumbbell Curls": "4 Sets × 10–12 Reps",
    "Banded Tricep Pushdowns": "4 Sets × 15–20 Reps",
    "Half-Kneeling Pallof Press": "3 Sets × 10–12 Reps/side",
    "Heavy Suitcase Holds": "3 Sets × 45 Seconds/side",
    "Front-Rack Kettlebell Marches": "3 Sets × 45 Seconds/side"
}

MUSCLE_MAP = {
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Neutral Grip Pull-Ups": {"Lats": 1.0, "Biceps": 0.5, "Upper Back": 0.5},
    "Band-Assisted Dips": {"Chest": 1.0, "Triceps": 1.0, "Front Delts": 0.5},
    "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Nordic Curls": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Banded Face Pulls": {"Rear Delts": 1.0, "Upper Back": 0.5},
    "Anchored Reverse Crunch": {"Abs": 1.0},
    "Glute-Focused Roman Chair Extension": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Squat Wedge Dumbbell Calf Raises": {"Calves": 1.0},
    "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0, "Erectors": 0.5},
    "Barbell Hip Thrusts": {"Glutes": 1.0, "Hamstrings": 0.5},
    "T-Bar Landmine Row": {"Lats": 1.0, "Upper Back": 1.0, "Biceps": 0.5},
    "Dumbbell Bench Press": {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5},
    "Incline Bar Push-Ups": {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5},
    "Meadows Row": {"Upper Back": 1.0, "Lats": 0.5, "Biceps": 0.5},
    "Overhead Tricep Extension": {"Triceps": 1.0},
    "Banded Crossovers": {"Chest": 1.0, "Front Delts": 0.5},
    "Ab-Wheel Rollouts": {"Abs": 1.0, "Erectors": 0.5},
    "Erector-Focused Roman Chair Extension": {"Erectors": 1.0, "Glutes": 0.5},
    "Landmine Press": {"Front Delts": 1.0, "Chest": 0.5, "Triceps": 0.5},
    "Chest-Supported Lateral Raise": {"Side Delts": 1.0},
    "Incline Supinated Dumbbell Curls": {"Biceps": 1.0},
    "Banded Tricep Pushdowns": {"Triceps": 1.0},
    "Half-Kneeling Pallof Press": {"Obliques": 1.0, "Abs": 1.0},
    "Heavy Suitcase Holds": {"Obliques": 1.0, "Forearms": 0.5},
    "Front-Rack Kettlebell Marches": {"Abs": 1.0, "Quads": 0.5}
}

BW_MULTIPLIERS = {
    "Neutral Grip Pull-Ups": 0.95, 
    "Band-Assisted Dips": 0.95,
    "Incline Bar Push-Ups": 0.50, 
    "Nordic Curls": 0.60, 
    "Anchored Reverse Crunch": 0.40, 
    "Ab-Wheel Rollouts": 0.50,
    "Squat Wedge Dumbbell Calf Raises": 1.0, 
    "Bulgarian Split Squats": 0.85, 
    "Erector-Focused Roman Chair Extension": 0.50,
    "Glute-Focused Roman Chair Extension": 0.50
}

BAND_SUBTRACTIONS = {
    "None": 0.0, "Yellow (13.6kg)": 13.6, "Red (22.6kg)": 22.6, 
    "Black (36.3kg)": 36.3, "Purple (45.4kg)": 45.4, 
    "Green (68.0kg)": 68.0, "Blue (88.5kg)": 88.5, "Orange (113.4kg)": 113.4
}

UNILATERAL_EXERCISES = ["Bulgarian Split Squats", "Meadows Row", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
ALL_EXERCISES = [ex for day_list in PROGRAM.values() for ex in day_list]
CARDIO_COLUMNS = ['Avg_HR', 'Max_HR', 'Avg_Resp', 'Z1_Mins', 'Z2_Mins', 'Z3_Mins', 'Z4_Mins', 'Z5_Mins']

def get_target_reps_and_sets(exercise_name):
    target_str = REP_TARGETS.get(exercise_name, "")
    sets_match = re.search(r'(\d+)\s*Sets', target_str, re.IGNORECASE)
    reps_match = re.search(r'–(\d+)\s*Reps', target_str, re.IGNORECASE)
    target_sets = int(sets_match.group(1)) if sets_match else 3
    top_rep = int(reps_match.group(1)) if reps_match else 8
    return target_sets, top_rep

@st.cache_data(ttl=600)
def load_data():
    records = worksheet.get_all_records()
    
    # Define the baseline columns including the new Cardio ones
    baseline_cols = ['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS
    
    if not records:
        return pd.DataFrame(columns=baseline_cols)
    
    df = pd.DataFrame(records)
    
    # Ensure all columns exist and are numeric where appropriate
    numeric_cols = ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS
    for col in numeric_cols:
        if col not in df.columns: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    if 'Side' not in df.columns: df['Side'] = 'Both'
    df['Side'] = df['Side'].replace('', 'Both').fillna('Both')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Hooke's Law & Effective Weight Calculation
    def calc_effective_weight(row):
        ex = row['Exercise']
        bw_mod = BW_MULTIPLIERS.get(ex, 0.0)
        base_body_load = row['Bodyweight'] * bw_mod
        
        peak_band_assistance = BAND_SUBTRACTIONS.get(row.get('Band', 'None'), 0.0)
        avg_band_assistance = peak_band_assistance * 0.5
        
        eff_wt = row['Weight'] + base_body_load - avg_band_assistance
        return max(eff_wt, 0.0) 
        
    df['Effective_Weight'] = df.apply(calc_effective_weight, axis=1)
    df['Volume'] = df['Effective_Weight'] * df['Reps_or_Mins']
    df['Epley_1RM'] = df['Effective_Weight'] * (1 + df['Reps_or_Mins'] / 30)
    return df

def save_data(df):
    df_to_save = df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore').copy()
    df_to_save['Date'] = df_to_save['Date'].dt.strftime('%Y-%m-%d')
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
    
    if selected_exercises:
        is_cardio = "Cardio" in workout_day
        
        if is_cardio:
            exercise = selected_exercises[0] # Usually only log one cardio session at a time
            st.markdown(f"### {exercise} (Garmin Data Integration)")
            
            c1, c2 = st.columns(2)
            with c1:
                duration = st.number_input("Duration (Minutes)", min_value=1.0, value=60.0, step=1.0)
                distance = st.number_input("Distance (km)", min_value=0.0, value=10.0, step=0.1)
                avg_resp = st.number_input("Avg Respiration (brpm)", min_value=0.0, value=20.0, step=1.0)
            with c2:
                avg_hr = st.number_input("Avg Heart Rate (bpm)", min_value=40.0, value=130.0, step=1.0)
                max_hr = st.number_input("Max Heart Rate (bpm)", min_value=40.0, value=165.0, step=1.0)
            
            st.markdown("#### ⏱️ Time in HR Zones (Minutes)")
            zc1, zc2, zc3, zc4, zc5 = st.columns(5)
            z1 = zc1.number_input("Zone 1", min_value=0.0, step=1.0)
            z2 = zc2.number_input("Zone 2", min_value=0.0, step=1.0)
            z3 = zc3.number_input("Zone 3", min_value=0.0, step=1.0)
            z4 = zc4.number_input("Zone 4", min_value=0.0, step=1.0)
            z5 = zc5.number_input("Zone 5", min_value=0.0, step=1.0)
            
            if st.button("Save Cardio Data", type="primary"):
                cardio_data = {
                    'Date': date_input, 'Workout_Day': workout_day, 'Exercise': exercise, 
                    'Set_Number': 1, 'Weight': 0.0, 'Band': 'None', 'Distance_km': distance, 
                    'Reps_or_Mins': duration, 'Bodyweight': bw_input, 'RIR': 0.0, 'Side': 'Both',
                    'Avg_HR': avg_hr, 'Max_HR': max_hr, 'Avg_Resp': avg_resp,
                    'Z1_Mins': z1, 'Z2_Mins': z2, 'Z3_Mins': z3, 'Z4_Mins': z4, 'Z5_Mins': z5
                }
                df = pd.concat([df, pd.DataFrame([cardio_data])], ignore_index=True)
                save_data(df)
                st.success("High-Fidelity Cardio Data Saved!")
                st.rerun()

        else:
            default_sets, _ = get_target_reps_and_sets(selected_exercises[0])
            num_sets = st.number_input("🎯 Total Rounds (Sets) to perform:", min_value=1, max_value=10, value=default_sets, step=1)
            st.write("---")
            
            weights, reps, reps_l, reps_r, rirs, bands = {}, {}, {}, {}, {}, {}
            
            for i in range(1, num_sets + 1):
                st.markdown(f"#### 🔁 Round {i}")
                
                for exercise in selected_exercises:
                    is_unilateral = exercise in UNILATERAL_EXERCISES
                    uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press"]
                    
                    _, top_rep = get_target_reps_and_sets(exercise)
                    st.markdown(f"**{exercise}** *(Target: {top_rep} reps)*")
                    
                    key = f"{exercise}_{i}" 
                    
                    if uses_band:
                        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 2])
                        weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, key=f"w_{key}")
                        if is_unilateral:
                            sc1, sc2 = c2.columns(2)
                            reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                            reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                        else:
                            reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                        bands[key] = c3.selectbox("Band", list(BAND_SUBTRACTIONS.keys()), key=f"b_{key}")
                        rirs[key] = c4.slider("RIR (Reps in Reserve)", 0, 5, 2, 1, key=f"rir_{key}")
                    else:
                        c1, c2, c3 = st.columns([1, 1, 2])
                        weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, key=f"w_{key}")
                        if is_unilateral:
                            sc1, sc2 = c2.columns(2)
                            reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                            reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                        else:
                            reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                        rirs[key] = c3.slider("RIR (Reps in Reserve)", 0, 5, 2, 1, key=f"rir_{key}")
                        
                st.write("---") 
                
            if st.button("Save To Database", type="primary"):
                new_rows = []
                for exercise in selected_exercises:
                    is_unilateral = exercise in UNILATERAL_EXERCISES
                    uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press"]
                    
                    for i in range(1, num_sets + 1):
                        key = f"{exercise}_{i}"
                        band_val = bands[key] if uses_band else "None"
                        
                        if (is_unilateral and (reps_l[key] > 0 or reps_r[key] > 0)) or (not is_unilateral and reps[key] > 0):
                            base_data = {
                                'Date': date_input, 'Workout_Day': workout_day, 'Exercise': exercise, 
                                'Set_Number': i, 'Weight': weights[key], 'Band': band_val, 
                                'Distance_km': 0.0, 'Bodyweight': bw_input, 'RIR': rirs[key],
                                'Avg_HR': 0.0, 'Max_HR': 0.0, 'Avg_Resp': 0.0,
                                'Z1_Mins': 0.0, 'Z2_Mins': 0.0, 'Z3_Mins': 0.0, 'Z4_Mins': 0.0, 'Z5_Mins': 0.0
                            }
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
        # Separate datasets for Lifting vs Cardio
        lift_df = df[(df['Reps_or_Mins'] > 0) & (~df['Exercise'].str.contains("Rowing|Bike|Rest", na=False))].copy()
        cardio_df = df[df['Exercise'].str.contains("Rowing|Bike", na=False)].copy()
        
        at1, at2, at3, at4, at5 = st.tabs(["👻 The Ghost", "📈 e1RM Velocity", "🔥 INOL & Volume", "🦵 Muscle Heatmap", "🫀 Cardio Engine"])
        
        # ... [Tabs at1 to at4 remain identical to previous versions] ...
        with at1:
            st.subheader("Historical Milestones")
            if not lift_df.empty:
                one_year_ago = pd.to_datetime(date.today()) - pd.DateOffset(years=1)
                past_workouts = lift_df[(lift_df['Date'] >= one_year_ago - pd.Timedelta(days=7)) & (lift_df['Date'] <= one_year_ago + pd.Timedelta(days=7))]
                if not past_workouts.empty:
                    st.success(f"**Exactly one year ago:** You were grinding. Look at how far you've come.")
                    st.dataframe(past_workouts[['Date', 'Exercise', 'Effective_Weight', 'Reps_or_Mins', 'Epley_1RM']].sort_values(by='Date').head(10))
                else:
                    st.info("No data from exactly one year ago found yet.")
                    
                st.markdown("### All-Time PRs by Rep Range")
                pr_ex = st.selectbox("Select Exercise for PRs", lift_df['Exercise'].unique())
                pr_df = lift_df[lift_df['Exercise'] == pr_ex]
                c1, c2, c3, c4 = st.columns(4)
                try:
                    c1.metric("1RM (Epley)", f"{pr_df['Epley_1RM'].max():.1f} kg")
                    c2.metric("3RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 3]['Effective_Weight'].max():.1f} kg")
                    c3.metric("5RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 5]['Effective_Weight'].max():.1f} kg")
                    c4.metric("10RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 10]['Effective_Weight'].max():.1f} kg")
                except:
                    st.warning("Not enough data for all rep ranges yet.")

        with at2:
            st.subheader("Progression Velocity & Plateaus")
            if not lift_df.empty:
                vel_ex = st.selectbox("Select Exercise", lift_df['Exercise'].unique(), key='vel_ex')
                v_df = lift_df[lift_df['Exercise'] == vel_ex].groupby('Date')['Epley_1RM'].max().reset_index()
                v_df['3_Session_Avg'] = v_df['Epley_1RM'].rolling(window=3).mean()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['Epley_1RM'], mode='markers', name='Daily e1RM', opacity=0.5))
                fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['3_Session_Avg'], mode='lines', name='Trend (Rolling Avg)', line=dict(color='#FF4B4B', width=3)))
                st.plotly_chart(fig, use_container_width=True)

        with at3:
            st.subheader("INOL & Fatigue Curves")
            if not lift_df.empty:
                inol_ex = st.selectbox("Analyze Exercise", lift_df['Exercise'].unique(), key='inol_ex')
                i_df = lift_df[lift_df['Exercise'] == inol_ex].copy()
                global_max = i_df['Epley_1RM'].max()
                i_df['Intensity_%'] = (i_df['Effective_Weight'] / global_max) * 100
                i_df['Intensity_%'] = i_df['Intensity_%'].clip(upper=99)
                i_df['INOL'] = i_df['Reps_or_Mins'] / (100 - i_df['Intensity_%'])
                daily_inol = i_df.groupby('Date')['INOL'].sum().reset_index()
                fig2 = px.bar(daily_inol, x='Date', y='INOL', title="Daily Session INOL Score", color='INOL', color_continuous_scale='RdYlGn_r')
                fig2.add_hline(y=2.0, line_dash="dot", annotation_text="Overreaching (>2.0)")
                st.plotly_chart(fig2, use_container_width=True)
                
                st.markdown("### Fatigue Degradation (Intra-Workout)")
                fatigue_df = i_df.groupby(['Date', 'Set_Number'])['Reps_or_Mins'].max().reset_index()
                fig3 = px.line(fatigue_df, x='Set_Number', y='Reps_or_Mins', color='Date', markers=True, title="Rep Drop-off Across Sets")
                st.plotly_chart(fig3, use_container_width=True)

        with at4:
            st.subheader("Muscle Volume Heatmap")
            if not lift_df.empty:
                recent_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=30)]
                muscle_vols = {}
                for index, row in recent_df.iterrows():
                    ex, vol = row['Exercise'], row['Volume']
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items():
                            muscle_vols[muscle] = muscle_vols.get(muscle, 0) + (vol * multiplier)
                if muscle_vols:
                    heat_df = pd.DataFrame(list(muscle_vols.items()), columns=['Muscle', 'Total Load (kg)']).sort_values(by='Total Load (kg)')
                    fig4 = px.bar(heat_df, x='Total Load (kg)', y='Muscle', orientation='h', color='Total Load (kg)', color_continuous_scale='Viridis')
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Log some data to populate the heatmap!")

        with at5:
            st.subheader("🫀 Cardio Engine Analytics")
            if cardio_df.empty:
                st.info("Log a cardio session with your Garmin data to see analytics.")
            else:
                c_ex = st.selectbox("Select Cardio Type", cardio_df['Exercise'].unique())
                cx_df = cardio_df[cardio_df['Exercise'] == c_ex].copy()
                
                # Biomechanical Split/Speed Calcs
                if "Rowing" in c_ex:
                    # Pace per 500m (in seconds)
                    cx_df['Pace_Sec'] = (cx_df['Reps_or_Mins'] * 60) / (cx_df['Distance_km'] * 1000 / 500)
                    cx_df['Metric_Value'] = cx_df['Pace_Sec']
                    metric_title = "Avg Split Pace (Seconds per 500m) 📉 Lower is Better"
                else:
                    # Speed in km/h
                    cx_df['Speed_kmh'] = cx_df['Distance_km'] / (cx_df['Reps_or_Mins'] / 60)
                    cx_df['Metric_Value'] = cx_df['Speed_kmh']
                    metric_title = "Avg Speed (km/h) 📈 Higher is Better"
                
                # Aerobic Efficiency Chart
                st.markdown("### Aerobic Efficiency")
                st.write("*Compare your external mechanical output (Speed/Pace) against your internal physiological cost (Heart Rate).*")
                
                fig_aerobic = go.Figure()
                fig_aerobic.add_trace(go.Bar(x=cx_df['Date'], y=cx_df['Metric_Value'], name='Speed/Pace Output', marker_color='#1f77b4', yaxis='y1'))
                fig_aerobic.add_trace(go.Scatter(x=cx_df['Date'], y=cx_df['Avg_HR'], name='Avg Heart Rate', mode='lines+markers', line=dict(color='#FF4B4B', width=3), yaxis='y2'))
                
                fig_aerobic.update_layout(
                    yaxis=dict(title=metric_title, side='left'),
                    yaxis2=dict(title='Avg HR (bpm)', side='right', overlaying='y', showgrid=False),
                    hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_aerobic, use_container_width=True)
                
                # Zone Distribution
                st.markdown("### Heart Rate Zone Distribution")
                zone_df = cx_df[['Date', 'Z1_Mins', 'Z2_Mins', 'Z3_Mins', 'Z4_Mins', 'Z5_Mins']].melt(id_vars='Date', var_name='Zone', value_name='Minutes')
                zone_df['Zone'] = zone_df['Zone'].str.replace('_Mins', '')
                
                # Custom colors for HR Zones (Blue to Red)
                zone_colors = {'Z1': '#4287f5', 'Z2': '#42f56f', 'Z3': '#f5d742', 'Z4': '#f58442', 'Z5': '#f54242'}
                
                fig_zones = px.bar(zone_df, x='Date', y='Minutes', color='Zone', title="Time in Zones per Session", color_discrete_map=zone_colors)
                st.plotly_chart(fig_zones, use_container_width=True)

with tab3:
    edited_df = st.data_editor(df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore'), num_rows="dynamic", use_container_width=True)
    if st.button("Save Changes"):
        save_data(edited_df)
        st.success("Database Saved!")
        st.rerun()
