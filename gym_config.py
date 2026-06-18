# --- PROGRAM & DICTIONARIES ---
PROGRAM = {
    "Tuesday: Lower A": {
        "Block 1: Heavy Front Squat": ["Heavy Barbell Front Squat"],
        "Block 2 (Superset): Reverse Nordics & Core": ["Reverse Nordic Curls", "Strict Hanging Leg Raises"],
        "Block 3 (Superset): KB Swings & Nordics": ["Heavy Russian Kettlebell Swings", "Nordic Curls"],
        "Block 4 (Tri-Set): Calves, Tibs & Core": ["Single-Leg Supported Dumbbell Calf Raise", "Wall Tibialis Raises", "Half-Kneeling Pallof Press"]
    },
    "Wednesday: Upper A": {
        "Block 1 (Alternating): T-Bar Row & DB Bench": ["T-Bar Landmine Row", "Dumbbell Bench Press"],
        "Block 2 (Alternating): DB Row & Push-Ups": ["Chest-Supported Dumbbell Row", "Push-Ups"],
        "Block 3 (Tri-Set): Triceps, Biceps & Chest": ["Overhead Tricep Extension", "Dumbbell Hammer Curls", "Banded Crossovers"],
        "Block 4 (Superset): Lateral & Rear Delts": ["Chest-Supported Lateral Raise", "Chest-Supported Rear Delt Flye"]
    },
    "Thursday: Lower B": {
        "Block 1: RDL": ["Romanian Deadlift (RDL)"],
        "Block 2 (Superset): Bulgarians & Rollouts": ["Bulgarian Split Squats", "Ab-Wheel Rollouts"],
        "Block 3 (Superset): Hip Thrusts & Hamstrings": ["Barbell Hip Thrusts", "Hamstring-Focused Roman Chair Extension"],
        "Block 4 (Quad-Set): Erectors, Calves & Core": ["Erector-Focused Roman Chair Extension", "Single-Leg Supported Dumbbell Calf Raise", "Heavy Suitcase Marches", "Front-Rack Kettlebell Marches"]
    },
    "Friday: Upper B": {
        "Block 1 (Alternating): Pull-Ups & Dips": ["Neutral Grip Pull-Ups", "Band-Assisted Dips"],
        "Block 2 (Alternating): Landmine Press & Face Pulls": ["Landmine Press", "Banded Face Pulls"],
        "Block 3 (Tri-Set): Curls, Pushdowns & Lateral Raises": ["Incline Supinated Dumbbell Curls", "Banded Tricep Pushdowns", "Chest-Supported Lateral Raise"]
    },
    "✈️ Travel: Bands & DBs": {
        "Block 1 (Superset): Quads & Hams": ["Bulgarian Split Squats", "Dumbbell Romanian Deadlift"],
        "Block 2 (Alternating): Chest & Back": ["Push-Ups", "Chest-Supported Dumbbell Row"],
        "Block 3 (Tri-Set): Arms & Shoulders": ["Dumbbell Hammer Curls", "Overhead Tricep Extension", "Standing Dumbbell Lateral Raise"],
        "Block 4 (Superset): Posture & Core": ["Banded Face Pulls", "Anchored Reverse Crunch"]
    },
    "🏨 Travel: Commercial Gym": {
        "Block 1 (Alternating): Legs": ["Machine Leg Press", "Seated Leg Curl"],
        "Block 2 (Alternating): Chest & Back": ["Machine Chest Press", "Lat Pulldown"],
        "Block 3 (Superset): Shoulders & Triceps": ["Cable Lateral Raise", "Cable Tricep Pushdown"],
        "Block 4 (Superset): Biceps & Core": ["Incline Supinated Dumbbell Curls", "Heavy Suitcase Holds"]
    },
    "Freestyle / Custom Day": {
        "Select Any Exercise(s)": [
            "Ab-Wheel Rollouts", "Anchored Reverse Crunch", "Band-Assisted Dips", "Banded Crossovers", 
            "Banded Face Pulls", "Banded Tricep Pushdowns", "Barbell Hip Thrusts", "Bulgarian Split Squats", 
            "Cable Lateral Raise", "Cable Tricep Pushdown", "Chest-Supported Dumbbell Row", "Chest-Supported Lateral Raise", 
            "Chest-Supported Rear Delt Flye", "Dumbbell Bench Press", "Dumbbell Hammer Curls", "Dumbbell Romanian Deadlift", 
            "Erector-Focused Roman Chair Extension", "Front-Rack Kettlebell Marches", 
            "Half-Kneeling Pallof Press", "Hamstring-Focused Roman Chair Extension", "Heavy Barbell Front Squat", 
            "Heavy Russian Kettlebell Swings", "Heavy Suitcase Holds", "Heavy Suitcase Marches", "Heels-Elevated Landmine Squat", 
            "Incline Supinated Dumbbell Curls", "Landmine Press", "Lat Pulldown", "Machine Chest Press", "Machine Leg Press", 
            "Neutral Grip Pull-Ups", "Nordic Curls", "Overhead Tricep Extension", "Push-Ups", "Reverse Nordic Curls", "Romanian Deadlift (RDL)", 
            "Seated Leg Curl", "Single-Arm Bench-Supported Dumbbell Row", "Single-Leg Supported Dumbbell Calf Raise", 
            "Standing Dumbbell Lateral Raise", "Strict Hanging Leg Raises", "T-Bar Landmine Row", "Wall Tibialis Raises"
        ]
    },
    "🧬 Life Event (Sick/Travel)": {
        "Rest": ["Rest / Recovery / Frozen Week"]
    }
}

