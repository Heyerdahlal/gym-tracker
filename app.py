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
    ws_lifts = sh.worksheet("Lifts")
    ws_health = sh.worksheet("Health")
    try:
        ws_system = sh.worksheet("System")
    except gspread.exceptions.WorksheetNotFound:
        ws_system = sh.add_worksheet(title="System", rows="10", cols="5")
except Exception as e:
    st.error(f"⚠️ **Google Connection Error:** Make sure you created the 'Lifts' and 'Health' tabs at the bottom of your Google Sheet! Error: {e}")
    st.stop()

# --- STATIC USER PROFILE ---
USER_HEIGHT = float(st.secrets.get("user_height_cm", 180.0))

# --- COLUMNS ---
LIFTS_COLS = ['Date', 'Workout_Day', 'Exercise', 'Set_Number', 'Weight', 'Band', 'Reps_or_Mins', 'Distance_km', 'Side', 'Bodyweight', 'RIR']
HEALTH_COLS = ['Date', 'Avg_HR', 'Max_HR', 'Avg_Resp', 'Z1_Mins', 'Z2_Mins', 'Z3_Mins', 'Z4_Mins', 'Z5_Mins', 'Height_cm', 'Body_Fat_Pct', 'Muscle_Mass_kg', 'Sleep_Score', 'FFMI', 'RHR', 'HRV']

