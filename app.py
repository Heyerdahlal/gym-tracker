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
from garminconnect import Garmin

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

# --- PROGRAM & DICTIONARIES (VERSION 21.0) ---
PROGRAM = {
    "Day 1: Upper A (Horizontal Push/Pull)": {
        "Block 1 (Superset): T-Bar Row & DB Bench": ["T-Bar Landmine Row", "Dumbbell Bench Press"],
        "Block 2 (Superset): DB Row & Push-Ups": ["Single-Arm Bench-Supported Dumbbell Row", "Push-Ups"],
        "Block 3 (Tri-Set): Triceps, Biceps & Chest": ["Overhead Tricep Extension", "Dumbbell Hammer Curls", "Banded Crossovers"],
        "Block 4 (Superset): Lateral & Rear Delts": ["Chest-Supported Lateral Raise", "Chest-Supported Rear Delt Flye"]
    },
    "Day 2: Lower A (Strength, Quads & Armor)": {
        "Block 1: Heavy Front Squat": ["Heavy Barbell Front Squat"],
        "Block 2 (Superset): Landmine Squat & Core": ["Heels-Elevated Landmine Squat", "Anchored Reverse Crunch"],
        "Block 3 (Superset): Bulgarians & Hamstrings": ["Bulgarian Split Squats", "Hamstring-Focused Roman Chair Extension"],
        "Block 4 (Tri-Set): Calves, Tibs & Core": ["Squat Wedge Dumbbell Calf Raises", "Wall Tibialis Raises", "Half-Kneeling Pallof Press"]
    },
    "Day 3: Upper B (Vertical Push/Pull)": {
        "Block 1 (Superset): Pull-Ups & Dips": ["Neutral Grip Pull-Ups", "Band-Assisted Dips"],
        "Block 2 (Superset): Landmine Press & Face Pulls": ["Landmine Press", "Banded Face Pulls"],
        "Block 3 (Superset): Curls & Pushdowns": ["Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns"],
        "Block 4: Lateral Raises": ["Chest-Supported Lateral Raise"]
    },
    "Day 4: Lower B (Hinge, Power & Posterior)": {
        "Block 1: RDL": ["Romanian Deadlift (RDL)"],
        "Block 2 (Superset): Swings & Rollouts": ["Heavy Russian Kettlebell Swings", "Ab-Wheel Rollouts"],
        "Block 3 (Superset): Hip Thrusts & Nordics": ["Barbell Hip Thrusts", "Nordic Curls"],
        "Block 4 (Tri-Set): Erectors, Calves & Carries": ["Erector-Focused Roman Chair Extension", "Squat Wedge Dumbbell Calf Raises", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
    },
    "Day 5: The Cardio Engine": {
        "Block 1: Rowing": ["4x4 Rowing (Zone 4/5)"],
        "Block 2: Bike": ["Zone 2 Spin Bike Flush"]
    },
    "🧬 Life Event (Sick/Travel)": {
        "Rest": ["Rest / Recovery / Frozen Week"]
    }
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
    "T-Bar Landmine Row": {"Back": 1.0, "Biceps": 0.5},
    "Dumbbell Bench Press": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5},
    "Single-Arm Bench-Supported Dumbbell Row": {"Back": 1.0, "Biceps": 0.5},
    "Push-Ups": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5},
    "Overhead Tricep Extension": {"Triceps": 1.0},
    "Dumbbell Hammer Curls": {"Biceps": 1.0},
    "Banded Crossovers": {"Chest": 1.0, "Shoulders": 0.5},
    "Chest-Supported Lateral Raise": {"Shoulders": 1.0},
    "Chest-Supported Rear Delt Flye": {"Shoulders": 1.0, "Back": 0.5},
    "Heavy Barbell Front Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Hamstring-Focused Roman Chair Extension": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Anchored Reverse Crunch": {"Abs": 1.0},
    "Wall Tibialis Raises": {"Calves": 1.0},
    "Squat Wedge Dumbbell Calf Raises": {"Calves": 1.0},
    "Half-Kneeling Pallof Press": {"Abs": 1.0},
    "Neutral Grip Pull-Ups": {"Back": 1.0, "Biceps": 0.5},
    "Band-Assisted Dips": {"Chest": 1.0, "Triceps": 1.0, "Shoulders": 0.5},
    "Landmine Press": {"Shoulders": 1.0, "Chest": 0.5, "Triceps": 0.5},
    "Banded Face Pulls": {"Shoulders": 1.0, "Back": 0.5},
    "Incline Supinated Dumbbell Curls": {"Biceps": 1.0},
    "Banded Tricep Pushdowns": {"Triceps": 1.0},
    "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0},
    "Heavy Russian Kettlebell Swings": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Barbell Hip Thrusts": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Ab-Wheel Rollouts": {"Abs": 1.0},
    "Nordic Curls": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Erector-Focused Roman Chair Extension": {"Back": 1.0, "Glutes": 0.5},
    "Heavy Suitcase Holds": {"Abs": 1.0},
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
HEALTH_COLUMNS = ['Height_cm', 'Body_Fat_Pct', 'Muscle_Mass_kg', 'Sleep_Score', 'FFMI']

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
    
    baseline_cols = ['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS + HEALTH_COLUMNS
    
    if not records:
        return pd.DataFrame(columns=baseline_cols)
    
    df = pd.DataFrame(records)
    
    numeric_cols = ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RIR'] + CARDIO_COLUMNS + HEALTH_COLUMNS
    for col in numeric_cols:
        if col not in df.columns: df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
    if 'Side' not in df.columns: df['Side'] = 'Both'
    df['Side'] = df['Side'].replace('', 'Both').fillna('Both')
    df['Date'] = pd.to_datetime(df['Date'])
    
    ASSISTED_EXERCISES = ["Neutral Grip Pull-Ups", "Band-Assisted Dips"]
    RESISTED_EXERCISES = ["Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
    
    def calc_effective_weight(row):
        ex = row['Exercise']
        bw_mod = BW_MULTIPLIERS.get(ex, 0.0)
        base_body_load = row['Bodyweight'] * bw_mod
        
        peak_band_force = BAND_SUBTRACTIONS.get(row.get('Band', 'None'), 0.0)
        avg_band_force = peak_band_force * 0.5
        
        if ex in ASSISTED_EXERCISES:
            eff_wt = row['Weight'] + base_body_load - avg_band_force
        elif ex in RESISTED_EXERCISES:
            eff_wt = row['Weight'] + base_body_load + avg_band_force
        else:
            eff_wt = row['Weight'] + base_body_load
            
        return max(eff_wt, 0.0) 
        
    df['Effective_Weight'] = df.apply(calc_effective_weight, axis=1)
    
    is_lift = ~df['Exercise'].str.contains("Rowing|Bike|Rest", na=False)
    df['Volume'] = 0.0
    df['Epley_1RM'] = 0.0
    
    df.loc[is_lift, 'Volume'] = df.loc[is_lift, 'Effective_Weight'] * df.loc[is_lift, 'Reps_or_Mins']
    df.loc[is_lift, 'Epley_1RM'] = df.loc[is_lift, 'Effective_Weight'] * (1 + df.loc[is_lift, 'Reps_or_Mins'] / 30)
    
    return df

def append_new_data(new_rows_df):
    df_to_append = new_rows_df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore').copy()
    df_to_append['Date'] = pd.to_datetime(df_to_append['Date']).dt.strftime('%Y-%m-%d')
    df_to_append = df_to_append.fillna('')
    worksheet.append_rows(df_to_append.values.tolist())
    st.cache_data.clear()

def overwrite_database(df):
    df_to_save = df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore').copy()
    df_to_save['Date'] = pd.to_datetime(df_to_save['Date']).dt.strftime('%Y-%m-%d')
    df_to_save = df_to_save.fillna('')
    worksheet.clear()
    worksheet.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
    st.cache_data.clear()

# --- INITIALIZE SESSION STATE ---
if 'g_dur' not in st.session_state: st.session_state.update({'g_dur': 60.0, 'g_dist': 10.0, 'g_avg_hr': 130.0, 'g_max_hr': 165.0})
if 'h_weight' not in st.session_state: st.session_state['h_weight'] = 80.0
if 'h_height' not in st.session_state: st.session_state['h_height'] = 180.0
if 'h_bf' not in st.session_state: st.session_state['h_bf'] = 15.0
if 'h_muscle' not in st.session_state: st.session_state['h_muscle'] = 35.0
if 'h_sleep' not in st.session_state: st.session_state['h_sleep'] = 80

df = load_data()

st.title("🔬 Sports Science Dashboard")

# --- UI RE-ARCHITECTURE: Added Tab 4 ---
tab1, tab2, tab3, tab4 = st.tabs(["📝 Data Collection", "📊 Analytics Engine", "⚙️ Database", "📡 Garmin Hub"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        date_input = st.date_input("Date", date.today())
        # Bodyweight syncs automatically if you pull it from Garmin in Tab 4
        bw_input = st.number_input("Daily Bodyweight (kg)", value=st.session_state['h_weight'], step=0.1)
        st.session_state['h_weight'] = bw_input 
        
        is_deload = st.toggle("🧘 Activate Deload Week")
        
    with col2:
        workout_day = st.selectbox("Select Workout Day", list(PROGRAM.keys()))
        workout_block = st.selectbox("Select Workout Block", list(PROGRAM[workout_day].keys()))
        selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day][workout_block], default=PROGRAM[workout_day][workout_block])
    
    st.write("---")
    
    if selected_exercises:
        is_cardio = "Cardio" in workout_day
        
        if is_cardio:
            st.info("🏃‍♂️ **Cardio Day Selected.** Head over to the **📡 Garmin Hub (Tab 4)** to sync your watch or log cardio data manually!")

        else:
            default_sets, _ = get_target_reps_and_sets(selected_exercises[0])
            if is_deload:
                default_sets = max(1, default_sets - 1)
            
            num_sets = st.number_input("🎯 Total Rounds (Sets) to perform:", min_value=1, max_value=10, value=default_sets, step=1)
            st.write("---")
            
            st.markdown("#### 🧠 Today's Mission Control")
            
            default_vals = {}
            
            for exercise in selected_exercises:
                ex_df = df[(df['Exercise'] == exercise) & (df['Reps_or_Mins'] > 0)].sort_values(by=['Date', 'Set_Number'])
                
                if not ex_df.empty:
                    max_all_time_weight = ex_df['Weight'].max()
                    working_sessions = ex_df[ex_df['Weight'] >= (max_all_time_weight * 0.85)]
                    
                    if not working_sessions.empty:
                        dates = working_sessions['Date'].unique()
                    else:
                        dates = ex_df['Date'].unique()
                        
                    last_date = dates[-1]
                    last_session = ex_df[ex_df['Date'] == last_date]
                    
                    set_1 = last_session[last_session['Set_Number'] == 1]
                    
                    if not set_1.empty:
                        s1_data = set_1.iloc[0]
                        last_weight = float(s1_data['Weight'])
                        last_reps = int(s1_data['Reps_or_Mins'])
                        last_band = s1_data['Band']
                        
                        target_sets, top_rep = get_target_reps_and_sets(exercise)
                        band_str = f" [{last_band} Band]" if last_band != "None" else ""
                        
                        if is_deload:
                            calc_w = max(0.0, last_weight * 0.8)
                            calc_w = round(calc_w / 2.5) * 2.5 
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': last_band}
                            
                            st.info(f"🧘 **DELOAD PRESCRIBED:** **{exercise}** ➔ Auto-dropped weight to {calc_w}kg.")
                            continue
                            
                        default_vals[exercise] = {'w': last_weight, 'r': last_reps, 'b': last_band}
                        
                        if last_reps >= top_rep:
                            st.success(f"🚀 **INCREASE WEIGHT:** **{exercise}** hit {last_reps} reps @ {last_weight}kg{band_str}. You own this weight.")
                        else:
                            st.warning(f"🎯 **HOLD WEIGHT:** **{exercise}** hit {last_reps} reps @ {last_weight}kg{band_str}. Chase {top_rep} reps today.")
                        
                        min_reps_last_session = last_session['Reps_or_Mins'].min()
                        if min_reps_last_session < 5:
                            st.error(f"⚠️ **FATIGUE ALERT:** You dropped to {int(min_reps_last_session)} reps on a later set last week. Keep Set 1 heavy, but **drop the weight by 10-15% for Sets 2 & 3** to stay in the hypertrophy zone.")
                            
                        if len(dates) >= 3:
                            last_3_dates = dates[-3:]
                            recent_history = ex_df[(ex_df['Date'].isin(last_3_dates)) & (ex_df['Set_Number'] == 1)]
                            
                            if len(recent_history) == 3:
                                weights_used = recent_history['Weight'].nunique()
                                reps_hit = recent_history['Reps_or_Mins'].nunique()
                                
                                if weights_used == 1 and reps_hit == 1:
                                    st.error(f"🛑 **TRUE PLATEAU DETECTED:** You have been stuck at {last_weight}kg for {last_reps} reps for 3 straight sessions. It is time to swap this exercise or take a Deload.")

                    else:
                        st.info(f"**{exercise}:** No Set 1 data found for last session.")
                        default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None"}
                else:
                    st.info(f"**{exercise}:** No history. Establish your baseline Set 1 today!")
                    default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None"}
            
            st.write("---")
            
            with st.form("lifting_form", clear_on_submit=True):
                weights, reps, reps_l, reps_r, rirs, bands = {}, {}, {}, {}, {}, {}
                
                for i in range(1, num_sets + 1):
                    st.markdown(f"#### 🔁 Round {i}")
                    
                    for exercise in selected_exercises:
                        is_unilateral = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
                        
                        _, top_rep = get_target_reps_and_sets(exercise)
                        st.markdown(f"**{exercise}** *(Target: {top_rep} reps)*")
                        
                        def_w = float(default_vals.get(exercise, {}).get('w', 0.0))
                        def_b = default_vals.get(exercise, {}).get('b', "None")
                        band_list = list(BAND_SUBTRACTIONS.keys())
                        band_index = band_list.index(def_b) if def_b in band_list else 0
                        
                        key = f"{exercise}_{i}" 
                        
                        if uses_band:
                            c1, c2, c3, c4 = st.columns([1, 1, 1.5, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, value=def_w, key=f"w_{key}")
                            if is_unilateral:
                                sc1, sc2 = c2.columns(2)
                                reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                                reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                            else:
                                reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            bands[key] = c3.selectbox("Band", band_list, index=band_index, key=f"b_{key}")
                            rirs[key] = c4.slider("RIR (Reps in Reserve)", 0, 5, 2, 1, key=f"rir_{key}")
                        else:
                            c1, c2, c3 = st.columns([1, 1, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, value=def_w, key=f"w_{key}")
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
                    # FFMI calculation at submission
                    lean_mass = st.session_state['h_weight'] * (1 - (st.session_state['h_bf'] / 100))
                    height_m = st.session_state['h_height'] / 100
                    ffmi = lean_mass / (height_m ** 2) if height_m > 0 else 0

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
                                    'Distance_km': 0.0, 'Bodyweight': st.session_state['h_weight'], 'RIR': rirs[key],
                                    'Avg_HR': 0.0, 'Max_HR': 0.0, 'Avg_Resp': 0.0,
                                    'Z1_Mins': 0.0, 'Z2_Mins': 0.0, 'Z3_Mins': 0.0, 'Z4_Mins': 0.0, 'Z5_Mins': 0.0,
                                    'Height_cm': st.session_state['h_height'], 'Body_Fat_Pct': st.session_state['h_bf'], 
                                    'Muscle_Mass_kg': st.session_state['h_muscle'], 'Sleep_Score': st.session_state['h_sleep'], 'FFMI': ffmi
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

with tab4:
    st.subheader("📡 Garmin Integration Hub")
    st.write("Keep your workout logging screen clean by managing all Garmin API syncing and manual cardio entry here.")
    
    st.markdown("### 🔐 Garmin Authentication")
    st.info("If you have Multi-Factor Authentication (2FA) enabled, open your Authenticator App and type the 6 digits below *right before* you click a sync button.")
    mfa_input = st.text_input("MFA Code (Leave blank if 2FA is disabled)", max_chars=6)
    
    def get_garmin_client():
        g_email = st.secrets.get("garmin_email")
        g_pass = st.secrets.get("garmin_password")
        if not g_email or not g_pass:
            st.error("Missing Garmin credentials in Streamlit secrets! Check your deployment settings.")
            return None
        try:
            if mfa_input:
                client = Garmin(g_email, g_pass, prompt_mfa=lambda: mfa_input)
            else:
                client = Garmin(g_email, g_pass)
            client.login()
            return client
        except Exception as e:
            if "prompt_mfa" in str(e):
                st.error("🛑 **Garmin requires 2FA!** Please enter your 6-digit Authenticator app code above and try syncing again.")
            else:
                st.error(f"Garmin Login Failed: {e}")
            return None

    c1, c2 = st.columns(2)
    
    with c1:
        st.markdown("#### 🧬 Morning Health Sync")
        if st.button("🔄 Sync Scale & Sleep"):
            with st.spinner("Connecting to Garmin API..."):
                client = get_garmin_client()
                if client:
                    today_iso = date.today().isoformat()
                    try:
                        weigh_ins = client.get_body_composition(today_iso)
                        if weigh_ins and 'dateWeightList' in weigh_ins and weigh_ins['dateWeightList']:
                            latest = weigh_ins['dateWeightList'][-1]
                            raw_w = latest.get('weight', st.session_state['h_weight'])
                            st.session_state['h_weight'] = float(raw_w / 1000 if raw_w > 1000 else raw_w)
                            st.session_state['h_bf'] = float(latest.get('bodyFat', st.session_state['h_bf']))
                            raw_m = latest.get('muscleMass', st.session_state['h_muscle'])
                            st.session_state['h_muscle'] = float(raw_m / 1000 if raw_m > 1000 else raw_m)
                    except Exception as e:
                        st.warning("Scale sync skipped or empty.")
                        
                    try:
                        sleep_data = client.get_sleep_data(today_iso)
                        if sleep_data:
                            st.session_state['h_sleep'] = int(sleep_data.get('dailySleepDTO', {}).get('sleepScores', {}).get('overall', {}).get('value', st.session_state['h_sleep']))
                    except Exception as e:
                        st.warning("Sleep sync skipped or empty.")
                        
                    st.success("Health Check Complete! Data stored for today's logs.")
                    st.rerun()

        st.markdown("**Current Session Health Data:**")
        st.session_state['h_height'] = st.number_input("Height (cm) - Fixed", value=st.session_state['h_height'], step=1.0)
        st.session_state['h_bf'] = st.number_input("Body Fat (%)", value=st.session_state['h_bf'], step=0.1)
        st.session_state['h_muscle'] = st.number_input("Skeletal Muscle (kg)", value=st.session_state['h_muscle'], step=0.1)
        st.session_state['h_sleep'] = st.number_input("Sleep Score (0-100)", value=st.session_state['h_sleep'], step=1)
        
    with c2:
        st.markdown("#### 🏃‍♂️ Cardio Session Data")
        if st.button("🔄 Sync Latest Cardio"):
            with st.spinner("Connecting to Garmin API..."):
                client = get_garmin_client()
                if client:
                    try:
                        activities = client.get_activities(0, 1) 
                        if activities:
                            act = activities[0]
                            st.session_state['g_dur'] = round(act.get('duration', 0) / 60, 1)
                            st.session_state['g_dist'] = round(act.get('distance', 0) / 1000, 2)
                            st.session_state['g_avg_hr'] = float(act.get('averageHR', 130.0))
                            st.session_state['g_max_hr'] = float(act.get('maxHR', 165.0))
                            st.success(f"Synced! Grabbed activity: {act.get('activityName', 'Unknown')}")
                            st.rerun()
                        else:
                            st.warning("No activities found on your Garmin account.")
                    except Exception as e:
                        st.error(f"Activity Sync Failed: {e}")

        st.markdown("**Cardio Log Entry:**")
        with st.form("cardio_form", clear_on_submit=False):
            ex_options = ["4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"]
            c_ex = st.selectbox("Select Cardio Type", ex_options)
            duration = st.number_input("Duration (Minutes)", min_value=1.0, value=st.session_state['g_dur'], step=1.0)
            distance = st.number_input("Distance (km)", min_value=0.0, value=st.session_state['g_dist'], step=0.1)
            avg_resp = st.number_input("Avg Respiration (brpm)", min_value=0.0, value=20.0, step=1.0)
            avg_hr = st.number_input("Avg Heart Rate (bpm)", min_value=40.0, value=st.session_state['g_avg_hr'], step=1.0)
            max_hr = st.number_input("Max Heart Rate (bpm)", min_value=40.0, value=st.session_state['g_max_hr'], step=1.0)
            
            st.markdown("#### ⏱️ Time in HR Zones (Minutes)")
            zc1, zc2, zc3, zc4, zc5 = st.columns(5)
            z1 = zc1.number_input("Zone 1", min_value=0.0, step=1.0)
            z2 = zc2.number_input("Zone 2", min_value=0.0, step=1.0)
            z3 = zc3.number_input("Zone 3", min_value=0.0, step=1.0)
            z4 = zc4.number_input("Zone 4", min_value=0.0, step=1.0)
            z5 = zc5.number_input("Zone 5", min_value=0.0, step=1.0)
            
            submit_cardio = st.form_submit_button("Save Cardio to Database", type="primary")
            
            if submit_cardio:
                lean_mass = st.session_state['h_weight'] * (1 - (st.session_state['h_bf'] / 100))
                height_m = st.session_state['h_height'] / 100
                ffmi = lean_mass / (height_m ** 2) if height_m > 0 else 0
                
                cardio_data = {
                    'Date': date.today(), 'Workout_Day': "Day 5: The Cardio Engine", 'Exercise': c_ex, 
                    'Set_Number': 1, 'Weight': 0.0, 'Band': 'None', 'Distance_km': distance, 
                    'Reps_or_Mins': duration, 'Bodyweight': st.session_state['h_weight'], 'RIR': 0.0, 'Side': 'Both',
                    'Avg_HR': avg_hr, 'Max_HR': max_hr, 'Avg_Resp': avg_resp,
                    'Z1_Mins': z1, 'Z2_Mins': z2, 'Z3_Mins': z3, 'Z4_Mins': z4, 'Z5_Mins': z5,
                    'Height_cm': st.session_state['h_height'], 'Body_Fat_Pct': st.session_state['h_bf'], 
                    'Muscle_Mass_kg': st.session_state['h_muscle'], 'Sleep_Score': st.session_state['h_sleep'], 'FFMI': ffmi
                }
                new_df = pd.DataFrame([cardio_data])
                append_new_data(new_df)
                st.success("High-Fidelity Cardio Data Saved!")

with tab2:
    if df.empty:
        st.info("Awaiting Data...")
    else:
        lift_df = df[(df['Reps_or_Mins'] > 0) & (~df['Exercise'].str.contains("Rowing|Bike|Rest", na=False))].copy()
        cardio_df = df[df['Exercise'].str.contains("Rowing|Bike", na=False)].copy()
        
        at1, at2, at3, at4, at5, at6 = st.tabs(["👻 Milestones", "📈 Relative Strength", "🔥 INOL", "🦵 Radar", "🫀 Cardio", "🧬 Recomp & Recovery"])
        
        with at1:
            st.subheader("Historical Milestones & Gamification")
            if not lift_df.empty:
                recent_30_lift = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=30)]
                monthly_tonnage = recent_30_lift['Volume'].sum()
                
                if monthly_tonnage > 0:
                    st.markdown("### 🎮 The Monthly Tonnage Game")
                    if monthly_tonnage < 2500:
                        emoji, item = "🦈", "A Great White Shark"
                    elif monthly_tonnage < 5000:
                        emoji, item = "🐘", "An African Elephant"
                    elif monthly_tonnage < 10000:
                        emoji, item = "🛻", "A Monster Truck"
                    elif monthly_tonnage < 40000:
                        emoji, item = "🚌", "A School Bus"
                    elif monthly_tonnage < 100000:
                        emoji, item = "✈️", "A Boeing 737"
                    else:
                        emoji, item = "🚀", "A Space Shuttle"
                        
                    st.info(f"**Total Volume (Last 30 Days):** {monthly_tonnage:,.1f} kg")
                    st.success(f"**{emoji} Achievement Unlocked:** You have officially lifted the equivalent weight of **{item}** this month.")
                
            st.write("---")
            
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
                
                if not pr_df.empty:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("1RM (Epley)", f"{pr_df['Epley_1RM'].max():.1f} kg")
                    c2.metric("3RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 3]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 3].empty else "N/A")
                    c3.metric("5RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 5]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 5].empty else "N/A")
                    c4.metric("10RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 10]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 10].empty else "N/A")
                else:
                    st.warning("Not enough data for this exercise yet.")

        with at2:
            st.subheader("Progression Velocity & Relative Strength")
            st.write("Tracking absolute max weight is good, but tracking your **Strength-to-Weight Ratio** proves you are building pure lean tissue, not just gaining fat/water weight.")
            
            if not lift_df.empty:
                vel_ex = st.selectbox("Select Exercise", lift_df['Exercise'].unique(), key='vel_ex')
                v_df = lift_df[lift_df['Exercise'] == vel_ex].groupby('Date').agg(
                    {'Epley_1RM': 'max', 'Bodyweight': 'mean'}
                ).reset_index()
                
                if not v_df.empty:
                    v_df['3_Session_Avg'] = v_df['Epley_1RM'].rolling(window=3, min_periods=1).mean()
                    v_df['Relative_Strength'] = v_df['Epley_1RM'] / v_df['Bodyweight'].replace(0, 1) 
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['Epley_1RM'], mode='lines+markers', name='Daily e1RM (kg)', opacity=0.5, line=dict(dash='dot', width=1)))
                    fig.add_trace(go.Scatter(x=v_df['Date'], y=v_df['3_Session_Avg'], mode='lines', name='Trend (Rolling Avg)', line=dict(color='#FF4B4B', width=3)))
                    fig.update_layout(title=f"Absolute Strength (e1RM) - {vel_ex}")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig_rel = go.Figure()
                    fig_rel.add_trace(go.Scatter(x=v_df['Date'], y=v_df['Relative_Strength'], mode='lines+markers', name='Strength-to-Weight Ratio', line=dict(color='#00CC96', width=3)))
                    fig_rel.update_layout(title=f"Relative Strength Multiplier (e1RM ÷ Bodyweight)", yaxis_title="x Bodyweight")
                    st.plotly_chart(fig_rel, use_container_width=True)
                else:
                    st.info("Log some sessions for this exercise to see the velocity trend.")

        with at3:
            st.subheader("INOL & Fatigue Curves")
            if not lift_df.empty:
                inol_ex = st.selectbox("Analyze Exercise", lift_df['Exercise'].unique(), key='inol_ex')
                i_df = lift_df[lift_df['Exercise'] == inol_ex].copy()
                
                SYSTEMIC_MODIFIERS = {
                    "Romanian Deadlift (RDL)": 1.0, "Heavy Barbell Front Squat": 1.0,
                    "Neutral Grip Pull-Ups": 0.8, "Bulgarian Split Squats": 0.8, "Heavy Russian Kettlebell Swings": 0.8, "Barbell Hip Thrusts": 0.8, "Heels-Elevated Landmine Squat": 0.8,
                    "T-Bar Landmine Row": 0.7, "Dumbbell Bench Press": 0.7, "Band-Assisted Dips": 0.7, "Landmine Press": 0.7,
                    "Single-Arm Bench-Supported Dumbbell Row": 0.6, "Nordic Curls": 0.6, "Front-Rack Kettlebell Marches": 0.6,
                    "Push-Ups": 0.5, "Hamstring-Focused Roman Chair Extension": 0.5, "Erector-Focused Roman Chair Extension": 0.5, "Ab-Wheel Rollouts": 0.5, "Heavy Suitcase Holds": 0.5,
                    "Chest-Supported Lateral Raise": 0.3, "Chest-Supported Rear Delt Flye": 0.3, "Overhead Tricep Extension": 0.3, "Dumbbell Hammer Curls": 0.3, "Banded Crossovers": 0.3, "Incline Supinated Dumbbell Curls": 0.3, "Banded Tricep Pushdowns": 0.3, "Banded Face Pulls": 0.3, "Wall Tibialis Raises": 0.3, "Squat Wedge Dumbbell Calf Raises": 0.3, "Half-Kneeling Pallof Press": 0.3, "Anchored Reverse Crunch": 0.3
                }
                
                if not i_df.empty:
                    global_max = i_df['Epley_1RM'].max()
                    i_df['Intensity_%'] = (i_df['Effective_Weight'] / global_max) * 100
                    i_df['Intensity_%'] = i_df['Intensity_%'].clip(upper=99)
                    
                    fatigue_factor = SYSTEMIC_MODIFIERS.get(inol_ex, 0.5)
                    i_df['INOL'] = (i_df['Reps_or_Mins'] / (100 - i_df['Intensity_%'])) * fatigue_factor
                    
                    daily_inol = i_df.groupby('Date')['INOL'].sum().reset_index()
                    fig2 = px.bar(daily_inol, x='Date', y='INOL', title="Daily Session INOL Score (Adjusted for Systemic Load)", color='INOL', color_continuous_scale='RdYlGn_r', range_color=[0, 2.0])
                    fig2.add_hline(y=2.0, line_dash="dot", annotation_text="Overreaching (>2.0)")
                    st.plotly_chart(fig2, use_container_width=True)
                    
                    st.markdown("### Fatigue Degradation (Intra-Workout)")
                    fatigue_df = i_df.groupby(['Date', 'Set_Number'])['Reps_or_Mins'].max().reset_index()
                    fig3 = px.line(fatigue_df, x='Set_Number', y='Reps_or_Mins', color='Date', markers=True, title="Rep Drop-off Across Sets")
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("No data available for INOL calculation yet.")

        with at4:
            st.subheader("7-Day Microcycle (Muscle Volume)")
            st.write("This tracks **Total Hard Sets** per muscle over a rolling 7-day window. It reveals true biological imbalances before they become joint injuries.")
            
            if not lift_df.empty:
                recent_7_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=7)]
                muscle_sets = {}
                for index, row in recent_7_df.iterrows():
                    ex = row['Exercise']
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items():
                            muscle_sets[muscle] = muscle_sets.get(muscle, 0) + (1 * multiplier)
                
                if muscle_sets:
                    heat_df = pd.DataFrame(list(muscle_sets.items()), columns=['Muscle', 'Total Sets']).sort_values(by='Total Sets')
                    
                    fig_radar = go.Figure(data=go.Scatterpolar(
                        r=heat_df['Total Sets'].tolist() + [heat_df['Total Sets'].iloc[0]], 
                        theta=heat_df['Muscle'].tolist() + [heat_df['Muscle'].iloc[0]],
                        fill='toself',
                        marker_color='#1f77b4'
                    ))
                    fig_radar.update_layout(
                        title="Structural Balance Radar",
                        polar=dict(radialaxis=dict(visible=True, range=[0, max(20, heat_df['Total Sets'].max())])),
                        showlegend=False
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
                    fig4 = px.bar(heat_df, x='Total Sets', y='Muscle', orientation='h', 
                                  color='Total Sets', color_continuous_scale='Inferno',
                                  title="Set Distribution (Last 7 Days)")
                    
                    fig4.add_vline(x=10, line_dash="dash", line_color="#00CC96", annotation_text="MEV (~10/wk)", annotation_position="top left")
                    fig4.add_vline(x=20, line_dash="dash", line_color="#EF553B", annotation_text="MRV (~20/wk)", annotation_position="top left")
                    st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("Log some data this week to populate the radar chart!")

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
                    
        with at6:
            st.subheader("🧬 Biological Recomp & Recovery")
            
            st.markdown("### FFMI (Fat-Free Mass Index) Tracker")
            st.write("*FFMI measures how much pure lean muscle tissue you carry. A natural limit is around 25.*")
            
            health_df = df.groupby('Date').agg({'FFMI': 'max', 'Body_Fat_Pct': 'max', 'Sleep_Score': 'max'}).reset_index()
            health_df = health_df[(health_df['FFMI'] > 0) & (health_df['Body_Fat_Pct'] > 0)]
            
            if not health_df.empty:
                fig_ffmi = go.Figure()
                fig_ffmi.add_trace(go.Scatter(x=health_df['Date'], y=health_df['FFMI'], mode='lines+markers', name='FFMI', line=dict(color='#00CC96', width=3), yaxis='y1'))
                fig_ffmi.add_trace(go.Scatter(x=health_df['Date'], y=health_df['Body_Fat_Pct'], mode='lines', name='Body Fat %', line=dict(color='#FF4B4B', dash='dot'), yaxis='y2'))
                
                fig_ffmi.update_layout(
                    yaxis=dict(title='FFMI Score', side='left'),
                    yaxis2=dict(title='Body Fat %', side='right', overlaying='y', showgrid=False),
                    hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_ffmi, use_container_width=True)
            else:
                st.info("Sync your Garmin Scale data a few times to start building your FFMI Recomp chart.")
                
            st.markdown("### 🛌 Sleep Score vs. Absolute Strength")
            st.write("*Visual proof of how your Garmin sleep score dictates your performance under the bar.*")
            
            if not lift_df.empty:
                rc_ex = st.selectbox("Select Exercise to compare against Sleep", lift_df['Exercise'].unique())
                rc_df = lift_df[lift_df['Exercise'] == rc_ex].groupby('Date').agg({'Epley_1RM': 'max', 'Sleep_Score': 'max'}).reset_index()
                rc_df = rc_df[rc_df['Sleep_Score'] > 0]
                
                if not rc_df.empty:
                    fig_sleep = px.scatter(rc_df, x='Sleep_Score', y='Epley_1RM', trendline="ols", 
                                           title=f"Correlation: Sleep Score vs. {rc_ex} e1RM",
                                           labels={'Sleep_Score': 'Garmin Sleep Score', 'Epley_1RM': 'e1RM (kg)'},
                                           color='Sleep_Score', color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_sleep, use_container_width=True)
                else:
                    st.info(f"Not enough Sleep Score data logged alongside {rc_ex} to generate a scatter plot yet.")

with tab3:
    st.subheader("⚙️ Database Editor")
    st.write("Loading thousands of rows can cause lag. Select how much recent history you need to edit.")
    
    days_to_edit = st.slider("Days of history to load", min_value=7, max_value=365, value=30, step=7)
    cutoff_date = pd.to_datetime(date.today()) - pd.Timedelta(days=days_to_edit)
    
    historical_df = df[df['Date'] < cutoff_date].copy()
    recent_df = df[df['Date'] >= cutoff_date].copy()
    
    edited_recent = st.data_editor(
        recent_df.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore'), 
        num_rows="dynamic", 
        use_container_width=True
    )
    
    if st.button("Save Changes", type="primary"):
        final_df = pd.concat([historical_df, edited_recent], ignore_index=True)
        overwrite_database(final_df)
        st.success("Database Saved safely!")
        st.rerun()