REST_PROTOCOLS = {
    "Tuesday: Lower A": {
        "Block 1: Heavy Front Squat": "Perform Squats ➔ Rest 3 full minutes.",
        "Block 2 (Superset): Reverse Nordics & Core": "Reverse Nordics ➔ Hanging Leg Raises ➔ Rest 90s.",
        "Block 3 (Superset): KB Swings & Nordics": "KB Swings ➔ Nordic Curls ➔ Rest 90-120s.",
        "Block 4 (Tri-Set): Calves, Tibs & Core": "Calves ➔ Tibs ➔ Pallof Press ➔ Rest 60s."
    },
    "Wednesday: Upper A": {
        "Block 1 (Alternating): T-Bar Row & DB Bench": "T-Bar Row ➔ Rest 90s ➔ DB Bench ➔ Rest 90s.",
        "Block 2 (Alternating): DB Row & Push-Ups": "DB Row ➔ Rest 60-90s ➔ Push-Ups ➔ Rest 60-90s.",
        "Block 3 (Tri-Set): Triceps, Biceps & Chest": "Triceps Ext ➔ Hammer Curls ➔ Crossovers ➔ Rest 60s.",
        "Block 4 (Superset): Lateral & Rear Delts": "Lateral Raise ➔ Rear Delt Flye ➔ Rest 45-60s."
    },
    "Thursday: Lower B": {
        "Block 1: RDL": "Perform RDL ➔ Rest 3 full minutes.",
        "Block 2 (Superset): Bulgarians & Rollouts": "Split Squats ➔ Rollouts ➔ Rest 90s.",
        "Block 3 (Superset): Hip Thrusts & Hamstrings": "Hip Thrusts ➔ Roman Chair Ext ➔ Rest 90s.",
        "Block 4 (Quad-Set): Erectors, Calves & Core": "Erectors ➔ Calves ➔ Suitcase Marches ➔ KB Marches ➔ Rest 60s."
    },
    "Friday: Upper B": {
        "Block 1 (Alternating): Pull-Ups & Dips": "Pull-Ups ➔ Rest 90-120s ➔ Dips ➔ Rest 90-120s.",
        "Block 2 (Alternating): Landmine Press & Face Pulls": "Landmine Press ➔ Rest 60s ➔ Face Pulls ➔ Rest 60s.",
        "Block 3 (Tri-Set): Curls, Pushdowns & Lateral Raises": "Curls ➔ Pushdowns ➔ Lateral Raises ➔ Rest 60s."
    },
    "✈️ Travel: Bands & DBs": {
        "Block 1 (Superset): Quads & Hams": "Split Squats ➔ DB RDL ➔ Rest 90-120s.",
        "Block 2 (Alternating): Chest & Back": "Push-Ups ➔ Rest 60s ➔ DB Row ➔ Rest 60s.",
        "Block 3 (Tri-Set): Arms & Shoulders": "Hammer Curls ➔ Tricep Ext ➔ Lateral Raise ➔ Rest 60s.",
        "Block 4 (Superset): Posture & Core": "Face Pulls ➔ Reverse Crunch ➔ Rest 60s."
    },
    "🏨 Travel: Commercial Gym": {
        "Block 1 (Alternating): Legs": "Leg Press ➔ Rest 90-120s ➔ Seated Leg Curl ➔ Rest 90-120s.",
        "Block 2 (Alternating): Chest & Back": "Chest Press ➔ Rest 90s ➔ Lat Pulldown ➔ Rest 90s.",
        "Block 3 (Superset): Shoulders & Triceps": "Cable Lateral Raise ➔ Cable Pushdown ➔ Rest 60-90s.",
        "Block 4 (Superset): Biceps & Core": "Incline Curls ➔ Suitcase Holds ➔ Rest 60s."
    }
}

WARM_UPS = {
    "Tuesday: Lower A": "2x10 Deep Bodyweight Squats (pry the hips), 2x10 Cossack Squats, 90-sec Couch Stretch per leg, 1x20 Wall Tibialis Raises.",
    "Wednesday: Upper A": "2x15 Band Pull-aparts, 2x10 Push-up to Downward Dog (shoulder flow), 2x15 light Tricep Pushdowns (elbow blood flow).",
    "Thursday: Lower B": "2x15 BW Glute Bridges, 1x15 KB Goblet Squats (stay at bottom to open hips), 2x10 BW Good Mornings, 90-sec Couch Stretch.",
    "Friday: Upper B": "Dead hang from pull-up bar for 30-45s, 2x10 Scapular Pull-ups (activate lats), 2x15 Banded Face Pulls (rotator cuff prep).",
    "✈️ Travel: Bands & DBs": "2x15 Band Pull-aparts, 2x10 BW Squats, 2x10 BW Glute Bridges to wake up the body after travel.",
    "🏨 Travel: Commercial Gym": "5 mins light incline walking on treadmill. 2x15 Band Pull-aparts, 2x10 Push-up to Downward Dog."
}

COOL_DOWNS = {
    "Tuesday: Lower A": "2 mins 90/90 hip breathing. 90-sec deep couch stretch per leg to reset quad/hip flexor length.",
    "Wednesday: Upper A": "90-sec Floor Scorpion Pec Stretch per side. 60-sec dead hang from pull-up bar to completely decompress the spine.",
    "Thursday: Lower B": "90-sec Banded hamstring stretch per leg (lying on back). 2 mins Seated pigeon/glute stretch.",
    "Friday: Upper B": "2 mins foam rolling thoracic spine. 60-sec cross-body shoulder stretch. 60-sec Lat stretch holding an upright pole.",
    "✈️ Travel: Bands & DBs": "90-sec Couch Stretch per leg. 60-sec Lat stretch holding a doorway.",
    "🏨 Travel: Commercial Gym": "2 mins Seated pigeon/glute stretch. 60-sec dead hang from a pull-up bar to decompress."
}

