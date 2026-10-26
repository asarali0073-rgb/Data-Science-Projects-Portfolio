
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Titanic Dashboard",
    page_icon="🚢",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    dataset_path = Path(__file__).resolve().parent / "titanic_survival_classification_dataset.csv"
    return pd.read_csv(dataset_path)

df = load_data()

st.title("🚢 Titanic Survival Dashboard")
st.write("Explore Titanic passenger data and survival patterns.")

# Sidebar filters
st.sidebar.header("Filters")

sex_options = ["All"] + sorted(df["Sex"].dropna().unique().tolist())
selected_sex = st.sidebar.selectbox("Select Sex", sex_options)

class_options = ["All"] + sorted(df["Pclass"].dropna().unique().tolist())
selected_class = st.sidebar.selectbox("Select Passenger Class", class_options)

filtered_df = df.copy()

if selected_sex != "All":
    filtered_df = filtered_df[filtered_df["Sex"] == selected_sex]

if selected_class != "All":
    filtered_df = filtered_df[filtered_df["Pclass"] == selected_class]

# KPI metrics
total = len(filtered_df)
survived = (filtered_df["Survived"] == 1).sum()
not_survived = (filtered_df["Survived"] == 0).sum()
survival_rate = survived / total * 100 if total else 0

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Passengers", total)
c2.metric("Survived", int(survived))
c3.metric("Did Not Survive", int(not_survived))
c4.metric("Survival Rate", f"{survival_rate:.1f}%")

st.divider()

# Survival distribution
col1, col2 = st.columns(2)

with col1:
    st.subheader("Survival Distribution")

    survival_counts = (
        filtered_df["Survived"]
        .map({0: "Did Not Survive", 1: "Survived"})
        .value_counts()
        .rename_axis("Outcome")
        .reset_index(name="Count")
    )

    fig = px.pie(
        survival_counts,
        names="Outcome",
        values="Count",
        hole=0.4,
        title="Survived vs Not Survived"
    )

    st.plotly_chart(fig, use_container_width=True)

# Survival by gender
with col2:
    st.subheader("Survival by Gender")

    gender_data = (
        filtered_df.groupby("Sex", as_index=False)["Survived"]
        .mean()
    )
    gender_data["Survival Rate (%)"] = gender_data["Survived"] * 100

    fig = px.bar(
        gender_data,
        x="Sex",
        y="Survival Rate (%)",
        text_auto=".1f",
        title="Survival Rate by Gender"
    )

    fig.update_yaxes(range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

# Survival by passenger class
st.subheader("Survival by Passenger Class")

class_data = (
    filtered_df.groupby("Pclass", as_index=False)["Survived"]
    .mean()
)
class_data["Survival Rate (%)"] = class_data["Survived"] * 100

fig = px.bar(
    class_data,
    x="Pclass",
    y="Survival Rate (%)",
    text_auto=".1f",
    title="Survival Rate by Class"
)

fig.update_yaxes(range=[0, 100])
st.plotly_chart(fig, use_container_width=True)

# Age distribution
col3, col4 = st.columns(2)

with col3:
    st.subheader("Age Distribution")

    fig = px.histogram(
        filtered_df.dropna(subset=["Age"]),
        x="Age",
        color="Survived",
        nbins=25,
        barmode="overlay",
        title="Age vs Survival",
        labels={"Survived": "Survived (0=No, 1=Yes)"}
    )

    st.plotly_chart(fig, use_container_width=True)

with col4:
    st.subheader("Fare Distribution")

    fig = px.box(
        filtered_df.dropna(subset=["Fare"]),
        x="Pclass",
        y="Fare",
        color="Pclass",
        title="Ticket Fare by Passenger Class"
    )

    st.plotly_chart(fig, use_container_width=True)

# Summary 
st.subheader("Summary Statistics")
st.dataframe(
    filtered_df.describe(include="all").T,
    use_container_width=True
)

# Passenger records
st.subheader("Passenger Records")
st.dataframe(filtered_df, use_container_width=True, hide_index=True)


st.download_button(
    "Download Filtered Data",
    data=filtered_df.to_csv(index=False).encode("utf-8"),
    file_name="titanic_filtered_data.csv",
    mime="text/csv"
)