# --- PROGRAM & DICTIONARIES ---
PROGRAM = {
    "Day 1: The Cardio Engine": {
        "Block 1: Rowing": ["4x4 Rowing (Zone 4/5)"],
        "Block 2: Bike": ["Zone 2 Spin Bike Flush"]
    },
    "Day 2: Upper A (Horizontal Push/Pull)": {
        "Block 1 (Superset): T-Bar Row & DB Bench": ["T-Bar Landmine Row", "Dumbbell Bench Press"],
        "Block 2 (Superset): DB Row & Push-Ups": ["Single-Arm Bench-Supported Dumbbell Row", "Push-Ups"],
        "Block 3 (Tri-Set): Triceps, Biceps & Chest": ["Overhead Tricep Extension", "Dumbbell Hammer Curls", "Banded Crossovers"],
        "Block 4 (Superset): Lateral & Rear Delts": ["Chest-Supported Lateral Raise", "Chest-Supported Rear Delt Flye"]
    },
    "Day 3: Lower A (Strength, Quads & Armor)": {
        "Block 1: Heavy Front Squat": ["Heavy Barbell Front Squat"],
        "Block 2 (Superset): Landmine Squat & Core": ["Heels-Elevated Landmine Squat", "Anchored Reverse Crunch"],
        "Block 3 (Superset): KB Swings & Nordics": ["Heavy Russian Kettlebell Swings", "Nordic Curls"],
        "Block 4 (Tri-Set): Calves, Tibs & Core": ["Squat Wedge Dumbbell Calf Raises", "Wall Tibialis Raises", "Half-Kneeling Pallof Press"]
    },
    "Day 4: Upper B (Vertical Push/Pull)": {
        "Block 1 (Superset): Pull-Ups & Dips": ["Neutral Grip Pull-Ups", "Band-Assisted Dips"],
        "Block 2 (Superset): Landmine Press & Face Pulls": ["Landmine Press", "Banded Face Pulls"],
        "Block 3 (Superset): Curls & Pushdowns": ["Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns"],
        "Block 4: Lateral Raises": ["Chest-Supported Lateral Raise"]
    },
    "Day 5: Lower B (Hinge, Power & Posterior)": {
        "Block 1: RDL": ["Romanian Deadlift (RDL)"],
        "Block 2 (Superset): Bulgarians & Rollouts": ["Bulgarian Split Squats", "Ab-Wheel Rollouts"],
        "Block 3 (Superset): Hip Thrusts & Hamstrings": ["Barbell Hip Thrusts", "Hamstring-Focused Roman Chair Extension"],
        "Block 4 (Tri-Set): Erectors, Calves & Carries": ["Erector-Focused Roman Chair Extension", "Squat Wedge Dumbbell Calf Raises", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
    },
    "Freestyle / Custom Day": {
        "Select Any Exercise(s)": [
            "Ab-Wheel Rollouts", "Anchored Reverse Crunch", "Band-Assisted Dips", "Banded Crossovers", 
            "Banded Face Pulls", "Banded Tricep Pushdowns", "Barbell Hip Thrusts", "Bulgarian Split Squats", 
            "Chest-Supported Lateral Raise", "Chest-Supported Rear Delt Flye", "Dumbbell Bench Press", 
            "Dumbbell Hammer Curls", "Erector-Focused Roman Chair Extension", "Front-Rack Kettlebell Marches", 
            "Half-Kneeling Pallof Press", "Hamstring-Focused Roman Chair Extension", "Heavy Barbell Front Squat", 
            "Heavy Russian Kettlebell Swings", "Heavy Suitcase Holds", "Heels-Elevated Landmine Squat", 
            "Incline Supinated Dumbbell Curls", "Landmine Press", "Neutral Grip Pull-Ups", "Nordic Curls", 
            "Overhead Tricep Extension", "Push-Ups", "Romanian Deadlift (RDL)", "Single-Arm Bench-Supported Dumbbell Row", 
            "Squat Wedge Dumbbell Calf Raises", "T-Bar Landmine Row", "Wall Tibialis Raises"
        ]
    },
    "🧬 Life Event (Sick/Travel)": {
        "Rest": ["Rest / Recovery / Frozen Week"]
    }
}

WARM_UPS = {
    "Day 1: The Cardio Engine": "5 mins light dynamic stretching (leg swings, arm circles) + 3 mins easy pacing to slowly build heart rate.",
    "Day 2: Upper A (Horizontal Push/Pull)": "2x15 Band Pull-aparts, 2x10 Push-up to Downward Dog (shoulder flow), 2x15 light Tricep Pushdowns (elbow blood flow).",
    "Day 3: Lower A (Strength, Quads & Armor)": "2x10 Deep Bodyweight Squats (pry the hips), 2x10 Cossack Squats, 90-sec Couch Stretch per leg, 1x20 Wall Tibialis Raises.",
    "Day 4: Upper B (Vertical Push/Pull)": "Dead hang from pull-up bar for 30-45s, 2x10 Scapular Pull-ups (activate lats), 2x15 Banded Face Pulls (rotator cuff prep).",
    "Day 5: Lower B (Hinge, Power & Posterior)": "2x15 BW Glute Bridges, 1x15 KB Goblet Squats (stay at bottom to open hips), 2x10 BW Good Mornings, 90-sec Couch Stretch."
}

DAY_PHILOSOPHY = {
    "Day 1: The Cardio Engine": "This day kicks off the week by building the aerobic base and VO2 Max. Establishing cardiovascular efficiency first improves recovery and work capacity for the heavy lifting days that follow.",
    "Day 2: Upper A (Horizontal Push/Pull)": "A heavy horizontal emphasis. Pairing pushes with pulls in supersets ensures structural balance across the shoulder joint while allowing you to accumulate dense volume efficiently.",
    "Day 3: Lower A (Strength, Quads & Armor)": "Quad-dominant strength focus. The goal here is anterior chain power (Front Squats) followed by intense core bracing and armor-building to protect the spine.",
    "Day 4: Upper B (Vertical Push/Pull)": "Vertical plane dominance. Pull-ups and overhead-angled presses (Landmine) build width and shoulder health, followed by targeted isolation for the arms and lateral delts.",
    "Day 5: Lower B (Hinge, Power & Posterior)": "Posterior chain obliteration. The RDL stretches the hamstrings under extreme load, while unilateral split squats fix imbalances. Finishes with intense erector and glute isolation."
}

REP_TARGETS = {
    "T-Bar Landmine Row": "4 Sets × 8–10 Reps", "Dumbbell Bench Press": "4 Sets × 8–10 Reps",
    "Single-Arm Bench-Supported Dumbbell Row": "3 Sets × 10–12 Reps/arm", "Push-Ups": "3 Sets × 10–15 Reps",
    "Overhead Tricep Extension": "3 Sets × 12–15 Reps", "Dumbbell Hammer Curls": "3 Sets × 10–12 Reps",
    "Banded Crossovers": "3 Sets × 15–20 Reps", "Chest-Supported Lateral Raise": "4 Sets × 15–20 Reps",
    "Chest-Supported Rear Delt Flye": "4 Sets × 15–20 Reps", "Heavy Barbell Front Squat": "3 Sets × 4–6 Reps",
    "Heels-Elevated Landmine Squat": "4 Sets × 6–8 Reps", "Bulgarian Split Squats": "4 Sets × 8–10 Reps/leg",
    "Hamstring-Focused Roman Chair Extension": "3 Sets × 12–15 Reps", "Anchored Reverse Crunch": "3 Sets × 10–12 Reps",
    "Wall Tibialis Raises": "3 Sets × 15–20 Reps", "Squat Wedge Dumbbell Calf Raises": "4 Sets × 10–12 Reps",
    "Half-Kneeling Pallof Press": "3 Sets × 10–12 Reps/side", "Neutral Grip Pull-Ups": "4 Sets × 5–8 Reps",
    "Band-Assisted Dips": "4 Sets × 10–12 Reps", "Landmine Press": "3 Sets × 8–10 Reps",
    "Banded Face Pulls": "3 Sets × 15–20 Reps", "Incline Supinated Dumbbell Curls": "4 Sets × 10–12 Reps",
    "Banded Tricep Pushdowns": "3 Sets × 15–20 Reps", "Romanian Deadlift (RDL)": "4 Sets × 6–8 Reps",
    "Heavy Russian Kettlebell Swings": "3 Sets × 12–15 Reps", "Barbell Hip Thrusts": "3 Sets × 10–12 Reps",
    "Ab-Wheel Rollouts": "3 Sets × 8–10 Reps", "Nordic Curls": "3 Sets × 5–8 Reps",
    "Erector-Focused Roman Chair Extension": "3 Sets × 8–10 Reps", "Heavy Suitcase Holds": "3 Sets × 45 Seconds/side",
    "Front-Rack Kettlebell Marches": "3 Sets × 45 Seconds/side"
}

EXERCISE_GUIDES = {
    "T-Bar Landmine Row": {"Setup": "Straddle the barbell facing away from the landmine anchor. Use a V-grip handle hooked under the bar.", "Execution": "Hinge at hips so torso is almost parallel. Row plates to your chest. Slow 3-second negative (lowering) phase.", "Why": "Stable pulling builds back thickness without the systemic lower back fatigue of a standard bent-over barbell row."},
    "Dumbbell Bench Press": {"Setup": "Set bench to a slight incline (15-30 degrees). Shoulder blades pinned down and back.", "Execution": "Lower slowly (3s) to a deep stretch. Press up, but STOP a few inches before the dumbbells touch. Do not lock out.", "Why": "A slight incline perfectly aligns with the pec fibers. Stopping before the bells touch prevents the joints from 'stacking', keeping 100% of the tension on the chest."},
    "Single-Arm Bench-Supported Dumbbell Row": {"Setup": "Hand and same-side knee on the bench. Back perfectly flat.", "Execution": "Pull the dumbbell towards your HIP, not your armpit. Pause for 1 full second at the top contraction.", "Why": "Bench support removes lower back strain. Pulling to the hip isolates the lats instead of shrugging with your upper traps."},
    "Push-Ups": {"Setup": "Hands shoulder-width, core braced tightly (hollow body).", "Execution": "Descend slowly. PAUSE for 1 second with your chest hovering 1 inch off the floor, then explode up.", "Why": "The dead-stop pause kills the stretch reflex, forcing raw pec/triceps activation. A high-rep finisher with zero joint wear."},
    "Overhead Tricep Extension": {"Setup": "Anchor band at waist height behind you (or step on it). Grab band, face away, and bring hands behind head with elbows pointing up.", "Execution": "Press the band straight up to the ceiling. Control the descent back into a deep stretch.", "Why": "Bands provide an 'ascending resistance curve', meaning tension increases at the lockout where the triceps are mechanically strongest, while keeping constant tension in the stretch."},
    "Dumbbell Hammer Curls": {"Setup": "Standing, neutral grip (palms facing each other).", "Execution": "Squeeze up cleanly, then a strict 2-second negative. Zero swinging or momentum.", "Why": "Targets the brachialis and brachioradialis. This pushes the bicep up (creating a larger peak) and prevents elbow tendonitis."},
    "Banded Crossovers": {"Setup": "Anchor bands HIGH (above head). Step forward to create tension.", "Execution": "Pull down and across your body (high-to-low). Squeeze for 2 full seconds at the bottom contraction where your hands overlap.", "Why": "The high-to-low angle perfectly targets the lower/sternocostal pec fibers, brilliantly complementing the upper-pec focus of your incline DB presses."},
    "Chest-Supported Lateral Raise": {"Setup": "Chest flat against a steep incline bench.", "Execution": "Lead with the elbows, sweeping the dumbbells OUT, not just up. Stop at shoulder height.", "Why": "Strict isolation of the lateral delt. The bench prevents you from using lumbar extension (leaning back) to cheat the weight."},
    "Chest-Supported Rear Delt Flye": {"Setup": "Chest on incline bench, palms facing down or neutral.", "Execution": "Sweep arms out to the side. Stop when elbows align with shoulders (do NOT pinch your shoulder blades together).", "Why": "Stopping before the shoulder blades retract ensures the load stays 100% on the rear deltoid, not the rhomboids or traps."},
    "Heavy Barbell Front Squat": {"Setup": "Clean grip or cross-arm grip. Bar resting deep on the meaty part of the front delts.", "Execution": "Deep, upright squat. Drive your elbows UP violently as you come out of the hole to prevent your chest from collapsing.", "Why": "Forces an upright torso, shifting the load intensely onto the quads and off the lumbar spine."},
    "Heels-Elevated Landmine Squat": {"Setup": "Place a squat wedge under your heels. Hold the thick part of the barbell sleeve at upper-chest level.", "Execution": "Perform 1.5 reps: Drop into a deep squat, rise halfway up, drop back into the deep squat, then stand up. That is ONE rep.", "Why": "Maximizes quad stretch while the 1.5 rep method creates immense time under tension without needing heavy, spine-crushing weights."},
    "Anchored Reverse Crunch": {"Setup": "Lying on your back, gripping a heavy kettlebell or pole behind your head.", "Execution": "Roll your pelvis UP towards your sternum. Control the descent (3 seconds) until your tailbone gently touches the floor.", "Why": "Flexes the spine against resistance (true abdominal function) rather than just working the hip flexors like standard leg raises."},
    "Heavy Russian Kettlebell Swings": {"Setup": "Hinge position, KB slightly in front of you.", "Execution": "Hike it back between your legs, then snap your hips forward violently. Your arms are just ropes. Stop at chest height.", "Why": "Builds explosive posterior chain power, hamstring resilience, and glute lockout strength."},
    "Nordic Curls": {"Setup": "Kneeling, ankles secured under a bar or by a partner.", "Execution": "Squeeze glutes to lock hips. Fall forward as slowly as humanly possible (eccentric focus). Catch yourself, push back up.", "Why": "The ultimate hamstring bulletproofing exercise. Lengthens the muscle fascicles, drastically reducing the risk of a hamstring tear."},
    "Squat Wedge Dumbbell Calf Raises": {"Setup": "Toes elevated on a wedge, holding heavy dumbbells.", "Execution": "PAUSE for 2 full seconds at the absolute bottom stretch. Explode up, pause 1 second at the top.", "Why": "The Achilles tendon is a massive spring. The bottom pause kills the spring energy, forcing the actual calf muscle to do 100% of the lifting."},
    "Wall Tibialis Raises": {"Setup": "Lean back against a wall, feet placed out in front of you.", "Execution": "Pull toes up towards your shins as hard as possible. Hold for 1 second.", "Why": "Bulletproofs the knees. The tibialis anterior decelerates the foot; strengthening it prevents shin splints and patellar pain."},
    "Half-Kneeling Pallof Press": {"Setup": "Half-kneeling, band anchored to your side at chest height.", "Execution": "Press the band straight out in front of you. Hold for 2 seconds, violently resisting the urge to twist.", "Why": "Elite anti-rotation core training. Protects the spine by teaching the deep core to brace against twisting forces."},
    "Neutral Grip Pull-Ups": {"Setup": "Palms facing each other.", "Execution": "Start from a dead hang. Pull your upper chest to the bar. Control the eccentric (lowering) phase.", "Why": "The neutral grip is highly shoulder-friendly and gives the lats a massive mechanical advantage for growth."},
    "Band-Assisted Dips": {"Setup": "Band looped over the bars and under your knees.", "Execution": "Slight forward lean to bias the chest. Descend until you feel a deep stretch in the pecs.", "Why": "The band provides help at the bottom (the most vulnerable shoulder position) forcing a strict, deep, hypertrophy-focused rep."},
    "Landmine Press": {"Setup": "Half-kneeling or standing. Hold the barbell sleeve at shoulder height.", "Execution": "Press up and slightly forward, following the natural arc of the barbell.", "Why": "The arcing path is incredibly healthy and natural for the shoulder capsule compared to a strict vertical barbell press."},
    "Banded Face Pulls": {"Setup": "Band anchored at eye level.", "Execution": "Pull the band towards your nose, pulling your hands APART and rotating your knuckles UP (external rotation) at the end.", "Why": "The ultimate posture corrector. Hits the rear delts, rhomboids, and bulletproofs the rotator cuff."},
    "Incline Supinated Dumbbell Curls": {"Setup": "Bench at 45-60 degrees. Let arms hang straight down behind your torso. Palms facing forward.", "Execution": "Keep elbows pinned back. Curl up, squeezing the biceps.", "Why": "Puts the bicep in an extreme stretched position (long head focus), triggering massive hypertrophy with lighter weights."},
    "Banded Tricep Pushdowns": {"Setup": "Band anchored high above you.", "Execution": "Keep elbows pinned to your sides. Push down and pull the band APART at the very bottom.", "Why": "Band resistance increases at peak contraction, matching the strength curve of the triceps perfectly."},
    "Romanian Deadlift (RDL)": {"Setup": "Stand inside the Hex/Trap bar. Feet shoulder-width. Unlock knees slightly and freeze them at that angle.", "Execution": "Push hips straight back toward the wall behind you. Stop and reverse the motion the moment your hamstrings are fully stretched.", "Why": "The Hex Bar aligns the center of gravity with your midline, providing a brutal hamstring/glute stretch while drastically reducing shear force on the lumbar spine."},
    "Bulgarian Split Squats": {"Setup": "Rear foot elevated on a bench. Hold dumbbells at your sides.", "Execution": "Drop your back knee straight down. Lean torso slightly forward to bias glutes, or stay upright to bias quads.", "Why": "Eliminates left/right strength imbalances and provides an extreme muscle stretch under load with zero spinal compression."},
    "Ab-Wheel Rollouts": {"Setup": "Kneeling. Squeeze glutes to lock your pelvis into a posterior tilt.", "Execution": "Roll out until your torso is parallel to the floor. Pull back using your ABS, not by pushing your hips back.", "Why": "Extreme anti-extension core strength. Forces the rectus abdominis to stabilize the spine under intense load."},
    "Barbell Hip Thrusts": {"Setup": "Upper back resting on a bench, heavy barbell padded across your hips.", "Execution": "Drive through the heels. Give a brutal 2-second squeeze at the top. Keep your chin tucked to your chest.", "Why": "The highest glute activation of any exercise in existence, completely bypassing the lower back."},
    "Hamstring-Focused Roman Chair Extension": {"Setup": "Lock into a 45-degree hyperextension bench. Pad sits BELOW the hips (upper thigh).", "Execution": "Keep your back perfectly flat and rigid. Hinge down, then pull up using only the hamstrings and glutes.", "Why": "Provides a fantastic, loaded stretch for the hamstrings without axial loading on the spine."},
    "Erector-Focused Roman Chair Extension": {"Setup": "Lock into a 45-degree bench. Pad sits AT the hips.", "Execution": "Allow your upper back to round over the pad (spinal flexion), then pull up by extending the spine (unrolling vertebra by vertebra).", "Why": "Directly trains the spinal erectors through a full range of motion, building a thick, resilient lower back."},
    "Heavy Suitcase Holds": {"Setup": "Hold a heavy kettlebell or dumbbell in one hand. Stand perfectly tall.", "Execution": "Perform a slow, highly controlled march in place. Do not let the weight pull your shoulder down or shift your hips.", "Why": "Marching upgrades this from an anti-lateral flexion core exercise to a dynamic pelvic stabilizer, bulletproofing the glute medius and preventing hip drop."},
    "Front-Rack Kettlebell Marches": {"Setup": "Two heavy KBs held at the chest (rack position).", "Execution": "Slowly march in place, lifting your knees above hip level with immense control.", "Why": "Heavy core stabilization under load. The rack position forces the upper back and core to work isometrically to keep you upright."}
}

MUSCLE_MAP = {
    "T-Bar Landmine Row": {"Back": 1.0, "Biceps": 0.5}, "Dumbbell Bench Press": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5},
    "Single-Arm Bench-Supported Dumbbell Row": {"Back": 1.0, "Biceps": 0.5}, "Push-Ups": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5},
    "Overhead Tricep Extension": {"Triceps": 1.0}, "Dumbbell Hammer Curls": {"Biceps": 1.0},
    "Banded Crossovers": {"Chest": 1.0, "Shoulders": 0.5}, "Chest-Supported Lateral Raise": {"Shoulders": 1.0},
    "Chest-Supported Rear Delt Flye": {"Shoulders": 1.0, "Back": 0.5}, "Heavy Barbell Front Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5}, "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Hamstring-Focused Roman Chair Extension": {"Hamstrings": 1.0, "Glutes": 0.5}, "Anchored Reverse Crunch": {"Abs": 1.0},
    "Wall Tibialis Raises": {"Calves": 1.0}, "Squat Wedge Dumbbell Calf Raises": {"Calves": 1.0},
    "Half-Kneeling Pallof Press": {"Abs": 1.0}, "Neutral Grip Pull-Ups": {"Back": 1.0, "Biceps": 0.5},
    "Band-Assisted Dips": {"Chest": 1.0, "Triceps": 1.0, "Shoulders": 0.5}, "Landmine Press": {"Shoulders": 1.0, "Chest": 0.5, "Triceps": 0.5},
    "Banded Face Pulls": {"Shoulders": 1.0, "Back": 0.5}, "Incline Supinated Dumbbell Curls": {"Biceps": 1.0},
    "Banded Tricep Pushdowns": {"Triceps": 1.0}, "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0},
    "Heavy Russian Kettlebell Swings": {"Glutes": 1.0, "Hamstrings": 0.5}, "Barbell Hip Thrusts": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Ab-Wheel Rollouts": {"Abs": 1.0}, "Nordic Curls": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Erector-Focused Roman Chair Extension": {"Back": 1.0, "Glutes": 0.5}, "Heavy Suitcase Holds": {"Abs": 1.0},
    "Front-Rack Kettlebell Marches": {"Abs": 1.0, "Quads": 0.5}
}