MOBILITY_GUIDES = {
    "Band Pull-aparts": "Hold a light band at chest height, arms straight. Squeeze shoulder blades together to pull the band apart until it touches your chest. Keeps shoulders healthy.",
    "Push-up to Downward Dog": "Perform a push-up, then immediately push your hips high into the air (Downward Dog), pressing your chest toward your toes to open the shoulders.",
    "Deep Bodyweight Squats": "Sit into a deep squat. Use elbows to actively press knees outward. Gently shift weight side to side to loosen hip capsules.",
    "Cossack Squats": "Take a very wide stance. Squat deep onto one leg while keeping the other leg completely straight, toes pointing to the ceiling. Stretches the adductors.",
    "Couch Stretch": "Place knee in corner where floor meets a wall (or couch). Keep shin vertical against wall. Step other foot forward. Squeeze glute to brutally stretch hip flexor.",
    "Scapular Pull-ups": "Hang from a bar. Without bending elbows, pull shoulder blades DOWN and TOGETHER to lift body an inch or two. Pause, then lower.",
    "BW Glute Bridges": "Lie on back, knees bent, feet flat. Drive through heels to bridge hips to ceiling. Pause and squeeze glutes to wake them up.",
    "KB Goblet Squats": "Hold a kettlebell at chest. Drop into a deep squat. Keep chest tall and let weight anchor you into bottom stretch to pry open hips.",
    "BW Good Mornings": "Hands gently behind head. Unlock knees slightly, then push hips straight back until torso is almost parallel to floor to dynamically stretch hamstrings.",
    "Floor Scorpion Pec Stretch": "Lie flat on stomach with arms in 'T'. Lift left leg, bend knee, and roll body to right, trying to touch left foot to floor behind right leg.",
    "90/90 hip breathing": "Sit on floor with both legs bent at 90 degrees (one in front, one to side). Lean forward over front shin with a flat back. Take deep breaths.",
    "thoracic spine": "Place foam roller horizontal across upper back. Support neck with hands. Slowly extend upper back over roller to reverse poor posture.",
    "Lat stretch holding an upright pole": "Grab a vertical rack or pole with one hand at hip height. Sit hips back and let arm act as a rope, feeling a massive stretch from armpit down side.",
    "Banded hamstring stretch": "Lie on back. Loop a band around one foot. Keep leg perfectly straight and pull it toward face until you feel a deep hamstring stretch.",
    "Seated pigeon/glute stretch": "Sit on bench. Cross right ankle over left knee. Keeping back perfectly flat, hinge forward from hips to stretch the right glute."
}

DAY_PHILOSOPHY = {
    "Tuesday: Lower A": "Quad-dominant strength focus. The goal here is anterior chain power (Front Squats) followed by intense core bracing and armor-building to protect the spine.",
    "Wednesday: Upper A": "A heavy horizontal emphasis. Pairing pushes with pulls in supersets ensures structural balance across the shoulder joint while allowing you to accumulate dense volume efficiently.",
    "Thursday: Lower B": "Posterior chain obliteration. The RDL stretches the hamstrings under extreme load, while unilateral split squats fix imbalances. Finishes with intense erector and glute isolation.",
    "Friday: Upper B": "Vertical plane dominance. Pull-ups and overhead-angled presses (Landmine) build width and shoulder health, followed by targeted isolation for the arms and lateral delts.",
    "✈️ Travel: Bands & DBs": "Metabolic Stress Focus. Lacking heavy barbells, we compensate with extreme stretch, slow eccentrics, and high-density supersets to force growth through blood accumulation rather than heavy mechanical tension.",
    "🏨 Travel: Commercial Gym": "Machine Tension Focus. Capitalize on equipment you don't own. Machines offer zero instability, meaning 100% of your energy goes strictly into the target muscle with minimal CNS fatigue."
}

REP_TARGETS = {
    "T-Bar Landmine Row": "4 Sets × 8–10 Reps", "Dumbbell Bench Press": "4 Sets × 8–10 Reps",
    "Single-Arm Bench-Supported Dumbbell Row": "3 Sets × 10–12 Reps/arm", "Chest-Supported Dumbbell Row": "3 Sets × 10–12 Reps",
    "Push-Ups": "3 Sets × 10–15 Reps", "Strict Hanging Leg Raises": "3 Sets × 10–15 Reps",
    "Overhead Tricep Extension": "3 Sets × 12–15 Reps", "Dumbbell Hammer Curls": "3 Sets × 10–12 Reps",
    "Banded Crossovers": "3 Sets × 15–20 Reps", "Chest-Supported Lateral Raise": "4 Sets × 15–20 Reps",
    "Chest-Supported Rear Delt Flye": "4 Sets × 15–20 Reps", "Heavy Barbell Front Squat": "3 Sets × 4–6 Reps",
    "Reverse Nordic Curls": "4 Sets × 5–8 Reps", "Heels-Elevated Landmine Squat": "4 Sets × 6–8 Reps", "Bulgarian Split Squats": "4 Sets × 8–10 Reps/leg",
    "Hamstring-Focused Roman Chair Extension": "3 Sets × 12–15 Reps", "Anchored Reverse Crunch": "3 Sets × 10–12 Reps",
    "Wall Tibialis Raises": "3 Sets × 15–20 Reps", "Single-Leg Supported Dumbbell Calf Raise": "4 Sets × 10–12 Reps/leg",
    "Half-Kneeling Pallof Press": "3 Sets × 10–12 Reps/side", "Neutral Grip Pull-Ups": "4 Sets × 5–8 Reps",
    "Band-Assisted Dips": "4 Sets × 10–12 Reps", "Landmine Press": "3 Sets × 8–10 Reps",
    "Banded Face Pulls": "3 Sets × 15–20 Reps", "Incline Supinated Dumbbell Curls": "4 Sets × 10–12 Reps",
    "Banded Tricep Pushdowns": "3 Sets × 15–20 Reps", "Romanian Deadlift (RDL)": "4 Sets × 6–8 Reps",
    "Heavy Russian Kettlebell Swings": "3 Sets × 12–15 Reps", "Barbell Hip Thrusts": "3 Sets × 10–12 Reps",
    "Ab-Wheel Rollouts": "3 Sets × 8–10 Reps", "Nordic Curls": "3 Sets × 5–8 Reps",
    "Erector-Focused Roman Chair Extension": "3 Sets × 8–10 Reps", "Heavy Suitcase Holds": "3 Sets × 45 Seconds/side",
    "Heavy Suitcase Marches": "3 Sets × 40 Steps/side", "Front-Rack Kettlebell Marches": "3 Sets × 45 Seconds/side",
    "Dumbbell Romanian Deadlift": "4 Sets × 10–12 Reps", "Standing Dumbbell Lateral Raise": "4 Sets × 15–20 Reps",
    "Machine Leg Press": "4 Sets × 8–10 Reps", "Seated Leg Curl": "4 Sets × 10–15 Reps",
    "Machine Chest Press": "4 Sets × 8–10 Reps", "Lat Pulldown": "4 Sets × 8–12 Reps",
    "Cable Lateral Raise": "4 Sets × 12–15 Reps", "Cable Tricep Pushdown": "3 Sets × 12–15 Reps"
}

