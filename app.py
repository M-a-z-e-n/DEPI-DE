import streamlit as st
import pandas as pd
import joblib


# Load CSS
def load_css():
    with open("DEADLOCK.css") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


load_css()


# Title
st.title("☄️ NASA NEO Hazard Prediction")


# Load model & scaler
model = joblib.load(
    r"C:\Users\HP\vscode\DEADLOCK\neo_random_forest_model.pkl"
)

scaler = joblib.load(
    r"C:\Users\HP\vscode\DEADLOCK\neo_scaler.pkl"
)


st.write("Enter asteroid details below:")


# Inputs

absolute_magnitude_h = st.number_input(
    "Absolute Magnitude H"
)


estimated_diameter_min_km = st.number_input(
    "Estimated Diameter Min (km)"
)


estimated_diameter_max_km = st.number_input(
    "Estimated Diameter Max (km)"
)


is_sentry_object = st.selectbox(
    "Is Sentry Object?",
    [0, 1]
)


relative_velocity_kph = st.number_input(
    "Relative Velocity (kph)"
)


miss_distance_km = st.number_input(
    "Miss Distance (km)"
)


miss_distance_lunar = st.number_input(
    "Miss Distance Lunar"
)


miss_distance_au = st.number_input(
    "Miss Distance AU"
)


# Integer inputs

year = st.number_input(
    "Year",
    min_value=1900,
    max_value=2100,
    step=1,
    format="%d"
)


month = st.number_input(
    "Month",
    min_value=1,
    max_value=12,
    step=1,
    format="%d"
)


day = st.number_input(
    "Day",
    min_value=1,
    max_value=31,
    step=1,
    format="%d"
)



# Prediction

if st.button("Predict Hazard Level ☄️"):


    input_data = pd.DataFrame({

        "absolute_magnitude_h":
        [absolute_magnitude_h],


        "estimated_diameter_min_km":
        [estimated_diameter_min_km],


        "estimated_diameter_max_km":
        [estimated_diameter_max_km],


        "is_sentry_object":
        [is_sentry_object],


        "relative_velocity_kph":
        [relative_velocity_kph],


        "miss_distance_km":
        [miss_distance_km],


        "miss_distance_lunar":
        [miss_distance_lunar],


        "miss_distance_au":
        [miss_distance_au],


        "year":
        [int(year)],


        "month":
        [int(month)],


        "day":
        [int(day)]

    })


    # Match training features
    input_data = input_data.reindex(
        columns=scaler.feature_names_in_,
        fill_value=0
    )


    # Scaling
    scaled_input = scaler.transform(
        input_data
    )


    # Prediction
    prediction = model.predict(
        scaled_input
    )


    probability = model.predict_proba(
        scaled_input
    )[0][1]


    risk_percentage = probability * 100



    # Result

    if prediction[0] == 1:


        st.error(
            f"""
☄️ Hazard Alert

This asteroid is classified as potentially hazardous.

📊 Risk Probability:
{risk_percentage:.2f}%

⚠️ Recommendation:
Further observation and analysis are suggested.
"""
        )


    else:


        st.success(
            f"""
🌌 Safe Classification

This asteroid is classified as not hazardous.

📊 Risk Probability:
{risk_percentage:.2f}%

✅ Current Assessment:
No significant hazard detected.
"""
        )