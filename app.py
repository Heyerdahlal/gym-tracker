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

# --- CSS HACK: KILL THE + / - BUTTONS GLOBALLY ---
st.markdown("""
    <style>
    /* Chrome, Safari, Edge, Opera */
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
      -webkit-appearance: none;
      margin: 0;
    }
    /* Firefox */
    input[type=number] {
      -moz-appearance: textfield;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- PROGRAM & DICTIONARIES (VERSION 14.0) ---
PROGRAM = {
    "Day 1: Upper A (Horizontal Push/Pull)": [
        "T-Bar Landmine Row", "Dumbbell Bench Press", "Single-Arm Bench-Supported Dumbbell Row", 
        "Push-Ups", "Overhead Tricep Extension", "Dumbbell Hammer Curls", "Banded Crossovers", 
        "Chest-Supported Lateral Raise", "Chest-Supported Rear Delt Flye"
    ],
    "Day 2: Lower A (Strength & Quads)": [
        "Heavy Barbell Front Squat", "Heels-Elevated Landmine Squat", "Bulgarian Split Squats", 
        "Hamstring-Focused Roman Chair Extension", "Anchored Reverse Crunch", "Wall Tibialis Raises", 
        "Squat Wedge Dumbbell Calf Raises", "Half-Kneeling Pallof Press"
    ],
    "Day 3: Upper B (Vertical Push/Pull)": [
        "Neutral Grip Pull-Ups", "Band-Assisted Dips", "Landmine Press", 
        "Banded Face Pulls", "Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns", "Chest-Supported Lateral Raise"
    ],
    "Day 4: Lower B (Hinge, Power & Anti-Extension)": [
        "Romanian Deadlift (RDL)", "Heavy Russian Kettlebell Swings", "Barbell Hip Thrusts", 
        "Ab-Wheel Rollouts", "Nordic Curls", "Erector-Focused Roman Chair Extension", 
        "Squat Wedge Dumbbell Calf Raises", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"
    ],
    "Day 5: The Cardio Engine": [
        "4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"
    ],
    "🧬 Life Event (Sick/Travel)": [
        "Rest / Recovery / Frozen Week"
    ]
}

REP_TARGETS = {
    "T-Bar Landmine Row": "4 Sets × 8–10 Reps",
    "Dumbbell Bench Press": "4 Sets × 8–10 Reps",
    "Single-Arm Bench-Supported Dumbbell Row": "3 Sets × 10–12 Reps/arm",
    "Push-Ups": "3 Sets × 10–15 Reps",
    "Overhead Tricep Extension": "3 Sets × 12–15 Reps",
    "Dumbbell Hammer Curls": "3 Sets × 10–12 Reps",
    "Banded Crossovers": "3 Sets × 15–20 Reps",
    "Chest-Supported Lateral Raise": "4 Sets × 15–20 Reps",
    "Chest-Supported Rear Delt Flye": "4 Sets × 15–20 Reps",
    "Heavy Barbell Front Squat": "3 Sets × 4–6 Reps",
    "Heels-Elevated Landmine Squat": "4 Sets × 6–8 Reps",
    "Bulgarian Split Squats": "4 Sets × 8–10 Reps/leg",
    "Hamstring-Focused Roman Chair Extension": "3 Sets × 12–15 Reps",
    "Anchored Reverse Crunch": "3 Sets × 10–12 Reps",
    "Wall Tibialis Raises": "3 Sets × 15–20 Reps",
    "Squat Wedge Dumbbell Calf Raises": "4 Sets × 10–12 Reps",
    "Half-Kneeling Pallof Press": "3 Sets × 10–12 Reps/side",
    "Neutral Grip Pull-Ups": "4 Sets × 5–8 Reps",
    "Band-Assisted Dips": "4 Sets × 10–12 Reps",
    "Landmine Press": "3 Sets × 8–10 Reps",
    "Banded Face Pulls": "3 Sets × 15–20 Reps",
    "Incline Supinated Dumbbell Curls": "4 Sets × 10–12 Reps",
    "Banded Tricep Pushdowns": "3 Sets × 15–20 Reps",
    "Romanian Deadlift (RDL)": "4 Sets × 6–8 Reps",
    "Heavy Russian Kettlebell Swings": "3 Sets × 12–15 Reps",
    "Barbell Hip Thrusts": "3 Sets × 10–12 Reps",
    "Ab-Wheel Rollouts": "3 Sets × 8–10 Reps",
    "Nordic Curls": "3 Sets × 5–8 Reps",
    "Erector-Focused Roman Chair Extension": "3 Sets × 8–10 Reps",
    "Heavy Suitcase Holds": "3 Sets × 45 Seconds/side",
    "Front-Rack Kettlebell Marches": "3 Sets × 45 Seconds/side"
}

MUSCLE_MAP = {
    "T-Bar Landmine Row": {"Lats": 1.0, "Upper Back": 1.0, "Biceps": 0.5},
    "Dumbbell Bench Press": {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5},
    "Single-Arm Bench-Supported Dumbbell Row": {"Lats": 1.0, "Upper Back": 0.5, "Biceps": 0.5},
    "Push-Ups": {"Chest": 1.0, "Front Delts": 0.5, "Triceps": 0.5},
    "Overhead Tricep Extension": {"Triceps": 1.0},
    "Dumbbell Hammer Curls": {"Biceps": 1.0, "Forearms": 0.5},
    "Banded Crossovers": {"Chest": 1.0, "Front Delts": 0.5},
    "Chest-Supported Lateral Raise": {"Side Delts": 1.0},
    "Chest-Supported Rear Delt Flye": {"Rear Delts": 1.0, "Upper Back": 0.5},
    "Heavy Barbell Front Squat": {"Quads": 1.0, "Glutes": 0.5, "Erectors": 0.5},
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Hamstring-Focused Roman Chair Extension": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Anchored Reverse Crunch": {"Abs": 1.0},
    "Wall Tibialis Raises": {"Calves": 1.0},
    "Squat Wedge Dumbbell Calf Raises": {"Calves": 1.0},
    "Half-Kneeling Pallof Press": {"Obliques": 1.0, "Abs": 1.0},
    "Neutral Grip Pull-Ups": {"Lats": 1.0, "Biceps": 0.5, "Upper Back": 0.5},
    "Band-Assisted Dips": {"Chest": 1.0, "Triceps": 1.0, "Front Delts": 0.5},
    "Landmine Press": {"Front Delts": 1.0, "Chest": 0.5, "Triceps": 0.5},
    "Banded Face Pulls": {"Rear Delts": 1.0, "Upper Back": 0.5},
    "Incline Supinated Dumbbell Curls": {"Biceps": 1.0},
    "Banded Tricep Pushdowns": {"Triceps": 1.0},
    "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0, "Erectors": 0.5},
    "Heavy Russian Kettlebell Swings": {"Glutes": 1.0, "Hamstrings": 0.5, "Erectors": 0.5},
    "Barbell Hip Thrusts": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Ab-Wheel Rollouts": {"Abs": 1.0, "Erectors": 0.5},
    "Nordic Curls": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Erector-Focused Roman Chair Extension": {"Erectors": 1.0, "Glutes": 0.5},
    "Heavy Suitcase Holds": {"Obliques": 1.0, "Forearms": 0.5},
    "Front-Rack Kettlebell Marches": {"Abs": 1.0, "Quads": 0.5}
}

BW_MULTIPLIERS = {
    "Neutral Grip Pull-Ups": 0.95, 
    "Band-Assisted Dips": 0.95,
    "Push-Ups": 0.65, 
    "Nordic Curls": 0.60, 
    "Anchored Reverse Crunch": 0.40, 
    "Ab-Wheel Rollouts": 0.50,
    "Squat Wedge Dumbbell Calf Raises": 1.0, 
    "Bulgarian Split Squats": 0.85, 
    "Erector-Focused Roman Chair Extension": 0.50,
    "Glute-Focused Roman Chair Extension": 0.50,
    "Hamstring-Focused Roman Chair Extension": 0.50,
    "Heavy Barbell Front Squat": 0.85,
    "Wall Tibialis Raises": 0.30
}

BAND_SUBTRACTIONS = {
    "None": 0.0, "Yellow (13.6kg)": 13.6, "Red (22.6kg)": 22.6, 
    "Black (36.3kg)": 36.3, "Purple (45.4kg)": 45.4, 
    "Green (68.0kg)": 68.0, "Blue (88.5kg)": 88.5, "Orange (113.4kg)": 113.4
}

UNILATERAL_EXERCISES = ["Bulgarian Split Squats", "Single-Arm Bench-Supported Dumbbell Row", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
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
    
    baseline_cols = ['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS
    
    if not records:
        return pd.DataFrame(columns=baseline_cols)
    
    df = pd.DataFrame(records)
    
    numeric_cols = ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS
    for col in numeric_cols:
        if col not in df.columns: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    if 'Side' not in df.columns: df['Side'] = 'Both'
    df['Side'] = df['Side'].replace('', 'Both').fillna('Both')
    df['Date'] = pd.to_datetime(df['Date'])
    
    # --- THE NEW BAND MATH LOGIC ---
    ASSISTED_EXERCISES = ["Neutral Grip Pull-Ups", "Band-Assisted Dips"]
    RESISTED_EXERCISES = ["Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
    
    def calc_effective_weight(row):
        ex = row['Exercise']
        bw_mod = BW_MULTIPLIERS.get(ex, 0.0)
        base_body_load = row['Bodyweight'] * bw_mod
        
        peak_band_force = BAND_SUBTRACTIONS.get(row.get('Band', 'None'), 0.0)
        avg_band_force = peak_band_force * 0.5
        
        if ex in ASSISTED_EXERCISES:
            # The band helps you, so we subtract its force
            eff_wt = row['Weight'] + base_body_load - avg_band_force
        elif ex in RESISTED_EXERCISES:
            # The band fights you, so we add its force to your total weight
            eff_wt = row['Weight'] + base_body_load + avg_band_force
        else:
            # Standard free weight / bodyweight exercise with no bands
            eff_wt = row['Weight'] + base_body_load
            
        return max(eff_wt, 0.0) 
        
    df['Effective_Weight'] = df.apply(calc_effective_weight, axis=1)
    # --------------------------------
    
    # Separate lifting math from cardio math
    is_lift = ~df['Exercise'].str.contains("Rowing|Bike|Rest", na=False)
    df['Volume'] = 0.0
    df['Epley_1RM'] = 0.0
    
    df.loc[is_lift, 'Volume'] = df.loc[is_lift, 'Effective_Weight'] * df.loc[is_lift, 'Reps_or_Mins']
    df.loc[is_lift, 'Epley_1RM'] = df.loc[is_lift, 'Effective_Weight'] * (1 + df.loc[is_lift, 'Reps_or_Mins'] / 30)
    
    return df

# FIX: New function for appending rows efficiently
def append_new_data(new_rows_df):
    df_to_append = new_rows_df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore').copy()
    df_to_append['Date'] = pd.to_datetime(df_to_append['Date']).dt.strftime('%Y-%m-%d')
    df_to_append = df_to_append.fillna('')
    worksheet.append_rows(df_to_append.values.tolist())
    st.cache_data.clear()

# Keeps original functionality for Tab 3 bulk edits
def overwrite_database(df):
    df_to_save = df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore').copy()
    df_to_save['Date'] = pd.to_datetime(df_to_save['Date']).dt.strftime('%Y-%m-%d')
    df_to_save = df_to_save.fillna('')
    worksheet.clear()
    worksheet.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
    st.cache_data.clear()

df = load_data()

st.title("🔬 Sports Science Dashboard")

tab1, tab2, tab3 = st.tabs(["📝 Data Collection", "📊 Analytics Engine", "⚙️ Database"])

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
            exercise = selected_exercises[0]
            st.markdown(f"### {exercise} (Garmin Data Integration)")
            
            # FIX: Wrapped in st.form to prevent state ghosts
            with st.form("cardio_form", clear_on_submit=True):
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
                
                submit_cardio = st.form_submit_button("Save Cardio Data", type="primary")
                
                if submit_cardio:
                    cardio_data = {
                        'Date': date_input, 'Workout_Day': workout_day, 'Exercise': exercise, 
                        'Set_Number': 1, 'Weight': 0.0, 'Band': 'None', 'Distance_km': distance, 
                        'Reps_or_Mins': duration, 'Bodyweight': bw_input, 'RIR': 0.0, 'Side': 'Both',
                        'Avg_HR': avg_hr, 'Max_HR': max_hr, 'Avg_Resp': avg_resp,
                        'Z1_Mins': z1, 'Z2_Mins': z2, 'Z3_Mins': z3, 'Z4_Mins': z4, 'Z5_Mins': z5
                    }
                    new_df = pd.DataFrame([cardio_data])
                    append_new_data(new_df)
                    st.success("High-Fidelity Cardio Data Saved!")
                    st.rerun()

      else:
            default_sets, _ = get_target_reps_and_sets(selected_exercises[0])
            num_sets = st.number_input("🎯 Total Rounds (Sets) to perform:", min_value=1, max_value=10, value=default_sets, step=1)
            st.write("---")
            
            # --- NEW: AUTOMATED PROGRESSIVE OVERLOAD TARGETS ---
            st.markdown("#### 📈 Target to Beat (Last Session)")
            for exercise in selected_exercises:
                ex_df = df[(df['Exercise'] == exercise) & (df['Reps_or_Mins'] > 0)]
                if not ex_df.empty:
                    last_date = ex_df['Date'].max()
                    last_session = ex_df[ex_df['Date'] == last_date]
                    
                    # Find the hardest set from that last session based on Epley 1RM
                    best_set = last_session.loc[last_session['Epley_1RM'].idxmax()]
                    target_weight = best_set['Weight']
                    target_reps = int(best_set['Reps_or_Mins'])
                    target_band = best_set['Band']
                    
                    band_str = f" [{target_band} Band]" if target_band != "None" else ""
                    st.success(f"**{exercise}:** Last done {last_date.strftime('%b %d')} ➔ **{target_weight}kg × {target_reps} reps**{band_str}")
                else:
                    st.info(f"**{exercise}:** No history. Establish your baseline today!")
            
            st.write("---")
            # ---------------------------------------------------
            
            # FIX: Wrapped in st.form to prevent state ghosts
            with st.form("lifting_form", clear_on_submit=True):
                weights, reps, reps_l, reps_r, rirs, bands = {}, {}, {}, {}, {}, {}
                
                for i in range(1, num_sets + 1):
                    st.markdown(f"#### 🔁 Round {i}")
                    
                    for exercise in selected_exercises:
                        is_unilateral = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
                        
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
                
                submit_lifts = st.form_submit_button("Save To Database", type="primary")
                
                if submit_lifts:
                    new_rows = []
                    for exercise in selected_exercises:
                        is_unilateral = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
                        
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
                    
                    if new_rows:
                        new_df = pd.DataFrame(new_rows)
                        append_new_data(new_df)
                        st.success(f"Logged {len(new_rows)} rows!")
                        st.rerun()
                    else:
                        st.warning("No reps logged. Database was not updated.")

with tab2:
    if df.empty:
        st.info("Awaiting Data...")
    else:
        lift_df = df[(df['Reps_or_Mins'] > 0) & (~df['Exercise'].str.contains("Rowing|Bike|Rest", na=False))].copy()
        cardio_df = df[df['Exercise'].str.contains("Rowing|Bike", na=False)].copy()
        
        at1, at2, at3, at4, at5 = st.tabs(["👻 The Ghost", "📈 e1RM Velocity", "🔥 INOL & Volume", "🦵 Muscle Sets", "🫀 Cardio Engine"])
        
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
                
                # FIX: Check if dataframe is empty before calculating max to prevent crash
                if not pr_df.empty:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("1RM (Epley)", f"{pr_df['Epley_1RM'].max():.1f} kg")
                    c2.metric("3RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 3]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 3].empty else "N/A")
                    c3.metric("5RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 5]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 5].empty else "N/A")
                    c4.metric("10RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 10]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 10].empty else "N/A")
                else:
                    st.warning("Not enough data for this exercise yet.")

        with at2:
            st.subheader("Progression Velocity & Plateaus")
            if not lift_df.empty:
                vel_ex = st.selectbox("Select Exercise", lift_df['Exercise'].unique(), key='vel_ex')
                v_df = lift_df[lift_df['Exercise'] == vel_ex].groupby('Date')['Epley_1RM'].max().reset_index()
                
                # FIX: Check if dataframe is empty before plotting
                if not v_df.empty:
                    v_df['3_Session_Avg'] = v_df['Epley_1RM'].rolling(window=3).mean()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['Epley_1RM'], mode='markers', name='Daily e1RM', opacity=0.5))
                    fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['3_Session_Avg'], mode='lines', name='Trend (Rolling Avg)', line=dict(color='#FF4B4B', width=3)))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Log some sessions for this exercise to see the velocity trend.")

        with at3:
            st.subheader("INOL & Fatigue Curves")
            if not lift_df.empty:
                inol_ex = st.selectbox("Analyze Exercise", lift_df['Exercise'].unique(), key='inol_ex')
                i_df = lift_df[lift_df['Exercise'] == inol_ex].copy()
                
                # --- NEW: SYSTEMIC FATIGUE MODIFIERS ---
                SYSTEMIC_MODIFIERS = {
                    "Romanian Deadlift (RDL)": 1.0, "Heavy Barbell Front Squat": 1.0,
                    "Neutral Grip Pull-Ups": 0.8, "Bulgarian Split Squats": 0.8, "Heavy Russian Kettlebell Swings": 0.8, "Barbell Hip Thrusts": 0.8, "Heels-Elevated Landmine Squat": 0.8,
                    "T-Bar Landmine Row": 0.7, "Dumbbell Bench Press": 0.7, "Band-Assisted Dips": 0.7, "Landmine Press": 0.7,
                    "Single-Arm Bench-Supported Dumbbell Row": 0.6, "Nordic Curls": 0.6, "Front-Rack Kettlebell Marches": 0.6,
                    "Push-Ups": 0.5, "Hamstring-Focused Roman Chair Extension": 0.5, "Erector-Focused Roman Chair Extension": 0.5, "Ab-Wheel Rollouts": 0.5, "Heavy Suitcase Holds": 0.5,
                    "Chest-Supported Lateral Raise": 0.3, "Chest-Supported Rear Delt Flye": 0.3, "Overhead Tricep Extension": 0.3, "Dumbbell Hammer Curls": 0.3, "Banded Crossovers": 0.3, "Incline Supinated Dumbbell Curls": 0.3, "Banded Tricep Pushdowns": 0.3, "Banded Face Pulls": 0.3, "Wall Tibialis Raises": 0.3, "Squat Wedge Dumbbell Calf Raises": 0.3, "Half-Kneeling Pallof Press": 0.3, "Anchored Reverse Crunch": 0.3
                }
                
                # FIX: Empty check
                if not i_df.empty:
                    global_max = i_df['Epley_1RM'].max()
                    i_df['Intensity_%'] = (i_df['Effective_Weight'] / global_max) * 100
                    i_df['Intensity_%'] = i_df['Intensity_%'].clip(upper=99)
                    
                    # --- NEW: APPLYING THE MODIFIER ---
                    fatigue_factor = SYSTEMIC_MODIFIERS.get(inol_ex, 0.5) # Defaults to a mid-tier 0.5 if an exercise isn't in the list
                    i_df['INOL'] = (i_df['Reps_or_Mins'] / (100 - i_df['Intensity_%'])) * fatigue_factor
                    
                    daily_inol = i_df.groupby('Date')['INOL'].sum().reset_index()
                    fig2 = px.bar(
                    daily_inol, 
                    x='Date', 
                    y='INOL', 
                    title="Daily Session INOL Score (Adjusted for Systemic Load)", 
                    color='INOL', 
                    color_continuous_scale='RdYlGn_r',
                    range_color=[0, 2.0] # This forces 0.48 to stay green!
                    )
                    fig2.add_hline(y=2.0, line_dash="dot", annotation_text="Overreaching (>2.0)")
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    st.markdown("### Fatigue Degradation (Intra-Workout)")
                    fatigue_df = i_df.groupby(['Date', 'Set_Number'])['Reps_or_Mins'].max().reset_index()
                    fig3 = px.line(fatigue_df, x='Set_Number', y='Reps_or_Mins', color='Date', markers=True, title="Rep Drop-off Across Sets")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("No data available for INOL calculation yet.")

        with at4:
            st.subheader("Muscle Volume (Hard Sets)")
            st.write("This tracks **Total Hard Sets** per muscle over the last 30 days. It equalizes heavy compound lifts and light isolation work to reveal true training imbalances.")
            
            if not lift_df.empty:
                recent_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=30)]
                muscle_sets = {}
                for index, row in recent_df.iterrows():
                    ex = row['Exercise']
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items():
                            muscle_sets[muscle] = muscle_sets.get(muscle, 0) + (1 * multiplier)
                
                if muscle_sets:
                    heat_df = pd.DataFrame(list(muscle_sets.items()), columns=['Muscle', 'Total Sets']).sort_values(by='Total Sets')
                    fig4 = px.bar(heat_df, x='Total Sets', y='Muscle', orientation='h', 
                                  color='Total Sets', color_continuous_scale='Inferno',
                                  title="Set Distribution (Last 30 Days)")
                    
                    fig4.add_vline(x=40, line_dash="dash", line_color="#00CC96", annotation_text="MEV (40/mo)", annotation_position="top left")
                    fig4.add_vline(x=80, line_dash="dash", line_color="#EF553B", annotation_text="MRV (80/mo)", annotation_position="top left")
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
                
                if not cx_df.empty:
                    if "Rowing" in c_ex:
                        cx_df['Pace_Sec'] = (cx_df['Reps_or_Mins'] * 60) / (cx_df['Distance_km'] * 1000 / 500)
                        cx_df['Metric_Value'] = cx_df['Pace_Sec']
                        metric_title = "Avg Split Pace (Seconds per 500m) 📉 Lower is Better"
                    else:
                        cx_df['Speed_kmh'] = cx_df['Distance_km'] / (cx_df['Reps_or_Mins'] / 60)
                        cx_df['Metric_Value'] = cx_df['Speed_kmh']
                        metric_title = "Avg Speed (km/h) 📈 Higher is Better"
                    
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
                    
                    st.markdown("### Heart Rate Zone Distribution")
                    zone_df = cx_df[['Date', 'Z1_Mins', 'Z2_Mins', 'Z3_Mins', 'Z4_Mins', 'Z5_Mins']].melt(id_vars='Date', var_name='Zone', value_name='Minutes')
                    zone_df['Zone'] = zone_df['Zone'].str.replace('_Mins', '')
                    
                    zone_colors = {'Z1': '#4287f5', 'Z2': '#42f56f', 'Z3': '#f5d742', 'Z4': '#f58442', 'Z5': '#f54242'}
                    
                    fig_zones = px.bar(zone_df, x='Date', y='Minutes', color='Zone', title="Time in Zones per Session", color_discrete_map=zone_colors)
                    st.plotly_chart(fig_zones, use_container_width=True)

with tab3:
    st.subheader("⚙️ Database Editor")
    st.write("Loading thousands of rows can cause lag. Select how much recent history you need to edit.")
    
    # 1. Choose how far back to look
    days_to_edit = st.slider("Days of history to load", min_value=7, max_value=365, value=30, step=7)
    cutoff_date = pd.to_datetime(date.today()) - pd.Timedelta(days=days_to_edit)
    
    # 2. Split the database into "Hidden Historical" and "Visible Recent"
    historical_df = df[df['Date'] < cutoff_date].copy()
    recent_df = df[df['Date'] >= cutoff_date].copy()
    
    # 3. Only put the recent data in the interactive editor
    edited_recent = st.data_editor(
        recent_df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore'), 
        num_rows="dynamic", 
        use_container_width=True
    )
    
    if st.button("Save Changes", type="primary"):
        # 4. Stitch the hidden history and the edited recent data back together
        final_df = pd.concat([historical_df, edited_recent], ignore_index=True)
        
        # 5. Save the combined, complete database
        overwrite_database(final_df)
        st.success("Database Saved safely!")
        st.rerun()