EXERCISE_GUIDES = {
    "Reverse Nordic Curls": {"Setup": "Kneel on a soft pad with knees hip-width apart, toes pointed straight back (or tucked if more comfortable). Squeeze glutes to lock your hips into full extension.", "Execution": "Keeping a perfectly straight line from your knees to your shoulders, slowly lean backward as far as you can control. Use your quads to pull yourself back up to the starting position.", "Why": "Delivers an unparalleled loaded stretch to the rectus femoris (quads) using pure bodyweight leverage, eliminating lower back fatigue entirely."},
    "Single-Leg Supported Dumbbell Calf Raise": {"Setup": "Hold a heavy dumbbell in one hand. Place that same-side foot on a wedge/plate. Use your free hand to firmly hold a wall or rack for perfect balance.", "Execution": "Let your heel drop as deep as possible into a stretch. Pause for 2 full seconds. Explode up to the top and pause.", "Why": "Removing the balance requirement allows 100% of your central nervous system to focus on calf tension, and the single-leg approach maximizes the load."},
    "Push-Ups": {"Setup": "Hands shoulder-width, core braced tightly (hollow body). Elevate hands on a bench if you cannot easily hit 10 perfect floor reps.", "Execution": "Descend slowly. PAUSE for 1 second with your chest hovering 1 inch off the surface, then explode up. Keep elbows tucked at 45 degrees.", "Why": "The dead-stop pause kills the stretch reflex, forcing raw pec/triceps activation. Hand elevation mechanically scales the resistance down so you can maintain perfect form."},
    "Strict Hanging Leg Raises": {"Setup": "Hang from a pull-up bar with a hollow body position.", "Execution": "Initiate by tilting your pelvis upward, then raise your legs (or knees if scaling) until they reach 90 degrees. Lower strictly over 3 seconds.", "Why": "Elite anti-extension core training that also builds grip and lat endurance."},
    "Heavy Suitcase Marches": {"Setup": "Hold a heavy kettlebell/dumbbell in one hand. Stand perfectly tall in place.", "Execution": "Slowly march in place, driving your knees above your hip crease with immense control. Do not let your shoulders tilt.", "Why": "Yields the exact same anti-lateral flexion stimulus as a carry, but with zero spinal twisting risk in small spaces."},
    "Chest-Supported Dumbbell Row": {"Setup": "Set an incline bench to 45 degrees. Lay chest flat against the pad, feet anchored securely on the floor.", "Execution": "Let long arms hang straight down. Row both dumbbells up by driving your elbows back toward your hips.", "Why": "Completely removes the lower back and core stabilization requirement, allowing you to use clunky dumbbells perfectly without them hitting the floor or ribs."},
    "T-Bar Landmine Row": {"Setup": "Straddle the barbell facing away from the landmine anchor. Use a V-grip handle hooked under the bar.", "Execution": "Hinge at hips so torso is almost parallel. Row plates to your chest. Slow 3-second negative (lowering) phase.", "Why": "Stable pulling builds back thickness without the systemic lower back fatigue of a standard bent-over barbell row."},
    "Dumbbell Bench Press": {"Setup": "Set bench to a slight incline (15-30 degrees). Shoulder blades pinned down and back.", "Execution": "Lower slowly (3s) to a deep stretch. Press up, but STOP a few inches before the dumbbells touch. Do not lock out.", "Why": "A slight incline perfectly aligns with the pec fibers. Stopping before the bells touch prevents the joints from 'stacking', keeping 100% of the tension on the chest."},
    "Single-Arm Bench-Supported Dumbbell Row": {"Setup": "Hand and same-side knee on the bench. Back perfectly flat.", "Execution": "Pull the dumbbell towards your HIP, not your armpit. Pause for 1 full second at the top contraction.", "Why": "Bench support removes lower back strain. Pulling to the hip isolates the lats instead of shrugging with your upper traps."},
    "Overhead Tricep Extension": {"Setup": "Anchor band at waist height behind you (or step on it). Grab band, face away, and bring hands behind head with elbows pointing up.", "Execution": "Press the band straight up to the ceiling. Control the descent back into a deep stretch.", "Why": "Bands provide an 'ascending resistance curve', meaning tension increases at the lockout where the triceps are mechanically strongest, while keeping constant tension in the stretch."},
    "Dumbbell Hammer Curls": {"Setup": "Standing, neutral grip (palms facing each other).", "Execution": "Squeeze up cleanly, then a strict 2-second negative. Zero swinging or momentum.", "Why": "Targets the brachialis and brachioradialis. This pushes the bicep up (creating a larger peak) and prevents elbow tendonitis."},
    "Banded Crossovers": {"Setup": "Anchor bands HIGH (above head). Step forward to create tension.", "Execution": "Pull down and across your body (high-to-low). Squeeze for 2 full seconds at the bottom contraction where your hands overlap.", "Why": "The high-to-low angle perfectly targets the lower/sternocostal pec fibers, brilliantly complementing the upper-pec focus of your incline DB presses."},
    "Chest-Supported Lateral Raise": {"Setup": "Chest flat against a steep incline bench.", "Execution": "Lead with the elbows, sweeping the dumbbells OUT, not just up. Stop at shoulder height.", "Why": "Strict isolation of the lateral delt. The bench prevents you from using lumbar extension (leaning back) to cheat the weight."},
    "Chest-Supported Rear Delt Flye": {"Setup": "Chest on incline bench, palms facing down or neutral.", "Execution": "Sweep arms out to the side. Stop when elbows align with shoulders (do NOT pinch your shoulder blades together).", "Why": "Stopping before the shoulder blades retract ensures the load stays 100% on the rear deltoid, not the rhomboids or traps."},
    "Heavy Barbell Front Squat": {"Setup": "Clean grip or cross-arm grip. Bar resting deep on the meaty part of the front delts.", "Execution": "Deep, upright squat. Drive your elbows UP violently as you come out of the hole to prevent your chest from collapsing.", "Why": "Forces an upright torso, shifting the load intensely onto the quads and off the lumbar spine."},
    "Heels-Elevated Landmine Squat": {"Setup": "Place a squat wedge under heels. Hold the thick part of the barbell sleeve at upper-chest level.", "Execution": "Perform 1.5 reps: Drop into a deep squat, rise halfway up, drop back into deep squat, then stand up.", "Why": "Maximizes quad stretch while creating immense time under tension without needing spine-crushing weights."},
    "Anchored Reverse Crunch": {"Setup": "Lying on back, gripping a heavy kettlebell or pole behind your head.", "Execution": "Roll pelvis UP towards sternum. Control descent (3 seconds) until tailbone gently touches the floor.", "Why": "Flexes the spine against resistance (true abdominal function) rather than just working hip flexors."},
    "Heavy Russian Kettlebell Swings": {"Setup": "Hinge position, KB slightly in front of you.", "Execution": "Hike it back between your legs, then snap hips forward violently. Arms are just ropes. Stop at chest height.", "Why": "Builds explosive posterior chain power, hamstring resilience, and glute lockout strength."},
    "Nordic Curls": {"Setup": "Kneeling, ankles secured under a bar or by a partner.", "Execution": "Squeeze glutes to lock hips. Fall forward as slowly as possible. Catch yourself, push back up.", "Why": "The ultimate hamstring bulletproofing exercise. Lengthens muscle fascicles, reducing tear risk."},
    "Wall Tibialis Raises": {"Setup": "Lean back against a wall, feet placed out in front of you.", "Execution": "Pull toes up towards shins as hard as possible. Hold for 1 second.", "Why": "Bulletproofs the knees. Strengthening the tibialis anterior prevents shin splints and patellar pain."},
    "Half-Kneeling Pallof Press": {"Setup": "Half-kneeling, band anchored to side at chest height.", "Execution": "Press band straight out in front. Hold for 2 seconds, violently resisting the urge to twist.", "Why": "Elite anti-rotation core training. Teaches deep core to brace against twisting forces."},
    "Neutral Grip Pull-Ups": {"Setup": "Palms facing each other.", "Execution": "Start from a dead hang. Pull upper chest to the bar. Control the eccentric phase.", "Why": "Neutral grip is highly shoulder-friendly and gives the lats a massive mechanical advantage for growth."},
    "Band-Assisted Dips": {"Setup": "Band looped over bars and under knees.", "Execution": "Slight forward lean to bias the chest. Descend until you feel a deep stretch in the pecs.", "Why": "Band provides help at the bottom (most vulnerable position) forcing a strict, deep, hypertrophy rep."},
    "Landmine Press": {"Setup": "Half-kneeling or standing. Hold barbell sleeve at shoulder height.", "Execution": "Press up and slightly forward, following the natural arc of the barbell.", "Why": "The arcing path is incredibly healthy and natural for the shoulder capsule."},
    "Banded Face Pulls": {"Setup": "Band anchored at eye level.", "Execution": "Pull band towards nose, pulling hands APART and rotating knuckles UP (external rotation) at the end.", "Why": "The ultimate posture corrector. Hits rear delts, rhomboids, and bulletproofs the rotator cuff."},
    "Incline Supinated Dumbbell Curls": {"Setup": "Bench at 45-60 degrees. Let arms hang straight down. Palms facing forward.", "Execution": "Keep elbows pinned back. Curl up, squeezing the biceps.", "Why": "Puts the bicep in an extreme stretched position (long head focus), triggering massive hypertrophy."},
    "Banded Tricep Pushdowns": {"Setup": "Band anchored high above you.", "Execution": "Keep elbows pinned to sides. Push down and pull band APART at the very bottom.", "Why": "Band resistance increases at peak contraction, matching the strength curve of the triceps perfectly."},
    "Romanian Deadlift (RDL)": {"Setup": "Hex/Trap bar. Feet shoulder-width. Unlock knees slightly and freeze them.", "Execution": "Push hips straight back. Stop and reverse the motion the moment hamstrings are fully stretched.", "Why": "Hex Bar aligns center of gravity with midline, reducing shear force on lumbar spine."},
    "Bulgarian Split Squats": {"Setup": "Rear foot elevated on a bench. Hold dumbbells at sides.", "Execution": "Drop back knee straight down. Lean torso slightly forward to bias glutes, or stay upright to bias quads.", "Why": "Eliminates left/right imbalances and provides an extreme stretch under load with zero spinal compression."},
    "Ab-Wheel Rollouts": {"Setup": "Kneeling. Squeeze glutes to lock pelvis into posterior tilt.", "Execution": "Roll out until torso is parallel. Pull back using ABS, not by pushing hips back.", "Why": "Extreme anti-extension core strength. Forces rectus abdominis to stabilize the spine under intense load."},
    "Barbell Hip Thrusts": {"Setup": "Upper back on a bench, heavy barbell padded across hips.", "Execution": "Drive through heels. Brutal 2-second squeeze at the top. Keep chin tucked.", "Why": "The highest glute activation of any exercise, completely bypassing the lower back."},
    "Hamstring-Focused Roman Chair Extension": {"Setup": "45-degree hyperextension bench. Pad sits BELOW hips.", "Execution": "Keep back flat. Hinge down, pull up using only hamstrings and glutes.", "Why": "Provides a fantastic, loaded stretch for hamstrings without axial loading on the spine."},
    "Erector-Focused Roman Chair Extension": {"Setup": "45-degree bench. Pad sits AT hips.", "Execution": "Allow upper back to round over the pad, then pull up by extending the spine.", "Why": "Directly trains the spinal erectors through full range of motion, building a thick, resilient lower back."},
    "Heavy Suitcase Holds": {"Setup": "Hold heavy kettlebell/dumbbell in one hand. Stand perfectly tall.", "Execution": "Perform slow, highly controlled march in place. Do not let weight pull shoulder down.", "Why": "Dynamic pelvic stabilizer, bulletproofing the glute medius and preventing hip drop."},
    "Front-Rack Kettlebell Marches": {"Setup": "Two heavy KBs held at chest.", "Execution": "Slowly march in place, lifting knees above hip level with immense control.", "Why": "Heavy core stabilization. Forces upper back and core to work isometrically to keep you upright."},
    "Dumbbell Romanian Deadlift": {"Setup": "Hold DBs in front of thighs, feet hip-width. Unlock knees.", "Execution": "Push hips straight back until you feel a massive hamstring stretch. Keep back perfectly flat.", "Why": "Excellent for travel. Provides deep hamstring loaded stretch without needing a heavy barbell."},
    "Standing Dumbbell Lateral Raise": {"Setup": "Stand tall, DBs at sides. Slight forward lean.", "Execution": "Sweep the dumbbells OUT and AWAY from you, not just up. Stop at shoulder height.", "Why": "Pure isolation of the lateral deltoid for width."},
    "Machine Leg Press": {"Setup": "Feet shoulder-width on the sled. Pull yourself deep into the seat to protect your lower back.", "Execution": "Lower the sled as deep as your mobility allows without your tailbone tucking under. Drive back up but do NOT lock the knees.", "Why": "Zero balancing required. Allows you to take the quads perfectly to muscular failure safely."},
    "Seated Leg Curl": {"Setup": "Align the machine axis perfectly with your knee joint. Pin the thigh pad down hard.", "Execution": "Curl the weight under, pausing for 1 second at the peak contraction.", "Why": "The seated position uniquely stretches the hamstrings at the hip, triggering massive stretch-mediated hypertrophy."},
    "Machine Chest Press": {"Setup": "Set seat height so the handles align with your mid/lower chest. Pin shoulder blades back.", "Execution": "Press the handles forward, focusing on bringing your biceps across your chest. Control the negative.", "Why": "Locks you into a safe plane of motion, allowing you to fry the pecs without shoulder instability."},
    "Lat Pulldown": {"Setup": "Use a medium/wide grip. Lock your knees under the pad tightly.", "Execution": "Pull the bar down to your upper chest, driving your elbows down toward your back pockets.", "Why": "Replaces pull-ups with adjustable tension, letting you build back width perfectly at any strength level."},
    "Cable Lateral Raise": {"Setup": "Set a cable to the lowest position. Grab it with the opposite hand (cable crosses in front of you).", "Execution": "Sweep the arm out to the side. Control the descent as the cable pulls your arm across your body.", "Why": "Unlike dumbbells which lose tension at the bottom, cables provide constant tension through the entire range of motion."},
    "Cable Tricep Pushdown": {"Setup": "Attach a rope to a high cable. Tuck elbows strictly to your ribs.", "Execution": "Push down and pull the rope APART at the very bottom. Control it on the way up.", "Why": "Maintains tension at the peak contraction where the triceps are mechanically strongest."}
}

