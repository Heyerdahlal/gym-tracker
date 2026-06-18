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
from gym_config import PROGRAM, REST_PROTOCOLS, WARM_UPS, COOL_DOWNS, MOBILITY_GUIDES, DAY_PHILOSOPHY, REP_TARGETS, EXERCISE_GUIDES, DAILY_SYSTEM_RESET, VOLUME_THRESHOLDS, EXERCISE_CAPS, MUSCLE_MAP, BW_MULTIPLIERS, BAND_SUBTRACTIONS, ADJUSTABLE_DBS, KETTLEBELLS, PUSH_UP_VARIATIONS, UNILATERAL_EXERCISES, HEAVY_COMPOUNDS, ASSISTED_EXERCISES, RESISTED_EXERCISES, BODYWEIGHT_ONLY, PURE_BAND_EXERCISES 

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
    ws_lifts = sh.worksheet("Lifts")
    ws_health = sh.worksheet("Health")
    try: ws_cardio = sh.worksheet("Cardio")
    except gspread.exceptions.WorksheetNotFound: ws_cardio = sh.add_worksheet(title="Cardio", rows="100", cols="15")
    try: ws_system = sh.worksheet("System")
    except gspread.exceptions.WorksheetNotFound: ws_system = sh.add_worksheet(title="System", rows="10", cols="5")
except Exception as e:
    st.error(f"⚠️ **Google Connection Error:** Make sure you created the 'Lifts' and 'Health' tabs! Error: {e}")
    st.stop()

# --- STATIC USER PROFILE ---
USER_HEIGHT = float(st.secrets.get("user_height_cm", 180.0))