BW_MULTIPLIERS = {
    "Neutral Grip Pull-Ups": 0.95, "Band-Assisted Dips": 0.95, "Push-Ups": 0.65, 
    "Nordic Curls": 0.60, "Anchored Reverse Crunch": 0.40, "Ab-Wheel Rollouts": 0.50,
    "Squat Wedge Dumbbell Calf Raises": 1.0, "Bulgarian Split Squats": 0.85, 
    "Erector-Focused Roman Chair Extension": 0.50, "Glute-Focused Roman Chair Extension": 0.50,
    "Hamstring-Focused Roman Chair Extension": 0.50, "Heavy Barbell Front Squat": 0.85,
    "Wall Tibialis Raises": 0.30
}

BAND_SUBTRACTIONS = {
    "None": 0.0, "Yellow (13.6kg)": 13.6, "Red (22.6kg)": 22.6, 
    "Black (36.3kg)": 36.3, "Purple (45.4kg)": 45.4, 
    "Green (68.0kg)": 68.0, "Blue (88.5kg)": 88.5, "Orange (113.4kg)": 113.4
}

UNILATERAL_EXERCISES = ["Bulgarian Split Squats", "Single-Arm Bench-Supported Dumbbell Row", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Front-Rack Kettlebell Marches"]
HEAVY_COMPOUNDS = ["Heavy Barbell Front Squat", "Romanian Deadlift (RDL)", "Dumbbell Bench Press", "T-Bar Landmine Row", "Landmine Press"]

def get_target_reps_and_sets(exercise_name):
    target_str = REP_TARGETS.get(exercise_name, "")
    sets_match = re.search(r'(\d+)\s*Sets', target_str, re.IGNORECASE)
    reps_match = re.search(r'–(\d+)\s*Reps', target_str, re.IGNORECASE)
    target_sets = int(sets_match.group(1)) if sets_match else 3
    top_rep = int(reps_match.group(1)) if reps_match else 8
    return target_sets, top_rep

@st.cache_data(ttl=600)
def load_data():
    try: l_recs = ws_lifts.get_all_records()
    except Exception: l_recs = []
        
    df_lifts = pd.DataFrame(l_recs) if l_recs else pd.DataFrame(columns=LIFTS_COLS)
    for col in LIFTS_COLS:
        if col not in df_lifts.columns:
            df_lifts[col] = 0.0 if col not in ['Date', 'Workout_Day', 'Exercise', 'Band', 'Side'] else ""
    
    try: h_recs = ws_health.get_all_records()
    except Exception: h_recs = []
        
    df_health = pd.DataFrame(h_recs) if h_recs else pd.DataFrame(columns=HEALTH_COLS)
    for col in HEALTH_COLS:
        if col not in df_health.columns:
            df_health[col] = 0.0 if col != 'Date' else ""

    num_cols_lifts = ['Distance_km', 'Weight', 'Set_Number', 'Reps_or_Mins', 'Bodyweight', 'RIR']
    for col in num_cols_lifts: df_lifts[col] = pd.to_numeric(df_lifts[col], errors='coerce').fillna(0)
        
    df_lifts['Side'] = df_lifts['Side'].replace('', 'Both').fillna('Both')
    df_lifts['Date'] = pd.to_datetime(df_lifts['Date'], errors='coerce')
    
    ASSISTED_EXERCISES = ["Neutral Grip Pull-Ups", "Band-Assisted Dips"]
    RESISTED_EXERCISES = ["Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
    
    def calc_effective_weight(row):
        ex = row['Exercise']
        bw_mod = BW_MULTIPLIERS.get(ex, 0.0)
        base_body_load = row['Bodyweight'] * bw_mod
        peak_band_force = BAND_SUBTRACTIONS.get(row.get('Band', 'None'), 0.0)
        avg_band_force = peak_band_force * 0.5
        
        if ex in ASSISTED_EXERCISES: eff_wt = row['Weight'] + base_body_load - avg_band_force
        elif ex in RESISTED_EXERCISES: eff_wt = row['Weight'] + base_body_load + avg_band_force
        else: eff_wt = row['Weight'] + base_body_load
            
        return max(eff_wt, 0.0) 
        
    df_lifts['Effective_Weight'] = df_lifts.apply(calc_effective_weight, axis=1) if not df_lifts.empty else 0.0
    is_lift = ~df_lifts['Exercise'].str.contains("Rowing|Bike|Rest", na=False)
    df_lifts['Volume'] = 0.0
    df_lifts['Epley_1RM'] = 0.0
    
    if not df_lifts.empty:
        df_lifts.loc[is_lift, 'Volume'] = df_lifts.loc[is_lift, 'Effective_Weight'] * df_lifts.loc[is_lift, 'Reps_or_Mins']
        df_lifts.loc[is_lift, 'Epley_1RM'] = df_lifts.loc[is_lift, 'Effective_Weight'] * (1 + df_lifts.loc[is_lift, 'Reps_or_Mins'] / 30)
    
    df_health['Date'] = pd.to_datetime(df_health['Date'], errors='coerce')
    num_cols_health = [c for c in HEALTH_COLS if c != 'Date']
    for col in num_cols_health: df_health[col] = pd.to_numeric(df_health[col], errors='coerce').fillna(0)
        
    return df_lifts, df_health

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
    
    ws.clear()
    ws.update(values=[df_to_save.columns.values.tolist()] + df_to_save.values.tolist(), range_name="A1")
    st.cache_data.clear()

df_lifts, df_health = load_data()

def get_latest_nonzero(col_name, default_val):
    if not df_health.empty and col_name in df_health.columns:
        valid_data = df_health[df_health[col_name] > 0]
        if not valid_data.empty: return float(valid_data.sort_values('Date').iloc[-1][col_name])
    return default_val

last_w = get_latest_nonzero('Bodyweight', 80.0) 
if df_lifts is not None and not df_lifts.empty and 'Bodyweight' in df_lifts.columns:
    valid_bw = df_lifts[df_lifts['Bodyweight'] > 0]
    if not valid_bw.empty: last_w = float(valid_bw.sort_values('Date').iloc[-1]['Bodyweight'])

if 'g_dur' not in st.session_state: st.session_state.update({'g_dur': 60.0, 'g_dist': 10.0, 'g_avg_hr': 130.0, 'g_max_hr': 165.0})
if 'h_weight' not in st.session_state: st.session_state['h_weight'] = last_w
if 'h_bf' not in st.session_state: st.session_state['h_bf'] = get_latest_nonzero('Body_Fat_Pct', 15.0)
if 'h_muscle' not in st.session_state: st.session_state['h_muscle'] = get_latest_nonzero('Muscle_Mass_kg', 35.0)
if 'h_sleep' not in st.session_state: st.session_state['h_sleep'] = int(get_latest_nonzero('Sleep_Score', 80))
if 'h_rhr' not in st.session_state: st.session_state['h_rhr'] = int(get_latest_nonzero('RHR', 50))
if 'h_hrv' not in st.session_state: st.session_state['h_hrv'] = int(get_latest_nonzero('HRV', 60))

st.title("🔬 Sports Science Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Data Collection", "📊 Analytics Engine", "⚙️ Database", "📡 Garmin Hub", "📋 Program Overview"])

with tab1:
    col1, col2 = st.columns([1, 2])
    
    with col1:
        date_input = st.date_input("Date", date.today())
        is_deload = st.toggle("🧘 Activate Deload Week")
        
    with col2:
        workout_day = st.selectbox("Select Workout Day", list(PROGRAM.keys()))
        workout_block = st.selectbox("Select Workout Block", list(PROGRAM[workout_day].keys()))
        
        if "Freestyle" in workout_day:
            selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day][workout_block], default=[])
        else:
            selected_exercises = st.multiselect("Select Exercise(s)", PROGRAM[workout_day][workout_block], default=PROGRAM[workout_day][workout_block])
            
        if workout_day in WARM_UPS:
            st.info(f"🔥 **Prep & Activation:** {WARM_UPS[workout_day]}")
    
    st.write("---")
    
    if selected_exercises:
        is_cardio = "Cardio" in workout_day
        
        if is_cardio:
            st.info("🏃‍♂️ **Cardio Day Selected.** Head over to the **📡 Garmin Hub (Tab 4)** to sync your watch or log cardio data manually!")

        else:
            default_sets, _ = get_target_reps_and_sets(selected_exercises[0])
            if is_deload: default_sets = max(1, default_sets - 1)
            
            num_sets = st.number_input("🎯 Total Rounds (Sets) to perform:", min_value=1, max_value=10, value=default_sets, step=1)
            st.write("---")
            st.markdown("#### 🧠 Today's Mission Control")
            default_vals = {}
            
            for exercise in selected_exercises:
                ex_df = df_lifts[(df_lifts['Exercise'] == exercise) & (df_lifts['Reps_or_Mins'] > 0)].sort_values(by=['Date', 'Set_Number'])
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
                        
                        target_sets, top_rep = get_target_reps_and_sets(exercise)
                        band_str = f" [{last_band} Band]" if last_band != "None" else ""
                        
                        if is_deload:
                            calc_w = max(0.0, last_weight * 0.8)
                            calc_w = round(calc_w / 2.5) * 2.5 
                            default_vals[exercise] = {'w': calc_w, 'r': last_reps, 'b': last_band}
                            st.info(f"🧘 **DELOAD:** **{exercise}** ➔ Drop weight to {calc_w}kg.")
                            continue
                            
                        default_vals[exercise] = {'w': last_weight, 'r': last_reps, 'b': last_band}
                        if last_reps >= top_rep: st.success(f"🚀 **INCREASE WEIGHT:** **{exercise}** hit {last_reps} reps @ {last_weight}kg{band_str}.")
                        else: st.warning(f"🎯 **HOLD WEIGHT:** **{exercise}** hit {last_reps} reps @ {last_weight}kg{band_str}. Chase {top_rep} reps today.")
                        
                        if exercise in HEAVY_COMPOUNDS and last_weight >= 20.0:
                            with st.expander(f"🔥 Warm-Up Protocol: {exercise}", expanded=False):
                                w1 = 20.0 if "Barbell" in exercise or "RDL" in exercise else max(5.0, round((last_weight*0.3)/2.5)*2.5)
                                w2 = round((last_weight * 0.5) / 2.5) * 2.5
                                w3 = round((last_weight * 0.8) / 2.5) * 2.5
                                st.markdown(f"- **Set 1:** {w1}kg × 8-10 reps\n- **Set 2:** {w2}kg × 5 reps\n- **Set 3:** {w3}kg × 2-3 reps")

                        guide = EXERCISE_GUIDES.get(exercise)
                        if guide:
                            with st.expander(f"📖 Form & Setup: {exercise}", expanded=False):
                                st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")

                        min_reps_last_session = last_session['Reps_or_Mins'].min()
                        if min_reps_last_session < 5: st.error(f"⚠️ **FATIGUE ALERT:** You dropped to {int(min_reps_last_session)} reps last week. Drop weight by 10% for Sets 2 & 3.")
                        if len(dates) >= 4:
                            recent_history = ex_df[(ex_df['Date'].isin(dates[-4:])) & (ex_df['Set_Number'] == 1)]
                            if len(recent_history) == 4 and recent_history['Weight'].nunique() == 1 and recent_history['Reps_or_Mins'].nunique() == 1:
                                st.error(f"🛑 **PLATEAU:** Stuck at {last_weight}kg for {last_reps} reps for 4 sessions. Time to progress or swap.")
                    else:
                        st.info(f"**{exercise}:** No Set 1 data found. Establish baseline!")
                        default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None"}
                        guide = EXERCISE_GUIDES.get(exercise)
                        if guide:
                            with st.expander(f"📖 Form & Setup: {exercise}", expanded=False): st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")
                else:
                    st.info(f"**{exercise}:** Establish your baseline today!")
                    default_vals[exercise] = {'w': 0.0, 'r': 0, 'b': "None"}
                    guide = EXERCISE_GUIDES.get(exercise)
                    if guide:
                        with st.expander(f"📖 Form & Setup: {exercise}", expanded=False): st.markdown(f"**Setup:** {guide.get('Setup', '')}\n**Execution:** {guide.get('Execution', '')}\n**Why:** {guide.get('Why', '')}")
            
            st.write("---")
            with st.form("lifting_form", clear_on_submit=True):
                weights, reps, reps_l, reps_r, rirs, bands = {}, {}, {}, {}, {}, {}
                for i in range(1, num_sets + 1):
                    st.markdown(f"#### 🔁 Round {i}")
                    for exercise in selected_exercises:
                        is_uni = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
                        _, top_rep = get_target_reps_and_sets(exercise)
                        st.markdown(f"**{exercise}** *(Target: {top_rep} reps)*")
                        
                        def_w = float(default_vals.get(exercise, {}).get('w', 0.0))
                        def_b = default_vals.get(exercise, {}).get('b', "None")
                        b_idx = list(BAND_SUBTRACTIONS.keys()).index(def_b) if def_b in BAND_SUBTRACTIONS else 0
                        key = f"{exercise}_{i}" 
                        
                        if uses_band:
                            c1, c2, c3, c4 = st.columns([1, 1, 1.5, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, value=def_w, key=f"w_{key}")
                            if is_uni:
                                sc1, sc2 = c2.columns(2)
                                reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                                reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                            else: reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            bands[key] = c3.selectbox("Band", list(BAND_SUBTRACTIONS.keys()), index=b_idx, key=f"b_{key}")
                            rirs[key] = c4.slider("RIR", 0, 5, 2, 1, key=f"rir_{key}")
                        else:
                            c1, c2, c3 = st.columns([1, 1, 2])
                            weights[key] = c1.number_input("Kg", min_value=0.0, step=2.5, value=def_w, key=f"w_{key}")
                            if is_uni:
                                sc1, sc2 = c2.columns(2)
                                reps_l[key] = sc1.number_input("L", min_value=0, step=1, key=f"rl_{key}")
                                reps_r[key] = sc2.number_input("R", min_value=0, step=1, key=f"rr_{key}")
                            else: reps[key] = c2.number_input("Reps", min_value=0, step=1, key=f"r_{key}")
                            rirs[key] = c3.slider("RIR", 0, 5, 2, 1, key=f"rir_{key}")
                    st.write("---") 
                
                if st.form_submit_button("Save Workouts To Database", type="primary"):
                    new_rows = []
                    for exercise in selected_exercises:
                        is_uni = exercise in UNILATERAL_EXERCISES
                        uses_band = exercise in ["Neutral Grip Pull-Ups", "Band-Assisted Dips", "Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
                        for i in range(1, num_sets + 1):
                            key = f"{exercise}_{i}"
                            b_val = bands[key] if uses_band else "None"
                            if (is_uni and (reps_l[key] > 0 or reps_r[key] > 0)) or (not is_uni and reps[key] > 0):
                                base_data = {'Date': date_input, 'Workout_Day': workout_day, 'Exercise': exercise, 'Set_Number': i, 'Weight': weights[key], 'Band': b_val, 'Distance_km': 0.0, 'Bodyweight': st.session_state['h_weight'], 'RIR': rirs[key]}
                                if is_uni:
                                    if reps_l[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_l[key], 'Side': 'Left'})
                                    if reps_r[key] > 0: new_rows.append({**base_data, 'Reps_or_Mins': reps_r[key], 'Side': 'Right'})
                                else: new_rows.append({**base_data, 'Reps_or_Mins': reps[key], 'Side': 'Both'})
                    if new_rows:
                        save_to_sheet(ws_lifts, pd.DataFrame(new_rows), LIFTS_COLS)
                        st.success(f"✅ Logged {len(new_rows)} sets to the Lifts database!")
                    else: st.warning("No reps logged.")

with tab4:
    st.subheader("📡 Garmin Integration Hub")
    st.write("Manage all biological and cardio data here. This saves directly to your **Health** database tab.")
    
    mfa_input = st.text_input("MFA Code (Leave blank if 2FA is disabled)", max_chars=6)
    
    def get_garmin_client():
        if 'garmin_vip_client' in st.session_state: return st.session_state['garmin_vip_client']
        g_email, g_pass = st.secrets.get("garmin_email"), st.secrets.get("garmin_password")
        if not g_email or not g_pass: return None
        
        client = Garmin(g_email, g_pass, prompt_mfa=lambda: mfa_input) if mfa_input else Garmin(g_email, g_pass)
        
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
            if "429" in str(e): st.error("🛑 **Garmin Timeout (429):** Please wait 15 minutes before clicking Sync again.")
            elif "prompt_mfa" in str(e): st.error("🛑 **Garmin requires 2FA!** Type the code and click sync. (Should only happen once!)")
            else: st.error(f"Garmin Login Failed: {e}")
            return None

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🧬 Morning Health Sync")
        if st.button("🔄 Sync Scale & Sleep (Auto-Save)"):
            with st.spinner(f"Pulling data for {date_input}..."):
                client = get_garmin_client()
                if client:
                    target_iso = date_input.isoformat()
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
                    health_data = {'Date': date_input, 'Avg_HR': 0, 'Max_HR': 0, 'Avg_Resp': 0, 'Z1_Mins': 0, 'Z2_Mins': 0, 'Z3_Mins': 0, 'Z4_Mins': 0, 'Z5_Mins': 0, 'Height_cm': USER_HEIGHT, 'Body_Fat_Pct': st.session_state['h_bf'], 'Muscle_Mass_kg': st.session_state['h_muscle'], 'Sleep_Score': st.session_state['h_sleep'], 'FFMI': ffmi, 'RHR': st.session_state['h_rhr'], 'HRV': st.session_state['h_hrv']}
                    save_to_sheet(ws_health, pd.DataFrame([health_data]), HEALTH_COLS)
                    st.success(f"✅ Health data locked into Google Sheets for {date_input}! Safe to close app.")

        st.markdown("**Current Session Health Data:**")
        st.session_state['h_weight'] = st.number_input("Weight (kg)", value=st.session_state['h_weight'], step=0.1)
        st.session_state['h_bf'] = st.number_input("Body Fat (%)", value=st.session_state['h_bf'], step=0.1)
        st.session_state['h_muscle'] = st.number_input("Muscle (kg)", value=st.session_state['h_muscle'], step=0.1)
        st.session_state['h_sleep'] = st.number_input("Sleep Score (0-100)", value=st.session_state['h_sleep'], step=1)
        st.session_state['h_rhr'] = st.number_input("Resting HR (bpm)", value=st.session_state['h_rhr'], step=1)
        st.session_state['h_hrv'] = st.number_input("HRV (ms)", value=st.session_state['h_hrv'], step=1)
        
    with c2:
        st.markdown("#### 🏃‍♂️ Cardio Session Data")
        if st.button("🔄 Sync Latest Cardio"):
            with st.spinner("Connecting..."):
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
                            st.success(f"Synced: {act.get('activityName', 'Unknown')}")
                            st.rerun()
                    except Exception as e: st.error(f"Activity Sync Failed: {e}")

        with st.form("cardio_form", clear_on_submit=True):
            c_ex = st.selectbox("Select Cardio Type", ["4x4 Rowing (Zone 4/5)", "Zone 2 Spin Bike Flush"])
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
                cardio_lift = {'Date': date_input, 'Workout_Day': "Day 1: The Cardio Engine", 'Exercise': c_ex, 'Set_Number': 1, 'Weight': 0.0, 'Band': 'None', 'Distance_km': distance, 'Reps_or_Mins': duration, 'Bodyweight': st.session_state['h_weight'], 'RIR': 0.0, 'Side': 'Both'}
                save_to_sheet(ws_lifts, pd.DataFrame([cardio_lift]), LIFTS_COLS)
                
                lean_mass = st.session_state['h_weight'] * (1 - (st.session_state['h_bf'] / 100))
                ffmi = lean_mass / ((USER_HEIGHT / 100) ** 2) if USER_HEIGHT > 0 else 0
                cardio_health = {'Date': date_input, 'Avg_HR': avg_hr, 'Max_HR': max_hr, 'Avg_Resp': avg_resp, 'Z1_Mins': z1, 'Z2_Mins': z2, 'Z3_Mins': z3, 'Z4_Mins': z4, 'Z5_Mins': z5, 'Height_cm': USER_HEIGHT, 'Body_Fat_Pct': st.session_state['h_bf'], 'Muscle_Mass_kg': st.session_state['h_muscle'], 'Sleep_Score': st.session_state['h_sleep'], 'FFMI': ffmi, 'RHR': st.session_state['h_rhr'], 'HRV': st.session_state['h_hrv']}
                save_to_sheet(ws_health, pd.DataFrame([cardio_health]), HEALTH_COLS)
                st.success("✅ Cardio Data saved perfectly!")

with tab2:
    if df_lifts.empty and df_health.empty:
        st.info("Awaiting Data...")
    else:
        health_latest = df_health.groupby('Date').last().reset_index() if not df_health.empty else pd.DataFrame(columns=HEALTH_COLS)
        lift_df = df_lifts[(df_lifts['Reps_or_Mins'] > 0) & (~df_lifts['Exercise'].str.contains("Rowing|Bike|Rest", na=False))].copy()
        
        if not lift_df.empty and not health_latest.empty: lift_df = pd.merge(lift_df, health_latest[['Date', 'Sleep_Score']], on='Date', how='left')
        elif not lift_df.empty: lift_df['Sleep_Score'] = 0
            
        cardio_df = df_lifts[df_lifts['Exercise'].str.contains("Rowing|Bike", na=False)].copy()
        if not cardio_df.empty and not health_latest.empty: cardio_df = pd.merge(cardio_df, health_latest, on='Date', how='left')

        at1, at2, at3, at4, at5, at6 = st.tabs(["👻 Milestones", "📈 Relative Strength", "🔥 INOL", "🦵 Radar", "🫀 Cardio", "🧬 Recomp & Recovery"])
        
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

        with at4:
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

        with at5:
            st.subheader("🫀 Cardio Engine Analytics")
            if not cardio_df.empty:
                c_ex = st.selectbox("Select Cardio Type", cardio_df['Exercise'].unique())
                cx_df = cardio_df[cardio_df['Exercise'] == c_ex].copy()
                if not cx_df.empty and 'Avg_HR' in cx_df.columns:
                    cx_df['Metric_Value'] = (cx_df['Reps_or_Mins'] * 60) / (cx_df['Distance_km'] * 1000 / 500) if "Rowing" in c_ex else cx_df['Distance_km'] / (cx_df['Reps_or_Mins'] / 60)
                    
                    fig_aerobic = go.Figure()
                    fig_aerobic.add_trace(go.Bar(x=cx_df['Date'], y=cx_df['Metric_Value'], name='Speed/Pace Output', marker_color='#1f77b4', yaxis='y1'))
                    fig_aerobic.add_trace(go.Scatter(x=cx_df['Date'], y=cx_df['Avg_HR'], name='Avg HR', mode='lines+markers', line=dict(color='#FF4B4B', width=3), yaxis='y2'))
                    fig_aerobic.update_layout(yaxis=dict(title="Pace/Speed", side='left'), yaxis2=dict(title='Avg HR (bpm)', side='right', overlaying='y', showgrid=False))
                    fig_aerobic.update_xaxes(tickformat="%Y-%m-%d", dtick="86400000")
                    st.plotly_chart(fig_aerobic, use_container_width=True)

        with at6:
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
            
            if not lift_df.empty and 'Sleep_Score' in lift_df.columns:
                rc_ex = st.selectbox("Compare Sleep vs Strength", lift_df['Exercise'].unique())
                rc_df = lift_df[(lift_df['Exercise'] == rc_ex) & (lift_df['Sleep_Score'] > 0)].groupby('Date').agg({'Epley_1RM': 'max', 'Sleep_Score': 'max'}).reset_index()
                if not rc_df.empty:
                    fig_sleep = px.scatter(rc_df, x='Sleep_Score', y='Epley_1RM', trendline="ols", title=f"Sleep vs. {rc_ex} e1RM", color='Sleep_Score', color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig_sleep, use_container_width=True)

with tab3:
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

with tab5:
    st.subheader("📋 Program Overview & Documentation")
    st.write("Easily copy this page to share your exact programming, logic, and execution cues with a coach or training partner.")
    st.write("---")
    
    for day, blocks in PROGRAM.items():
        if "Freestyle" in day or "Life Event" in day:
            continue
            
        st.markdown(f"## {day}")
        
        philosophy = DAY_PHILOSOPHY.get(day, "")
        if philosophy:
            st.info(f"**🧠 Programming Philosophy:** {philosophy}")
            
        warm_up = WARM_UPS.get(day, "")
        if warm_up:
            st.markdown(f"**🔥 Warm-Up Protocol:** {warm_up}")
            
        for block_name, exercises in blocks.items():
            st.markdown(f"#### {block_name}")
            for ex in exercises:
                target = REP_TARGETS.get(ex, "Sets x Reps")
                guide = EXERCISE_GUIDES.get(ex, {})
                st.markdown(f"- **{ex}** *(Target: {target})*")
                if guide:
                    st.markdown(f"  - *Setup:* {guide.get('Setup', '')}")
                    st.markdown(f"  - *Execution:* {guide.get('Execution', '')}")
                    st.markdown(f"  - *Why:* {guide.get('Why', '')}")
        st.write("---")