DAILY_SYSTEM_RESET = {
    "1. The Shin Breaker": {"Target": "1-2min: Stretches the anterior tibialis to prevent shin splints and keep knees healthy.", "Execution": "Kneel with toes pointed back (laces flat), sit butt onto heels. Lean back slightly and lift knees 1 inch off the floor.", "Progression": "Increase the height you lift your knees off the floor."},
    "2. The Combat Stretch (Ankle Mobility)": {"Target": "1-2min per side: Unlocks true ankle dorsiflexion for deep squatting.", "Execution": "Half-kneeling lunge. Place a heavy kettlebell on your front knee. Drive the knee as far over your toes as humanly possible while keeping the heel glued to the floor.", "Progression": "Increase the weight of the kettlebell to force a deeper fascial stretch."},
    "3. The Couch Stretch": {"Target": "2min per side: Deep stretch of the quadriceps and hip flexors.", "Execution": "Place knee into a wall/couch corner, shin vertical. Squeeze the glute of the stretching leg HARD and lift torso upright.", "Progression": "Move from resting hands on a box/chair to a fully upright, unsupported torso."},
    "4. The 90/90 Hip Switch": {"Target": "2min: Restores internal and external rotation of the hip capsule.", "Execution": "Sit on the floor, both legs bent at 90 degrees (one in front, one behind). Pivot on your heels to windshield-wiper your knees to the other side.", "Progression": "Perform the movement without using your hands on the floor for support."},
    "5. The 'Paleo Chair'": {"Target": "2min: Recalibrates hips and ankles for deep squatting.", "Execution": "Drop into the deepest squat you can hold with heels flat. Drive knees out with elbows, keep chest tall.", "Progression": "Shift from holding a doorframe for support to a completely free-standing hold."},
    "6. The Lateral Child’s Pose": {"Target": "1min each side: Stretches the latissimus dorsi and quadratus lumborum (lower back).", "Execution": "Sit in Child's pose, walk both hands far to one side, and push the opposite hip down into your heel.", "Progression": "Walk the hands further laterally to increase the fascial pull."},
    "7. Wall 'Snow Angels'": {"Target": "15 reps: Restores thoracic spine (upper back) mobility and shoulder health.", "Execution": "Back flat against wall, touch lower back, head, elbows, and wrists to the wall. Slide arms up to a 'Y' and down to a 'W'.", "Progression": "Move feet closer to the wall while maintaining full lower back contact."},
    "8. The 'Neck Anchor'": {"Target": "1min per side: Releases tension in the upper traps and neck.", "Execution": "Place right hand behind back, tilt left ear to left shoulder, rotate chin toward armpit.", "Progression": "Gently use the non-anchored hand to apply microscopic overpressure to the stretch."}
}