# --- COLUMNS ---
LIFTS_COLS = ['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Variation', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RIR']
HEALTH_COLS = ['Date', 'Weight_kg', 'Body_Fat_Pct', 'Muscle_Mass_kg', 'Sleep_Score', 'RHR', 'HRV', 'FFMI', 'Height_cm']
CARDIO_COLS = ['Date', 'Exercise', 'Duration_Mins', 'Distance_km', 'Avg_HR', 'Max_HR', 'Avg_Resp', 'Z1_Mins', 'Z2_Mins', 'Z3_Mins', 'Z4_Mins', 'Z5_Mins']


def snap_to_weight(target_weight, exercise_name):
    if "Dumbbell" in exercise_name or "DB" in exercise_name:
        return min(ADJUSTABLE_DBS, key=lambda x: abs(x - target_weight))
    elif "Kettlebell" in exercise_name or "KB" in exercise_name:
        return min(KETTLEBELLS, key=lambda x: abs(x - target_weight))
    else:
        return round(target_weight / 2.5) * 2.5

def get_next_weight(current_weight, exercise_name):
    if "Dumbbell" in exercise_name or "DB" in exercise_name:
        closest = min(ADJUSTABLE_DBS, key=lambda x: abs(x - current_weight))
        idx = ADJUSTABLE_DBS.index(closest)
        return ADJUSTABLE_DBS[min(idx + 1, len(ADJUSTABLE_DBS) - 1)]
    elif "Kettlebell" in exercise_name or "KB" in exercise_name:
        closest = min(KETTLEBELLS, key=lambda x: abs(x - current_weight))
        idx = KETTLEBELLS.index(closest)
        return KETTLEBELLS[min(idx + 1, len(KETTLEBELLS) - 1)]
    else:
        return current_weight + 2.5

def get_target_reps_and_sets(exercise_name):
    target_str = REP_TARGETS.get(exercise_name, "")
    sets_match = re.search(r'(\d+)\s*Sets', target_str, re.IGNORECASE)
    reps_match = re.search(r'–(\d+)\s*Reps', target_str, re.IGNORECASE)
    target_sets = int(sets_match.group(1)) if sets_match else 3
    top_rep = int(reps_match.group(1)) if reps_match else 8
    return target_sets, top_rep

@st.cache_data(ttl=600)
def get_last_deload():
    try: return ws_system.acell('B1').value
    except Exception: return None

@st.cache_data(ttl=600)
def load_data():
    try: l_recs = ws_lifts.get_all_records()
    except Exception: l_recs = []
    df_lifts = pd.DataFrame(l_recs) if l_recs else pd.DataFrame(columns=LIFTS_COLS)
    for col in LIFTS_COLS:
        if col not in df_lifts.columns: df_lifts[col] = 0.0 if col not in ['Date', 'Workout_Day', 'Exercise', 'Band', 'Variation', 'Side'] else ("None" if col == 'Variation' else "")
    
    try: h_recs = ws_health.get_all_records()
    except Exception: h_recs = []
    df_health = pd.DataFrame(h_recs) if h_recs else pd.DataFrame(columns=HEALTH_COLS)
    for col in HEALTH_COLS:
        if col not in df_health.columns: df_health[col] = 0.0 if col != 'Date' else ""
            
    try: c_recs = ws_cardio.get_all_records()
    except Exception: c_recs = []
    df_cardio = pd.DataFrame(c_recs) if c_recs else pd.DataFrame(columns=CARDIO_COLS)
    for col in CARDIO_COLS:
        if col not in df_cardio.columns: df_cardio[col] = 0.0 if col not in ['Date', 'Exercise'] else ""

    num_cols_lifts = ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RIR']
    for col in num_cols_lifts: df_lifts[col] = pd.to_numeric(df_lifts[col], errors='coerce').fillna(0)
    df_lifts['Side'] = df_lifts['Side'].replace('', 'Both').fillna('Both')
    df_lifts['Date'] = pd.to_datetime(df_lifts['Date'], errors='coerce')
    
    if not df_lifts.empty:
        bw_mod = df_lifts['Exercise'].map(BW_MULTIPLIERS).fillna(0.0)
        base_body_load = df_lifts['Bodyweight'] * bw_mod
        
        peak_band_force = df_lifts['Band'].map(BAND_SUBTRACTIONS).fillna(0.0)
        avg_band_force = peak_band_force * 0.5
        
        is_assisted = df_lifts['Exercise'].isin(ASSISTED_EXERCISES)
        is_resisted = df_lifts['Exercise'].isin(RESISTED_EXERCISES)
        
        eff_wt = df_lifts['Weight'] + base_body_load
        
        # Override for Push-up variations
        is_pushup = df_lifts['Exercise'] == "Push-Ups"
        if is_pushup.any():
            var_mult = df_lifts.loc[is_pushup, 'Variation'].map({"Elevated": 0.45, "Flat": 0.65, "Deficit": 0.70}).fillna(0.65)
            eff_wt.loc[is_pushup] = df_lifts.loc[is_pushup, 'Weight'] + (df_lifts.loc[is_pushup, 'Bodyweight'] * var_mult)

        eff_wt = np.where(is_assisted, eff_wt - avg_band_force, eff_wt)
        eff_wt = np.where(is_resisted, eff_wt + avg_band_force, eff_wt)
        
        df_lifts['Effective_Weight'] = np.maximum(eff_wt, 5.0)
    else:
        df_lifts['Effective_Weight'] = 0.0

    is_lift = ~df_lifts['Exercise'].str.contains("Rowing|Bike|Rest", na=False)
    df_lifts['Volume'] = 0.0
    df_lifts['Epley_1RM'] = 0.0
    
    if not df_lifts.empty:
        df_lifts.loc[is_lift, 'Volume'] = df_lifts.loc[is_lift, 'Effective_Weight'] * df_lifts.loc[is_lift, 'Reps_or_Mins']
        capped_reps = df_lifts.loc[is_lift, 'Reps_or_Mins'].clip(upper=12)
        df_lifts.loc[is_lift, 'Epley_1RM'] = df_lifts.loc[is_lift, 'Effective_Weight'] * (1 + capped_reps / 30)
    
    df_health['Date'] = pd.to_datetime(df_health['Date'], errors='coerce')
    num_cols_health = [c for c in HEALTH_COLS if c != 'Date']
    for col in num_cols_health: df_health[col] = pd.to_numeric(df_health[col], errors='coerce').fillna(0)
        
    df_cardio['Date'] = pd.to_datetime(df_cardio['Date'], errors='coerce')
    num_cols_cardio = [c for c in CARDIO_COLS if c not in ['Date', 'Exercise']]
    for col in num_cols_cardio: df_cardio[col] = pd.to_numeric(df_cardio[col], errors='coerce').fillna(0)
        
    return df_lifts, df_health, df_cardio

def save_to_sheet(ws, df_new, required_cols):
    df_to_save = df_new.copy()
    for col in required_cols:
        if col not in df_to_save.columns: df_to_save[col] = ""
    df_to_save = df_to_save[required_cols]
    df_to_save['Date'] = pd.to_datetime(df_to_save['Date']).dt.strftime('%Y-%m-%d')
    df_to_save = df_to_save.fillna('')
    try: first_row = ws.row_values(1)
    except Exception: first_row = []
    if not first_row or first_row[0] != 'Date':
        ws.clear()
        ws.update(values=[df_to_save.columns.tolist()], range_name="A1")
    ws.append_rows(df_to_save.values.tolist())
    st.cache_data.clear()

def overwrite_sheet(ws, df_new, required_cols):
    df_to_save = df_new.copy()
    for col in required_cols:
        if col not in df_to_save.columns: df_to_save[col] = ""
    df_to_save = df_to_save[required_cols]
    df_to_save['Date'] = pd.to_datetime(df_to_save['Date']).dt.strftime('%Y-%m-%d')
    df_to_save = df_to_save.fillna('')
    
    # SAFEGUARD: Grab the current data as a backup before clearing
    try:
        backup_data = ws.get_all_values()
    except Exception as e:
        st.error(f"Failed to create backup. Aborting save! Error: {e}")
        return False

    try:
        # Clear and write new data
        ws.clear()
        ws.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
        st.cache_data.clear()
        return True
    except Exception as e:
        # PUSH THE BACKUP IF IT FAILS
        st.error("Connection failed mid-save! Restoring backup...")
        if backup_data:
            ws.update(values=backup_data, range_name="A1")
        return False

def get_garmin_client(mfa_val=""):
    if 'garmin_vip_client' in st.session_state: return st.session_state['garmin_vip_client']
    g_email, g_pass = st.secrets.get("garmin_email"), st.secrets.get("garmin_password")
    if not g_email or not g_pass: return None
    client = Garmin(g_email, g_pass, prompt_mfa=lambda: mfa_val) if mfa_val else Garmin(g_email, g_pass)
    try:
        saved_token = ws_system.acell('A1').value
        if saved_token:
            import garth
            garth.client.loads(json.loads(saved_token))
            client.garth = garth.client
            st.session_state['garmin_vip_client'] = client
            return client
    except Exception: pass 
    try:
        client.login()
        try:
            import garth
            ws_system.update_acell('A1', json.dumps(garth.client.dump()))
        except Exception: pass 
        st.session_state['garmin_vip_client'] = client 
        return client
    except Exception as e:
        if "429" in str(e): st.error("🛑 **Garmin Timeout (429):** Please wait 15 minutes.")
        elif "prompt_mfa" in str(e): st.error("🛑 **Garmin requires 2FA!** Type the code and click sync.")
        else: st.error(f"Garmin Login Failed: {e}")
        return None

df_lifts, df_health, df_cardio = load_data()

def get_latest_nonzero(df, col_name, default_val):
    if not df.empty and col_name in df.columns:
        valid_data = df[df[col_name] > 0]
        if not valid_data.empty: return float(valid_data.sort_values('Date').iloc[-1][col_name])
    return default_val

last_w = get_latest_nonzero(df_health, 'Weight_kg', 80.0) 
if last_w == 80.0 and not df_lifts.empty and 'Bodyweight' in df_lifts.columns:
    valid_bw = df_lifts[df_lifts['Bodyweight'] > 0]
    if not valid_bw.empty: last_w = float(valid_bw.sort_values('Date').iloc[-1]['Bodyweight'])

if 'g_dur' not in st.session_state: st.session_state.update({'g_dur': 60.0, 'g_dist': 10.0, 'g_avg_hr': 130.0, 'g_max_hr': 165.0})
if 'h_weight' not in st.session_state: st.session_state['h_weight'] = last_w
if 'h_bf' not in st.session_state: st.session_state['h_bf'] = get_latest_nonzero(df_health, 'Body_Fat_Pct', 15.0)
if 'h_muscle' not in st.session_state: st.session_state['h_muscle'] = get_latest_nonzero(df_health, 'Muscle_Mass_kg', 35.0)
if 'h_sleep' not in st.session_state: st.session_state['h_sleep'] = int(get_latest_nonzero(df_health, 'Sleep_Score', 80))
if 'h_rhr' not in st.session_state: st.session_state['h_rhr'] = int(get_latest_nonzero(df_health, 'RHR', 50))
if 'h_hrv' not in st.session_state: st.session_state['h_hrv'] = int(get_latest_nonzero(df_health, 'HRV', 60))

df_lifts_recent = df_lifts[df_lifts['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=90)] if not df_lifts.empty else df_lifts

st.title("🔬 Sports Science Dashboard")

tab_sessions, tab_health, tab_analytics, tab_overview, tab_db = st.tabs(["🏋️‍♂️ Sessions", "🧬 Bio Data", "📊 Analytics", "📋 Program Overview", "⚙️ Database"])

with tab_sessions:
    sub_lift, sub_cardio, sub_mob = st.tabs(["💪 Strength Training", "🫀 Cardio Engine", "🧘 System Reset"])
    
    with sub_lift:
        acwr_alert = False
        hrv_alert = False
        meso_alert = False
        
        last_deload_str = get_last_deload()
        last_deload_date = pd.to_datetime(last_deload_str) if last_deload_str else pd.to_datetime('2000-01-01')
        
        if not df_lifts.empty:
            post_deload_lifts = df_lifts[df_lifts['Date'] >= last_deload_date]
            active_weeks = len(post_deload_lifts['Date'].dt.isocalendar().week.unique())
            if active_weeks >= 5: meso_alert = True
                
            daily_vol = df_lifts.groupby('Date')['Volume'].sum().reset_index().set_index('Date').resample('D').sum().fillna(0)
            if len(daily_vol) >= 7:
                acute = daily_vol['Volume'].iloc[-7:].sum()
                chronic = daily_vol['Volume'].iloc[-28:].sum() / 4 if len(daily_vol) >= 28 else (daily_vol['Volume'].sum() / (len(daily_vol)/7) if len(daily_vol)>0 else 0)
                acwr = acute / chronic if chronic > 0 else 1.0
                if acwr > 1.5: acwr_alert = True
        
        hrv_7d, hrv_30d = 0, 0
        if not df_health.empty and 'HRV' in df_health.columns:
            valid_hrv = df_health[df_health['HRV'] > 0].set_index('Date').resample('D').mean().ffill()
            if len(valid_hrv) >= 7:
                hrv_7d = valid_hrv['HRV'].iloc[-7:].mean()
                hrv_30d = valid_hrv['HRV'].iloc[-30:].mean() if len(valid_hrv) >= 30 else valid_hrv['HRV'].mean()
                if hrv_7d < (hrv_30d * 0.90): hrv_alert = True

        if acwr_alert or hrv_alert:
            st.error(f"🚨 **CRITICAL SYSTEM ALERT:** " + 
                     ("Your ACWR is dangerously high (>1.5). " if acwr_alert else "") +
                     ("Your 7-Day HRV has crashed significantly below baseline. " if hrv_alert else "") +
                     "Your CNS is fried. Mandatory Deload advised today.")
        elif meso_alert:
            st.warning("📅 **Mesocycle Peak Reached:** You have accumulated 5+ weeks of volume since your last rest period. A systemic deload is highly recommended.")

        col1, col2 = st.columns([1, 2])
        with col1:
            date_input = st.date_input("Date", date.today())
            is_deload = st.toggle("🧘 Activate Deload Week")
        with col2:
            today_name = date_input.strftime('%A')
            program_keys = list(PROGRAM.keys())
            default_idx = 0
            for i, key in enumerate(program_keys):
                if today_name in key:
                    default_idx = i
                    break
                    
            workout_day = st.selectbox("Select Workout Day", program_keys, index=default_idx)
            workout_block = st.selectbox("Select Workout Block", list(PROGRAM[workout_day].keys()))
            
            if "Freestyle" in workout_day: selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day][workout_block], default=[])
            else: selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day][workout_block], default=PROGRAM[workout_day][workout_block])
                
            if workout_day in WARM_UPS: st.info(f"🔥 **Prep & Activation:** {WARM_UPS[workout_day]}")
            if workout_day in COOL_DOWNS: st.info(f"🧊 **Down-Regulation (Post-Workout):** {COOL_DOWNS[workout_day]}")
                
            combined_text = WARM_UPS.get(workout_day, "") + COOL_DOWNS.get(workout_day, "")
            relevant_mobility = {k: v for k, v in MOBILITY_GUIDES.items() if k.lower() in combined_text.lower()}
            if relevant_mobility:
                with st.expander("📖 View Mobility & Stretching Guides", expanded=False):
                    for m_name, m_guide in relevant_mobility.items(): st.markdown(f"**{m_name}:** {m_guide}")
        
        st.write("---")
        
        if selected_exercises:
            primary_ex = selected_exercises[0]
            base_sets, _ = get_target_reps_and_sets(primary_ex)
            ex_cap = EXERCISE_CAPS.get(primary_ex, 5)
            suggested_sets = base_sets
            
            if is_deload:
                suggested_sets = max(1, base_sets - 1)
            else:
                ex_df_primary = df_lifts_recent[(df_lifts_recent['Exercise'] == primary_ex) & (df_lifts_recent['Reps_or_Mins'] > 0)]
                if not ex_df_primary.empty:
                    last_date = ex_df_primary['Date'].max()
                    last_session = ex_df_primary[ex_df_primary['Date'] == last_date]
                    last_sets_done = last_session['Set_Number'].max()
                    if last_sets_done < base_sets: suggested_sets = base_sets
                    else: suggested_sets = min(ex_cap, last_sets_done + 1)
            
            num_sets = st.number_input("🎯 Target Rounds (Auto-Calculated by Mesocycle):", min_value=1, max_value=10, value=int(suggested_sets), step=1)
            
            if suggested_sets == ex_cap and not is_deload:
                st.success(f"🏆 **Volume Cap Reached:** {primary_ex} is capped at {ex_cap} sets to prevent systemic junk volume. Focus on adding weight or reducing rest!")
                
            st.write("---")
            st.markdown("#### 🦍 Gorilla Protocol: Just Lift.")
            
            default_vals = {}
            for exercise in selected_exercises:
                ex_df = df_lifts_recent[(df_lifts_recent['Exercise'] == exercise) & (df_lifts_recent['Reps_or_Mins'] > 0)].sort_values(by=['Date', 'Set_Number'])
                fatigue_drop = False
                
                if not ex_df.empty:
                    max_all_time_weight = ex_df['Weight'].max()
                    working_sessions = ex_df[ex_df['Weight'] >= (max_all_time_weight * 0.85)]
                    dates = working_sessions['Date'].unique() if not working_sessions.empty else ex_df['Date'].unique()
                    last_date = dates[-1]
                    last_session = ex_df[ex_df['Date'] == last_date]
                    set_1 = last_session[last_session['Set_Number'] == 1]
                    
                    if not set_1.empty:
                        s1_data = set_1.iloc[0]
                        last_weight = float(s1_data['Weight'])
                        last_reps = int(s1_data['Reps_or_Mins'])
                        last_band = s1_data['Band']
                        last_var = s1_data.get('Variation', 'Flat') if 'Variation' in s1_data else 'Flat'
                        target_sets, top_rep = get_target_reps_and_sets(exercise)
                        min_reps_last_session = last_session['Reps_or_Mins'].min()
                        
                        s1_history = ex_df[ex_df['Set_Number'] == 1].sort_values('Date')
                        last_3 = s1_history.tail(3)
                        plateau = False
                        bleed_out = False
                        
                        is_bw_only = exercise in BODYWEIGHT_ONLY
                        is_pure_band = exercise in PURE_BAND_EXERCISES
                        is_kb = "Kettlebell" in exercise or "KB" in exercise
                        
                        if len(last_3) >= 3 and not is_deload:
                            w_vals = last_3['Weight'].tolist()
                            r_vals = last_3['Reps_or_Mins'].tolist()
                            if w_vals[0] == w_vals[1] == w_vals[2] and r_vals[0] == r_vals[1] == r_vals[2]:
                                plateau = True
                            elif w_vals[0] == w_vals[1] == w_vals[2] and r_vals[0] > r_vals[1] > r_vals[2]:
                                bleed_out = True

                        if is_deload:
                            calc_w = 0.0 if (is_bw_only or is_pure_band) else snap_to_weight(last_weight * 0.8, exercise)
                            calc_b = last_band
                            
                            if calc_w == 0.0 and last_band != "None":
                                band_keys = list(BAND_SUBTRACTIONS.keys())
                                b_idx = band_keys.index(last_band) if last_band in band_keys else 0
                                if exercise in ASSISTED_EXERCISES and b_idx < len(band_keys) - 1:
                                    calc_b = band_keys[b_idx + 1]
                                elif exercise in RESISTED_EXERCISES and b_idx > 0:
                                    calc_b = band_keys[b_idx - 1]
                            
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': calc_b, 'v': last_var, 'fatigue': False}
                            if calc_b != last_band:
                                st.info(f"🧘 **{exercise}:** Deload week. Shifted band to **{calc_b}**.")
                            elif not is_bw_only and not is_pure_band:
                                st.info(f"🧘 **{exercise}:** Deload week. Dropped to **{calc_w}kg**.")
                            else:
                                st.info(f"🧘 **{exercise}:** Deload week. Focus on light technique execution.")

                        elif plateau:
                            calc_w = 0.0 if (is_bw_only or is_pure_band) else max(0.0, snap_to_weight(last_weight * 0.9, exercise))
                            st.warning(f"🚧 **Plateau Alert:** Stuck for 3 weeks. Neurological stagnation. Drop to **{calc_w}kg** and push high reps today.")
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': last_band, 'v': last_var, 'fatigue': False}
                        elif bleed_out:
                            calc_w = 0.0 if (is_bw_only or is_pure_band) else max(0.0, snap_to_weight(last_weight * 0.85, exercise))
                            if hrv_alert: st.error(f"🛑 **CNS FRIED:** {exercise} reps regressing & HRV tanking. Mandatory drop for localized active recovery.")
                            else: st.error(f"🩸 **Bleed-Out Alert:** {exercise} reps regressing. Tissue fatigue detected. Dropping weight.")
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': last_band, 'v': last_var, 'fatigue': False}
                        else:
                            if min_reps_last_session < 5: 
                                fatigue_drop = True
                                if hrv_alert: st.error(f"🛑 **CNS Alert:** {exercise} dropped below target AND your HRV is tanking.")
                                
                                if exercise in ASSISTED_EXERCISES:
                                    if last_weight > 0.0:
                                        raw_new = last_weight - max(2.5, last_weight * 0.10)
                                        new_w = max(0.0, snap_to_weight(raw_new, exercise))
                                        st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. Strip plate for Sets 2+.")
                                    else:
                                        band_keys = list(BAND_SUBTRACTIONS.keys())
                                        b_idx = band_keys.index(last_band) if last_band in band_keys else 0
                                        if b_idx < len(band_keys) - 1:
                                            next_band = band_keys[b_idx + 1]
                                            st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. Switch to **{next_band}** for Sets 2+.")
                                        else:
                                            st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. Max band reached.")
                                elif exercise in RESISTED_EXERCISES:
                                    band_keys = list(BAND_SUBTRACTIONS.keys())
                                    b_idx = band_keys.index(last_band) if last_band in band_keys else 0
                                    if b_idx > 0:
                                        prev_band = band_keys[b_idx - 1]
                                        st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. Drop to **{prev_band}** for Sets 2+.")
                                    else:
                                        st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. No lighter band available.")
                                elif not is_bw_only:
                                    raw_new = last_weight - max(2.5, last_weight * 0.10)
                                    new_w = max(0.0, snap_to_weight(raw_new, exercise))
                                    st.error(f"⚠️ **Fatigue Alert:** {exercise} dropped. Drop load for Sets 2+.")

                            # PROGRESSION LOGIC
                            if is_bw_only:
                                calc_w = 0.0
                                if last_reps >= top_rep:
                                    st.success(f"✅ **{exercise}:** Hit {last_reps} reps! To overload, slow the eccentric phase by 2s or push beyond the rep cap.")
                                else:
                                    st.warning(f"🎯 **{exercise}:** Hit {last_reps}/{top_rep} reps last week. Keep fighting for reps.")
                                calc_b = last_band
                                
                            elif is_pure_band:
                                calc_w = 0.0
                                band_keys = list(BAND_SUBTRACTIONS.keys())
                                b_idx = band_keys.index(last_band) if last_band in band_keys else 0
                                if last_reps >= top_rep:
                                    next_b = band_keys[min(b_idx + 1, len(band_keys) - 1)]
                                    calc_b = next_b
                                    if next_b != last_band:
                                        st.success(f"📈 **{exercise}:** Hit {last_reps} reps. Band resistance increased to **{next_b}**!")
                                    else:
                                        st.success(f"🏆 **{exercise}:** Max band reached! Focus on density or slower reps.")
                                else:
                                    calc_b = last_band
                                    st.warning(f"🎯 **{exercise}:** Hit {last_reps}/{top_rep} reps. Hold at **{last_band}**.")
                                    
                            elif is_kb:
                                calc_b = last_band
                                if last_reps >= top_rep:
                                    calc_w = get_next_weight(last_weight, exercise)
                                    if calc_w == last_weight and last_weight >= 20.0:
                                        st.success(f"🏆 **{exercise}:** Max Kettlebell (20kg) reached! Overload by reducing rest times or increasing reps.")
                                    else:
                                        st.success(f"📈 **{exercise}:** Hit {last_reps} reps. Load increased to **{calc_w}kg**.")
                                else:
                                    calc_w = last_weight
                                    st.warning(f"🎯 **{exercise}:** Hit {last_reps}/{top_rep} reps. Hold at **{calc_w}kg**.")
                                    
                            else:
                                calc_b = last_band
                                if last_reps >= top_rep: 
                                    calc_w = get_next_weight(last_weight, exercise)
                                    st.success(f"📈 **{exercise}:** Hit {last_reps} reps last week. Load increased to **{calc_w}kg**.")
                                else: 
                                    calc_w = last_weight
                                    st.warning(f"🎯 **{exercise}:** Hit {last_reps}/{top_rep} reps last week. Hold at **{calc_w}kg** and fight.")
                                    
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': calc_b, 'v': last_var, 'fatigue': fatigue_drop}
                            
                        if exercise in HEAVY_COMPOUNDS and default_vals[exercise]['w'] >= 20.0:
                            with st.expander(f"🔥 Warm-Up Load: {exercise}", expanded=False):
                                trg_w = default_vals[exercise]['w']
                                w1 = 20.0 if "Barbell" in exercise or "RDL" in exercise else max(5.0, snap_to_weight(trg_w*0.3, exercise))
                                w2 = snap_to_weight(trg_w * 0.5, exercise)
                                w3 = snap_to_weight(trg_w * 0.8, exercise)
                                st.markdown(f"- **Set 1:** {w1}kg × 8-10 reps\n- **Set 2:** {w2}kg × 5 reps\n- **Set 3:** {w3}kg × 2-3 reps")
                        guide = EXERCISE_GUIDES.get(exercise)
                        if guide:
                            with st.expander(f"📖 Form & Setup: {exercise}", expanded=False): st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")

                    else:
                        st.info(f"**{exercise}:** Establish baseline weight today.")
                        default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None", 'v': "Flat", 'fatigue': False}
                        guide = EXERCISE_GUIDES.get(exercise)
                        if guide:
                            with st.expander(f"📖 Form & Setup: {exercise}", expanded=False): st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")
                else:
                    st.info(f"**{exercise}:** Establish baseline weight today.")
                    default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None", 'v': "Flat", 'fatigue': False}
                    guide = EXERCISE_GUIDES.get(exercise)
                    if guide:
                        with st.expander(f"📖 Form & Setup: {exercise}", expanded=False): st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")
            
            st.write("---")
            with st.form("lifting_form", clear_on_submit=True):
                weights, reps, reps_l, reps_r, rirs, bands, variations = {}, {}, {}, {}, {}, {}, {}
                for i in range(1, num_sets + 1):
                    st.markdown(f"#### 🔁 Round {i}")
                    
                    if not "Freestyle" in workout_day:
                        rest_flow = REST_PROTOCOLS.get(workout_day, {}).get(workout_block, "")
                        if rest_flow:
                            st.info(f"⏱️ **Execution Flow:** {rest_flow}")
                            
                    for exercise in selected_exercises:
                        is_uni = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ASSISTED_EXERCISES or exercise in RESISTED_EXERCISES
                        is_bw_only = exercise in BODYWEIGHT_ONLY
                        is_pure_band = exercise in PURE_BAND_EXERCISES
                        is_pushup = exercise == "Push-Ups"
                        
                        _, top_rep = get_target_reps_and_sets(exercise)
                        st.markdown(f"**{exercise}** *(Target: {top_rep} reps)*")
                        
                        def_w = float(default_vals.get(exercise, {}).get('w', 0.0))
                        def_b = default_vals.get(exercise, {}).get('b', "None")
                        def_v = default_vals.get(exercise, {}).get('v', "Flat")
                        
                        band_keys = list(BAND_SUBTRACTIONS.keys())
                        b_idx = band_keys.index(def_b) if def_b in band_keys else 0
                        v_idx = PUSH_UP_VARIATIONS.index(def_v) if def_v in PUSH_UP_VARIATIONS else 1
                        
                        if i > 1 and default_vals.get(exercise, {}).get('fatigue', False):
                            if exercise in ASSISTED_EXERCISES:
                                if def_w > 0.0:
                                    raw_new = def_w - max(2.5, def_w * 0.10)
                                    def_w = max(0.0, snap_to_weight(raw_new, exercise))
                                else:
                                    if b_idx < len(band_keys) - 1:
                                        b_idx += 1 
                                        def_b = band_keys[b_idx]
                            elif exercise in RESISTED_EXERCISES:
                                if b_idx > 0:
                                    b_idx -= 1 
                                    def_b = band_keys[b_idx]
                            elif not is_bw_only and not is_pure_band:
                                raw_new = def_w - max(2.5, def_w * 0.10)
                                def_w = max(0.0, snap_to_weight(raw_new, exercise))

                        key = f"{exercise}_{i}" 
                        
                        if uses_band:
                            c1, c2, c3, c4 = st.columns([1, 1, 1.5, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=0.5, value=0.0 if is_pure_band else def_w, disabled=is_pure_band, key=f"w_{key}")
                            if is_uni:
                                sc1, sc2 = c2.columns(2)
                                reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                                reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                            else: reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            bands[key] = c3.selectbox("Band", band_keys, index=b_idx, key=f"b_{key}")
                            rirs[key] = c4.slider("RIR", 0, 5, 2, 1, key=f"rir_{key}")
                        elif is_pushup:
                            c1, c2, c3, c4 = st.columns([1, 1, 1.5, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=0.5, value=0.0, disabled=True, key=f"w_{key}")
                            reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            variations[key] = c3.selectbox("Variation", PUSH_UP_VARIATIONS, index=v_idx, key=f"v_{key}")
                            rirs[key] = c4.slider("RIR", 0, 5, 2, 1, key=f"rir_{key}")
                        else:
                            c1, c2, c3 = st.columns([1, 1, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=0.5, value=0.0 if is_bw_only else def_w, disabled=is_bw_only, key=f"w_{key}")
                            if is_uni:
                                sc1, sc2 = c2.columns(2)
                                reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                                reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                            else: reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            rirs[key] = c3.slider("RIR", 0, 5, 2, 1, key=f"rir_{key}")
                    st.write("---") 
                
                if st.form_submit_button("Save Workouts To Database", type="primary"):
                    
                    sanity_failed = False
                    for exercise in selected_exercises:
                        max_hist_w = df_lifts[df_lifts['Exercise'] == exercise]['Weight'].max() if not df_lifts.empty else 0.0
                        for i in range(1, num_sets + 1):
                            key = f"{exercise}_{i}"
                            w_val = weights.get(key, 0.0)
                            is_uni = exercise in UNILATERAL_EXERCISES
                            reps_val = max(reps_l.get(key, 0), reps_r.get(key, 0)) if is_uni else reps.get(key, 0)
                            
                            if reps_val > 0 and max_hist_w >= 10.0 and w_val > (max_hist_w * 1.5):
                                st.error(f"🛑 **Sanity Check Failed:** You logged **{w_val}kg** for {exercise}. Your historical max is **{max_hist_w}kg**. Did your thumb slip? (Fix the typo and click save again).")
                                sanity_failed = True
                                break
                        if sanity_failed: break
                            
                    if not sanity_failed:
                        new_rows = []
                        for exercise in selected_exercises:
                            is_uni = exercise in UNILATERAL_EXERCISES
                            uses_band = exercise in ASSISTED_EXERCISES or exercise in RESISTED_EXERCISES
                            is_pushup = exercise == "Push-Ups"
                            for i in range(1, num_sets + 1):
                                key = f"{exercise}_{i}"
                                b_val = bands[key] if uses_band else "None"
                                v_val = variations[key] if is_pushup else "None"
                                if (is_uni and (reps_l[key] > 0 or reps_r[key] > 0)) or (not is_uni and reps[key] > 0):
                                    base_data = {'Date': date_input.strftime('%Y-%m-%d'), 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': b_val, 'Variation': v_val, 'Distance_km': 0.0, 'Bodyweight': st.session_state['h_weight'], 'RIR': rirs[key]}
                                    if is_uni:
                                        if reps_l[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_l[key], 'Side': 'Left'})
                                        if reps_r[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_r[key], 'Side': 'Right'})
                                    else: new_rows.append({**base_data, 'Reps_or_Mins': reps[key], 'Side': 'Both'})
                        if new_rows:
                            save_to_sheet(ws_lifts, pd.DataFrame(new_rows), LIFTS_COLS)
                            
                            if is_deload:
                                try:
                                    ws_system.update_acell('B1', date_input.strftime('%Y-%m-%d'))
                                    get_last_deload.clear()
                                except Exception: pass
                                
                            st.success(f"✅ Logged {len(new_rows)} sets to the Lifts database!")
                        else: st.warning("No reps logged.")

    with sub_cardio:
        st.subheader("🏃‍♂️ Aerobic Cardio Engine")
        with st.expander("📖 Cardio Protocols & Execution Guides", expanded=False):
            st.markdown("### 🔥 4x4 Norwegian VO2 Max Protocol")
            st.markdown("- **Warm-up:** 5 mins light dynamic stretching + 3 mins easy pacing to build heart rate.")
            st.markdown("- **Work Interval:** 4 minutes pushing hard into Zone 4/5 (approx. 85-95% Max HR). You should be breathing very heavily by the end.")
            st.markdown("- **Active Recovery:** 3 minutes of very easy, light pedaling/rowing (Zone 1/2) to clear lactic acid.")
            st.markdown("- **Repeat:** Do this 4 times total.")
            st.markdown("- **Cool-down:** 3 mins loose pedaling + 60-sec standing calf stretch per leg.")
            st.write("---")
            st.markdown("### 🐢 Zone 2 Flush & Base Building")
            st.markdown("- **Target Duration:** 60-90 minutes. *(Do not exceed 90 mins as it generates unnecessary systemic fatigue that interferes with lifting recovery).*")
            st.markdown("- **Intensity:** Strict Zone 2 (approx. 60-70% Max HR). You should be able to hold a conversation or comfortably watch anime without gasping for breath.")
            st.markdown("- **Goal:** Mitochondrial density and aerobic base building. Pushing into Zone 3 kills the specific adaptations we want here. Stay slow!")

        st.write("---")
        st.write("Sync your specific session from Garmin, filtering out the noise. Data isolates perfectly into your Cardio database.")
        mfa_input_c = st.text_input("MFA Code (Leave blank if 2FA disabled or token saved)", max_chars=6, key="mfa_cardio")
        sync_target = st.selectbox("Select Activity to Sync:", ["Row Indoor", "Bike Indoor"])
        if st.button("🔄 Sync Target Garmin Activity"):
            with st.spinner(f"Hunting down your latest {sync_target} session..."):
                client = get_garmin_client(mfa_input_c)
                if client:
                    try:
                        activities = client.get_activities(0, 20) 
                        found_act = None
                        if activities:
                            for act in activities:
                                name = act.get('activityName', '').lower()
                                act_type = act.get('activityType', {}).get('typeKey', '').lower()
                                if sync_target == "Row Indoor" and ("row" in name or "row" in act_type):
                                    found_act = act
                                    break
                                elif sync_target == "Bike Indoor" and ("bike" in name or "cycl" in act_type or "bike" in act_type):
                                    found_act = act
                                    break
                        if found_act:
                            st.session_state['g_dur'] = round(found_act.get('duration', 0) / 60, 1)
                            st.session_state['g_dist'] = round(found_act.get('distance', 0) / 1000, 2)
                            st.session_state['g_avg_hr'] = float(found_act.get('averageHR', 130.0))
                            st.session_state['g_max_hr'] = float(found_act.get('maxHR', 165.0))
                            st.success(f"🎯 Target Acquired: {found_act.get('activityName', 'Unknown')} ({st.session_state['g_dur']} mins)")
                        else: st.error(f"⚠️ Could not find a recent '{sync_target}' session in your last 20 activities.")
                    except Exception as e: st.error(f"Activity Sync Failed: {e}")

        st.write("---")
        with st.form("cardio_form", clear_on_submit=True):
            c_ex = st.selectbox("Select Protocol Executed", ["4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"])
            c_date = st.date_input("Date", date.today(), key="cardio_date")
            duration = st.number_input("Duration (Mins)", min_value=1.0, value=st.session_state['g_dur'], step=1.0)
            distance = st.number_input("Distance (km)", min_value=0.0, value=st.session_state['g_dist'], step=0.1)
            avg_resp = st.number_input("Avg Resp (brpm)", min_value=0.0, value=20.0, step=1.0)
            avg_hr = st.number_input("Avg HR (bpm)", min_value=40.0, value=st.session_state['g_avg_hr'], step=1.0)
            max_hr = st.number_input("Max HR (bpm)", min_value=40.0, value=st.session_state['g_max_hr'], step=1.0)
            zc1, zc2, zc3, zc4, zc5 = st.columns(5)
            z1 = zc1.number_input("Z1", min_value=0.0, step=1.0)
            z2 = zc2.number_input("Z2", min_value=0.0, step=1.0)
            z3 = zc3.number_input("Z3", min_value=0.0, step=1.0)
            z4 = zc4.number_input("Z4", min_value=0.0, step=1.0)
            z5 = zc5.number_input("Z5", min_value=0.0, step=1.0)
            if st.form_submit_button("Save Cardio to Database", type="primary"):
                cardio_data = {'Date': c_date, 'Exercise': c_ex, 'Duration_Mins': duration, 'Distance_km': distance, 'Avg_HR': avg_hr, 'Max_HR': max_hr, 'Avg_Resp': avg_resp, 'Z1_Mins': z1, 'Z2_Mins': z2, 'Z3_Mins': z3, 'Z4_Mins': z4, 'Z5_Mins': z5}
                save_to_sheet(ws_cardio, pd.DataFrame([cardio_data]), CARDIO_COLS)
                st.success("✅ Cardio Data isolated into pure Cardio DB!")

    with sub_mob:
        st.subheader("🌙 The Daily System Reset")
        st.info("**Frequency:** Daily Evening Protocol  \n**Goal:** Restore joint range of motion, down-regulate the nervous system, and achieve pain-free living.")
        st.write("Check these off as you go for that dopamine hit! *(Resets daily, not logged to database)*")
        reset_c1, reset_c2 = st.columns(2)
        half = len(DAILY_SYSTEM_RESET) // 2
        for i, (ex_name, details) in enumerate(DAILY_SYSTEM_RESET.items()):
            col = reset_c1 if i < half else reset_c2
            col.checkbox(ex_name, key=f"reset_chk_{i}")
        st.write("---")
        st.markdown("### 📖 Execution Guides")
        for ex_name, details in DAILY_SYSTEM_RESET.items():
            with st.expander(ex_name, expanded=False):
                st.markdown(f"**Target:** {details['Target']}")
                st.markdown(f"**Execution:** {details['Execution']}")
                st.markdown(f"**Progression:** {details['Progression']}")

with tab_health:
    st.subheader("🧬 Bio Data Sync")
    st.write("Manage your morning stats here. Data is safely isolated into your pure Health database.")
    mfa_input_h = st.text_input("MFA Code (Leave blank if 2FA disabled or token saved)", max_chars=6, key="mfa_health")
    h_date = st.date_input("Date", date.today(), key="health_date")
    if st.button("🔄 Sync Scale & Sleep (Auto-Save)"):
        with st.spinner(f"Pulling biological data for {h_date}..."):
            client = get_garmin_client(mfa_input_h)
            if client:
                target_iso = h_date.isoformat()
                try:
                    weigh_ins = client.get_body_composition(target_iso)
                    if weigh_ins and weigh_ins.get('dateWeightList'):
                        latest = weigh_ins['dateWeightList'][-1]
                        raw_w = latest.get('weight', st.session_state['h_weight'])
                        st.session_state['h_weight'] = float(raw_w / 1000 if raw_w > 1000 else raw_w)
                        st.session_state['h_bf'] = float(latest.get('bodyFat', st.session_state['h_bf']))
                        st.session_state['h_muscle'] = float(latest.get('muscleMass', st.session_state['h_muscle'] * 1000) / 1000)
                        st.toast("✅ Scale data found")
                except Exception: pass
                try:
                    sleep_data = client.get_sleep_data(target_iso)
                    if sleep_data and 'dailySleepDTO' in sleep_data:
                        score = sleep_data['dailySleepDTO'].get('sleepScores', {}).get('overall', {}).get('value')
                        if score: st.session_state['h_sleep'] = int(score)
                    stats = client.get_stats(target_iso)
                    if stats and 'restingHeartRate' in stats: st.session_state['h_rhr'] = int(stats['restingHeartRate'])
                    hrv_data = client.get_hrv_data(target_iso)
                    if hrv_data and 'hrvSummary' in hrv_data:
                        hrv = hrv_data['hrvSummary'].get('lastNightAvg')
                        if hrv: st.session_state['h_hrv'] = int(hrv)
                except Exception: pass
                
                lean_mass = st.session_state['h_weight'] * (1 - (st.session_state['h_bf'] / 100))
                ffmi = lean_mass / ((USER_HEIGHT / 100) ** 2) if USER_HEIGHT > 0 else 0
                health_data = {'Date': h_date, 'Weight_kg': st.session_state['h_weight'], 'Body_Fat_Pct': st.session_state['h_bf'], 'Muscle_Mass_kg': st.session_state['h_muscle'], 'Sleep_Score': st.session_state['h_sleep'], 'FFMI': ffmi, 'RHR': st.session_state['h_rhr'], 'HRV': st.session_state['h_hrv'], 'Height_cm': USER_HEIGHT}
                save_to_sheet(ws_health, pd.DataFrame([health_data]), HEALTH_COLS)
                st.success(f"✅ Biological data safely isolated in Health DB for {h_date}!")

    st.write("---")
    with st.form("health_form", clear_on_submit=True):
        st.markdown("**Current Bio Data (Manual Override):**")
        h_weight = st.number_input("Weight (kg)", value=st.session_state['h_weight'], step=0.1)
        h_bf = st.number_input("Body Fat (%)", value=st.session_state['h_bf'], step=0.1)
        h_muscle = st.number_input("Muscle (kg)", value=st.session_state['h_muscle'], step=0.1)
        h_sleep = st.number_input("Sleep Score (0-100)", value=st.session_state['h_sleep'], step=1)
        h_rhr = st.number_input("Resting HR (bpm)", value=st.session_state['h_rhr'], step=1)
        h_hrv = st.number_input("HRV (ms)", value=st.session_state['h_hrv'], step=1)
        if st.form_submit_button("Save Manual Entry"):
            lean_mass = h_weight * (1 - (h_bf / 100))
            ffmi = lean_mass / ((USER_HEIGHT / 100) ** 2) if USER_HEIGHT > 0 else 0
            health_data = {'Date': h_date, 'Weight_kg': h_weight, 'Body_Fat_Pct': h_bf, 'Muscle_Mass_kg': h_muscle, 'Sleep_Score': h_sleep, 'FFMI': ffmi, 'RHR': h_rhr, 'HRV': h_hrv, 'Height_cm': USER_HEIGHT}
            save_to_sheet(ws_health, pd.DataFrame([health_data]), HEALTH_COLS)
            st.success("✅ Saved manual health entry!")

with tab_analytics:
    if df_lifts.empty and df_health.empty and df_cardio.empty:
        st.info("Awaiting Data...")
    else:
        health_latest = df_health.groupby('Date').last().reset_index() if not df_health.empty else pd.DataFrame(columns=HEALTH_COLS)
        lift_df = df_lifts[(df_lifts['Reps_or_Mins'] > 0)].copy()
        
        if not lift_df.empty and not health_latest.empty: lift_df = pd.merge(lift_df, health_latest[['Date', 'Sleep_Score']], on='Date', how='left')
        elif not lift_df.empty: lift_df['Sleep_Score'] = 0

        at1, at2, at3, at4, at5, at6, at7 = st.tabs(["👻 Milestones", "📈 Relative Strength", "🔥 INOL & RIR", "⚖️ Volume & ACWR", "🦵 Radar", "🫀 Cardio Engine", "🧬 Recomp & Recovery"])
        
        with at1:
            st.subheader("Historical Milestones")
            if not lift_df.empty:
                recent_30 = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=30)]
                monthly_tonnage = recent_30['Volume'].sum()
                if monthly_tonnage > 0: st.info(f"**Total Volume (Last 30 Days):** {monthly_tonnage:,.1f} kg")
                
                pr_ex = st.selectbox("Select Exercise for PRs", lift_df['Exercise'].unique())
                pr_df = lift_df[lift_df['Exercise'] == pr_ex]
                if not pr_df.empty:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("1RM (Epley)", f"{pr_df['Epley_1RM'].max():.1f} kg")
                    c2.metric("5RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 5]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 5].empty else "N/A")
                    c3.metric("10RM Record", f"{pr_df[pr_df['Reps_or_Mins'] >= 10]['Effective_Weight'].max():.1f} kg" if not pr_df[pr_df['Reps_or_Mins'] >= 10].empty else "N/A")

        with at2:
            st.subheader("Relative Strength")
            if not lift_df.empty:
                vel_ex = st.selectbox("Select Exercise", lift_df['Exercise'].unique(), key='vel_ex')
                v_df = lift_df[lift_df['Exercise'] == vel_ex].groupby('Date').agg({'Epley_1RM': 'max', 'Bodyweight': 'mean'}).reset_index()
                if not v_df.empty:
                    v_df['Relative_Strength'] = v_df['Epley_1RM'] / v_df['Bodyweight'].replace(0, 1) 
                    fig_rel = go.Figure(data=go.Scatter(x=v_df['Date'], y=v_df['Relative_Strength'], mode='lines+markers', line=dict(color='#00CC96', width=3)))
                    fig_rel.update_layout(title=f"Relative Strength Multiplier (e1RM ÷ Bodyweight)")
                    fig_rel.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig_rel, use_container_width=True)

        with at3:
            st.subheader("INOL & Fatigue Curves")
            if not lift_df.empty:
                inol_ex = st.selectbox("Analyze Exercise", lift_df['Exercise'].unique(), key='inol_ex')
                i_df = lift_df[lift_df['Exercise'] == inol_ex].copy()
                if not i_df.empty:
                    global_max = i_df['Epley_1RM'].max()
                    i_df['Intensity_%'] = (i_df['Effective_Weight'] / global_max) * 100
                    i_df['INOL'] = (i_df['Reps_or_Mins'] / (100 - i_df['Intensity_%'].clip(upper=99))) * 0.5
                    daily_inol = i_df.groupby('Date')['INOL'].sum().reset_index()
                    fig2 = px.bar(daily_inol, x='Date', y='INOL', title="Daily Session INOL Score", color='INOL', color_continuous_scale='RdYlGn_r')
                    fig2.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig2, use_container_width=True)

            st.write("---")
            st.markdown("### 🛑 Proximity to Failure (Average RIR)")
            st.write("Are you sandbagging? RIR should ideally sit between 0 and 2 for true muscle growth.")
            if not lift_df.empty:
                rir_df = lift_df[lift_df['RIR'] >= 0].groupby('Date')['RIR'].mean().reset_index()
                if not rir_df.empty:
                    fig_rir = px.bar(rir_df, x='Date', y='RIR', title="Average Daily Reps in Reserve (RIR)", color='RIR', color_continuous_scale='RdYlGn')
                    fig_rir.update_yaxes(autorange="reversed") 
                    fig_rir.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig_rir, use_container_width=True)

        with at4:
            st.subheader("⚖️ Volume Engineering (MEV/MRV)")
            if not lift_df.empty:
                st.markdown("### 🚦 Current 7-Day Speedometer")
                recent_7_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=7)]
                muscle_sets = {}
                for _, row in recent_7_df.iterrows():
                    ex = row['Exercise']
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items(): muscle_sets[muscle] = muscle_sets.get(muscle, 0) + (1 * multiplier)
                
                if muscle_sets:
                    mev_df = pd.DataFrame(list(muscle_sets.items()), columns=['Muscle', 'Sets'])
                    mev_df['MEV'] = mev_df['Muscle'].apply(lambda x: VOLUME_THRESHOLDS.get(x, {}).get('MEV', 10))
                    mev_df['MRV'] = mev_df['Muscle'].apply(lambda x: VOLUME_THRESHOLDS.get(x, {}).get('MRV', 20))
                    
                    def assign_color(row):
                        if row['Sets'] < row['MEV']: return '#A0AEC0'
                        elif row['Sets'] > row['MRV']: return '#FF4B4B'
                        else: return '#00CC96'
                        
                    mev_df['Color'] = mev_df.apply(assign_color, axis=1)
                    
                    fig_mev = go.Figure()
                    fig_mev.add_trace(go.Bar(x=mev_df['Muscle'], y=mev_df['Sets'], marker_color=mev_df['Color'], name='Actual Sets'))
                    fig_mev.add_trace(go.Scatter(x=mev_df['Muscle'], y=mev_df['MEV'], mode='markers', name='MEV', marker=dict(symbol='line-ew', size=40, color='#00CC96', line=dict(width=4))))
                    fig_mev.add_trace(go.Scatter(x=mev_df['Muscle'], y=mev_df['MRV'], mode='markers', name='MRV', marker=dict(symbol='line-ew', size=40, color='#FF4B4B', line=dict(width=4))))
                    fig_mev.update_layout(title="7-Day Traffic Light Tracker", yaxis_title="Total Sets", barmode='overlay')
                    st.plotly_chart(fig_mev, use_container_width=True)
                else: st.info("No lifting volume detected in the last 7 days.")

                st.write("---")
                st.markdown("### 📈 4-Week Mesocycle GPS")
                recent_28_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=28)].copy()
                trend_data = []
                for _, row in recent_28_df.iterrows():
                    ex = row['Exercise']
                    week_label = row['Date'].strftime('%Y-W%V')
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items(): trend_data.append({'Week': week_label, 'Muscle': muscle, 'Sets': 1 * multiplier})
                if trend_data:
                    trend_df = pd.DataFrame(trend_data).groupby(['Week', 'Muscle'])['Sets'].sum().reset_index()
                    fig_trend = px.line(trend_df, x='Week', y='Sets', color='Muscle', markers=True, title="Muscle Volume Escalation (Last 4 Weeks)")
                    st.plotly_chart(fig_trend, use_container_width=True)
                else: st.info("Not enough data yet for a 4-week trend.")
                
                st.write("---")
                st.markdown("### ⚠️ Acute:Chronic Workload Ratio (ACWR)")
                st.write("Tracks injury risk. **Sweet Spot:** 0.8 - 1.3. **Danger Zone:** > 1.5.")
                daily_vol = lift_df.groupby('Date')['Volume'].sum().reset_index().set_index('Date').resample('D').sum().fillna(0)
                daily_vol['Acute_7D'] = daily_vol['Volume'].rolling(window=7, min_periods=1).sum()
                daily_vol['Chronic_28D'] = daily_vol['Volume'].rolling(window=28, min_periods=1).sum() / 4
                daily_vol['ACWR'] = daily_vol['Acute_7D'] / daily_vol['Chronic_28D'].replace(0, np.nan)
                fig_acwr = go.Figure()
                fig_acwr.add_trace(go.Scatter(x=daily_vol.index, y=daily_vol['ACWR'], mode='lines+markers', name='ACWR', line=dict(color='#8A2BE2', width=3)))
                fig_acwr.add_hrect(y0=0.8, y1=1.3, fillcolor="#00CC96", opacity=0.2, line_width=0, annotation_text="Sweet Spot (0.8 - 1.3)", annotation_position="top left")
                fig_acwr.add_hline(y=1.5, line_dash="dash", line_color="#FF4B4B", annotation_text="Danger Zone (>1.5)")
                fig_acwr.update_layout(yaxis_title="ACWR Ratio")
                st.plotly_chart(fig_acwr, use_container_width=True)

        with at5:
            st.subheader("7-Day Microcycle Radar")
            if not lift_df.empty:
                recent_7_df = lift_df[lift_df['Date'] >= pd.to_datetime(date.today()) - pd.Timedelta(days=7)]
                muscle_sets = {}
                for _, row in recent_7_df.iterrows():
                    ex = row['Exercise']
                    if ex in MUSCLE_MAP:
                        for muscle, multiplier in MUSCLE_MAP[ex].items(): muscle_sets[muscle] = muscle_sets.get(muscle, 0) + (1 * multiplier)
                if muscle_sets:
                    heat_df = pd.DataFrame(list(muscle_sets.items()), columns=['Muscle', 'Total Sets'])
                    fig_radar = go.Figure(data=go.Scatterpolar(r=heat_df['Total Sets'].tolist() + [heat_df['Total Sets'].iloc[0]], theta=heat_df['Muscle'].tolist() + [heat_df['Muscle'].iloc[0]], fill='toself'))
                    st.plotly_chart(fig_radar, use_container_width=True)

        with at6:
            st.subheader("🫀 Clean Cardio Analytics")
            if not df_cardio.empty:
                c_ex = st.selectbox("Select Cardio Type", df_cardio['Exercise'].unique())
                cx_df = df_cardio[df_cardio['Exercise'] == c_ex].copy()
                if not cx_df.empty and 'Avg_HR' in cx_df.columns:
                    cx_df['Metric_Value'] = (cx_df['Duration_Mins'] * 60) / (cx_df['Distance_km'] * 1000 / 500) if "Rowing" in c_ex else cx_df['Distance_km'] / (cx_df['Duration_Mins'] / 60)
                    
                    fig_aerobic = go.Figure()
                    fig_aerobic.add_trace(go.Bar(x=cx_df['Date'], y=cx_df['Metric_Value'], name='Speed/Pace Output', marker_color='#1f77b4', yaxis='y1'))
                    fig_aerobic.add_trace(go.Scatter(x=cx_df['Date'], y=cx_df['Avg_HR'], name='Avg HR', mode='lines+markers', line=dict(color='#FF4B4B', width=3), yaxis='y2'))
                    fig_aerobic.update_layout(yaxis=dict(title="Pace/Speed", side='left'), yaxis2=dict(title='Avg HR (bpm)', side='right', overlaying='y', showgrid=False))
                    fig_aerobic.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig_aerobic, use_container_width=True)
                    
                    st.write("---")
                    st.markdown("### 🚀 Aerobic Efficiency (Cardiac Drift)")
                    st.write("Measures Output (Speed in km/h) per Heart Beat. An upward trend proves extreme aerobic adaptation.")
                    cx_df['Speed_kmh'] = cx_df['Distance_km'] / (cx_df['Duration_Mins'] / 60)
                    cx_df['Efficiency'] = (cx_df['Speed_kmh'] / cx_df['Avg_HR']) * 100
                    fig_eff = px.line(cx_df, x='Date', y='Efficiency', markers=True, title="Aerobic Efficiency Score", color_discrete_sequence=['#1f77b4'])
                    st.plotly_chart(fig_eff, use_container_width=True)

        with at7:
            st.subheader("🧬 Biological Recomp & Recovery")
            
            if not health_latest.empty:
                hdf = health_latest[(health_latest['FFMI'] > 0) & (health_latest['Body_Fat_Pct'] > 0)].copy()
                if not hdf.empty:
                    fig_ffmi = go.Figure()
                    fig_ffmi.add_trace(go.Scatter(x=hdf['Date'], y=hdf['FFMI'], mode='lines+markers', name='FFMI', line=dict(color='#00CC96', width=3), yaxis='y1'))
                    fig_ffmi.add_trace(go.Scatter(x=hdf['Date'], y=hdf['Body_Fat_Pct'], mode='lines', name='Body Fat %', line=dict(color='#FF4B4B', dash='dot'), yaxis='y2'))
                    fig_ffmi.update_layout(yaxis=dict(title='FFMI Score', side='left'), yaxis2=dict(title='Body Fat %', side='right', overlaying='y', showgrid=False))
                    fig_ffmi.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig_ffmi, use_container_width=True)
                else:
                    st.info("📊 Log your Body Fat % in the Bio Data tab to unlock the FFMI Recomp Chart.")
            else:
                st.info("📊 Log your Body Fat % in the Bio Data tab to unlock the FFMI Recomp Chart.")
            
            if not lift_df.empty and 'Sleep_Score' in lift_df.columns:
                rc_ex = st.selectbox("Compare Sleep vs Strength", lift_df['Exercise'].unique())
                rc_df = lift_df[(lift_df['Exercise'] == rc_ex) & (lift_df['Sleep_Score'] > 0)].groupby('Date').agg({'Epley_1RM': 'max', 'Sleep_Score': 'max'}).reset_index()
                if not rc_df.empty:
                    fig_sleep = px.scatter(rc_df, x='Sleep_Score', y='Epley_1RM', title=f"Sleep vs. {rc_ex} e1RM", color='Sleep_Score', color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_sleep, use_container_width=True)
                else:
                    st.info(f"💤 Awaiting linked Sleep Data for {rc_ex}.")
            else:
                st.info("💤 Awaiting strength data to compare against sleep scores.")
                    
            st.write("---")
            st.markdown("### ⚡ CNS Autonomic Balance (HRV Trends)")
            st.write("If your 7-Day HRV (Green) dips significantly below your 30-Day baseline (Red), your CNS is under-recovered. Take a rest day.")
            
            if not df_health.empty and 'HRV' in df_health.columns and df_health['HRV'].sum() > 0:
                hrv_df = df_health[df_health['HRV'] > 0][['Date', 'HRV']].copy().set_index('Date').resample('D').mean().ffill()
                hrv_df['7D_Avg'] = hrv_df['HRV'].rolling(window=7, min_periods=1).mean()
                hrv_df['30D_Avg'] = hrv_df['HRV'].rolling(window=30, min_periods=1).mean()
                fig_hrv = go.Figure()
                fig_hrv.add_trace(go.Scatter(x=hrv_df.index, y=hrv_df['HRV'], mode='markers', name='Daily HRV', marker=dict(color='gray', opacity=0.4)))
                fig_hrv.add_trace(go.Scatter(x=hrv_df.index, y=hrv_df['7D_Avg'], mode='lines', name='7-Day Trend', line=dict(color='#00CC96', width=3)))
                fig_hrv.add_trace(go.Scatter(x=hrv_df.index, y=hrv_df['30D_Avg'], mode='lines', name='30-Day Baseline', line=dict(color='#FF4B4B', dash='dash')))
                fig_hrv.update_layout(yaxis_title="Heart Rate Variability (ms)")
                st.plotly_chart(fig_hrv, use_container_width=True)
            else:
                st.info("❤️‍🔥 Log your daily HRV in the Bio Data tab to unlock Autonomic Balance tracking.")