VOLUME_THRESHOLDS = {
    "Chest": {"MEV": 10, "MRV": 20}, "Back": {"MEV": 10, "MRV": 20},
    "Quads": {"MEV": 8, "MRV": 18}, "Hamstrings": {"MEV": 6, "MRV": 14}, "Glutes": {"MEV": 4, "MRV": 16},
    "Biceps": {"MEV": 8, "MRV": 20}, "Triceps": {"MEV": 6, "MRV": 18},
    "Shoulders": {"MEV": 8, "MRV": 22}, "Calves": {"MEV": 8, "MRV": 20}, "Abs": {"MEV": 4, "MRV": 20}
}

EXERCISE_CAPS = {
    "Heavy Barbell Front Squat": 4, "Heels-Elevated Landmine Squat": 4, "Reverse Nordic Curls": 4, "Romanian Deadlift (RDL)": 4,
    "Bulgarian Split Squats": 4, "T-Bar Landmine Row": 4, "Dumbbell Bench Press": 4,
    "Landmine Press": 4, "Neutral Grip Pull-Ups": 4, "Band-Assisted Dips": 4,
    "Heavy Russian Kettlebell Swings": 4, "Barbell Hip Thrusts": 4, "Nordic Curls": 4,
    "Machine Leg Press": 4, "Machine Chest Press": 4, "Lat Pulldown": 5, "Dumbbell Romanian Deadlift": 4,
    "Single-Arm Bench-Supported Dumbbell Row": 6, "Chest-Supported Dumbbell Row": 6, "Push-Ups": 6, 
    "Overhead Tricep Extension": 6, "Dumbbell Hammer Curls": 6, "Banded Crossovers": 6, 
    "Chest-Supported Lateral Raise": 6, "Chest-Supported Rear Delt Flye": 6, "Anchored Reverse Crunch": 6, 
    "Strict Hanging Leg Raises": 6, "Wall Tibialis Raises": 6, "Single-Leg Supported Dumbbell Calf Raise": 6, "Half-Kneeling Pallof Press": 6, 
    "Banded Face Pulls": 6, "Incline Supinated Dumbbell Curls": 6, "Banded Tricep Pushdowns": 6, 
    "Ab-Wheel Rollouts": 6, "Erector-Focused Roman Chair Extension": 6, "Heavy Suitcase Holds": 6, "Heavy Suitcase Marches": 6,
    "Front-Rack Kettlebell Marches": 6, "Hamstring-Focused Roman Chair Extension": 6, 
    "Standing Dumbbell Lateral Raise": 6, "Seated Leg Curl": 6, "Cable Lateral Raise": 6, "Cable Tricep Pushdown": 6
}

MUSCLE_MAP = {
    "T-Bar Landmine Row": {"Back": 1.0, "Biceps": 0.5}, "Dumbbell Bench Press": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5},
    "Single-Arm Bench-Supported Dumbbell Row": {"Back": 1.0, "Biceps": 0.5}, "Chest-Supported Dumbbell Row": {"Back": 1.0, "Biceps": 0.5},
    "Push-Ups": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5}, 
    "Overhead Tricep Extension": {"Triceps": 1.0}, "Dumbbell Hammer Curls": {"Biceps": 1.0},
    "Banded Crossovers": {"Chest": 1.0, "Shoulders": 0.5}, "Chest-Supported Lateral Raise": {"Shoulders": 1.0},
    "Chest-Supported Rear Delt Flye": {"Shoulders": 1.0, "Back": 0.5}, "Heavy Barbell Front Squat": {"Quads": 1.0, "Glutes": 0.5},
    "Heels-Elevated Landmine Squat": {"Quads": 1.0, "Glutes": 0.5}, "Reverse Nordic Curls": {"Quads": 1.0, "Abs": 0.5}, "Bulgarian Split Squats": {"Quads": 1.0, "Glutes": 1.0},
    "Hamstring-Focused Roman Chair Extension": {"Hamstrings": 1.0, "Glutes": 0.5}, "Anchored Reverse Crunch": {"Abs": 1.0},
    "Strict Hanging Leg Raises": {"Abs": 1.0},
    "Wall Tibialis Raises": {"Calves": 1.0}, "Single-Leg Supported Dumbbell Calf Raise": {"Calves": 1.0},
    "Half-Kneeling Pallof Press": {"Abs": 1.0}, "Neutral Grip Pull-Ups": {"Back": 1.0, "Biceps": 0.5},
    "Band-Assisted Dips": {"Chest": 1.0, "Triceps": 1.0, "Shoulders": 0.5}, "Landmine Press": {"Shoulders": 1.0, "Chest": 0.5, "Triceps": 0.5},
    "Banded Face Pulls": {"Shoulders": 1.0, "Back": 0.5}, "Incline Supinated Dumbbell Curls": {"Biceps": 1.0},
    "Banded Tricep Pushdowns": {"Triceps": 1.0}, "Romanian Deadlift (RDL)": {"Hamstrings": 1.0, "Glutes": 1.0},
    "Heavy Russian Kettlebell Swings": {"Glutes": 1.0, "Hamstrings": 0.5}, "Barbell Hip Thrusts": {"Glutes": 1.0, "Hamstrings": 0.5},
    "Ab-Wheel Rollouts": {"Abs": 1.0}, "Nordic Curls": {"Hamstrings": 1.0, "Glutes": 0.5},
    "Erector-Focused Roman Chair Extension": {"Back": 1.0, "Glutes": 0.5}, "Heavy Suitcase Holds": {"Abs": 1.0},
    "Heavy Suitcase Marches": {"Abs": 1.0}, "Front-Rack Kettlebell Marches": {"Abs": 1.0, "Quads": 0.5},
    "Dumbbell Romanian Deadlift": {"Hamstrings": 1.0, "Glutes": 0.5}, "Standing Dumbbell Lateral Raise": {"Shoulders": 1.0},
    "Machine Leg Press": {"Quads": 1.0, "Glutes": 0.5}, "Seated Leg Curl": {"Hamstrings": 1.0},
    "Machine Chest Press": {"Chest": 1.0, "Shoulders": 0.5, "Triceps": 0.5}, "Lat Pulldown": {"Back": 1.0, "Biceps": 0.5},
    "Cable Lateral Raise": {"Shoulders": 1.0}, "Cable Tricep Pushdown": {"Triceps": 1.0}
}