with tab_overview:
    st.subheader("📋 Program Overview & Documentation")
    st.write("Easily copy this page to share your exact programming, logic, and execution cues with a coach or training partner.")
    st.write("---")
    for day, blocks in PROGRAM.items():
        if "Freestyle" in day or "Life Event" in day: continue
        st.markdown(f"## {day}")
        philosophy = DAY_PHILOSOPHY.get(day, "")
        if philosophy: st.info(f"**🧠 Programming Philosophy:** {philosophy}")
        warm_up = WARM_UPS.get(day, "")
        cool_down = COOL_DOWNS.get(day, "")
        if warm_up: st.markdown(f"**🔥 Warm-Up Protocol:** {warm_up}")
        if cool_down: st.markdown(f"**🧊 Down-Regulation (Post-Workout):** {cool_down}")
        combined_text_t5 = warm_up + cool_down
        rel_mob_t5 = {k: v for k, v in MOBILITY_GUIDES.items() if k.lower() in combined_text_t5.lower()}
        if rel_mob_t5:
            st.markdown("**📖 Mobility Execution Cues:**")
            for m_name, m_guide in rel_mob_t5.items(): st.markdown(f"- *{m_name}:* {m_guide}")
        st.write("") 
        for block_name, exercises in blocks.items():
            st.markdown(f"#### {block_name}")
            
            # --- REST PROTOCOL OVERVIEW ---
            rest_flow = REST_PROTOCOLS.get(day, {}).get(block_name, "")
            if rest_flow:
                st.info(f"⏱️ **Execution Flow:** {rest_flow}")
                
            for ex in exercises:
                target = REP_TARGETS.get(ex, "Sets x Reps")
                guide = EXERCISE_GUIDES.get(ex, {})
                st.markdown(f"- **{ex}** *(Target: {target})*")
                if guide:
                    st.markdown(f"  - *Setup:* {guide.get('Setup', '')}")
                    st.markdown(f"  - *Execution:* {guide.get('Execution', '')}")
                    st.markdown(f"  - *Why:* {guide.get('Why', '')}")
        st.write("---")

with tab_db:
    st.subheader("⚙️ Database Editor")
    
    st.markdown("### 🏋️‍♂️ Lifts Database")
    edited_lifts = st.data_editor(df_lifts.drop(columns=['Volume', 'Epley_1RM', 'Effective_Weight'], errors='ignore'), num_rows="dynamic", width="stretch")
    if st.button("Save Changes to Lifts DB", type="primary"):
        overwrite_sheet(ws_lifts, edited_lifts, LIFTS_COLS)
        st.success("Lifts Database Saved!")
        
    st.write("---")
    st.markdown("### 🧬 Health Database")
    edited_health = st.data_editor(df_health, num_rows="dynamic", width="stretch")
    if st.button("Save Changes to Health DB", type="primary"):
        overwrite_sheet(ws_health, edited_health, HEALTH_COLS)
        st.success("Health Database Saved!")
        
    st.write("---")
    st.markdown("### 🏃‍♂️ Cardio Database")
    edited_cardio = st.data_editor(df_cardio, num_rows="dynamic", width="stretch")
    if st.button("Save Changes to Cardio DB", type="primary"):
        overwrite_sheet(ws_cardio, edited_cardio, CARDIO_COLS)
        st.success("Cardio Database Saved!")