BW_MULTIPLIERS = {
    "Neutral Grip Pull-Ups": 0.95, "Band-Assisted Dips": 0.95, "Push-Ups": 0.65,
    "Nordic Curls": 0.60, "Reverse Nordic Curls": 0.65, "Anchored Reverse Crunch": 0.40, "Strict Hanging Leg Raises": 0.50, "Ab-Wheel Rollouts": 0.50,
    "Single-Leg Supported Dumbbell Calf Raise": 1.0, "Bulgarian Split Squats": 0.85, 
    "Erector-Focused Roman Chair Extension": 0.50, "Glute-Focused Roman Chair Extension": 0.50,
    "Hamstring-Focused Roman Chair Extension": 0.50, "Heavy Barbell Front Squat": 0.85,
    "Wall Tibialis Raises": 0.30, "Machine Leg Press": 0.0, "Seated Leg Curl": 0.0,
    "Machine Chest Press": 0.0, "Lat Pulldown": 0.0, "Cable Lateral Raise": 0.0, "Cable Tricep Pushdown": 0.0,
    "Dumbbell Romanian Deadlift": 0.40, "Standing Dumbbell Lateral Raise": 0.0, "Chest-Supported Dumbbell Row": 0.0,
    "Heavy Suitcase Marches": 0.0
}

BAND_SUBTRACTIONS = {
    "None": 0.0, "Yellow (13.6kg)": 13.6, "Red (22.6kg)": 22.6, 
    "Black (36.3kg)": 36.3, "Purple (45.4kg)": 45.4, 
    "Green (68.0kg)": 68.0, "Green + Yellow (81.6kg)": 81.6,
    "Blue (88.5kg)": 88.5, "Blue + Yellow (102.1kg)": 102.1,
    "Blue + Red (111.1kg)": 111.1, "Orange (113.4kg)": 113.4,
    "Orange + Yellow (127.0kg)": 127.0
}

ADJUSTABLE_DBS = [0.0, 4.0, 7.0, 9.0, 11.0, 14.0, 16.0, 18.0, 20.0, 23.0, 25.0, 27.0, 30.0, 32.0, 34.0, 36.0, 39.0, 41.0]
KETTLEBELLS = [0.0, 4.0, 6.0, 8.0, 12.0, 16.0, 20.0]
PUSH_UP_VARIATIONS = ["Elevated", "Flat", "Deficit"]

UNILATERAL_EXERCISES = ["Bulgarian Split Squats", "Single-Arm Bench-Supported Dumbbell Row", "Half-Kneeling Pallof Press", "Heavy Suitcase Holds", "Heavy Suitcase Marches", "Front-Rack Kettlebell Marches", "Single-Leg Supported Dumbbell Calf Raise"]
HEAVY_COMPOUNDS = ["Heavy Barbell Front Squat", "Romanian Deadlift (RDL)", "Dumbbell Bench Press", "T-Bar Landmine Row", "Landmine Press", "Machine Leg Press", "Machine Chest Press"]

ASSISTED_EXERCISES = ["Neutral Grip Pull-Ups", "Band-Assisted Dips"]
RESISTED_EXERCISES = ["Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]
BODYWEIGHT_ONLY = ["Anchored Reverse Crunch", "Strict Hanging Leg Raises", "Nordic Curls", "Reverse Nordic Curls", "Ab-Wheel Rollouts"]
PURE_BAND_EXERCISES = ["Banded Face Pulls", "Banded Crossovers", "Banded Tricep Pushdowns", "Half-Kneeling Pallof Press", "Overhead Tricep Extension"]

