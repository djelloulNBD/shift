import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date


st.set_page_config(page_title="Rotational Shift Scheduler", layout="wide")

st.title("🗓️ Weekly Rotational Shift Scheduler")


# Agent list
agents = ["Djelloul", "Nour", "Abdennour", "Iheb"]


# Function to rotate agents for 3-person morning shift
def rotate_agents(agent_list, week_offset, count):
    rotated = agent_list[week_offset % len(agent_list):] + agent_list[:week_offset % len(agent_list)]
    return rotated[:count]


# Function to select afternoon shift from agents NOT in morning shift
def select_afternoon_agent(agent_list, morning_agents, week_offset):
    available = [a for a in agent_list if a not in morning_agents]
    if not available:
        return "None"
    rotated = available[week_offset % len(available):] + available[:week_offset % len(available)]
    return rotated[0]


# Function to alternate Sunday morning shift
def sunday_morning_agent(week_offset):
    return "Djelloul" if week_offset % 2 == 0 else "Abdennour"


# Generate schedule
def generate_schedule(start_date_str, num_weeks):
    start_date = datetime.strptime(str(start_date_str), "%Y-%m-%d")
    schedule = []

    for week in range(num_weeks):
        for day_offset in range(7):
            date_obj = start_date + timedelta(days=week * 7 + day_offset)
            day_name = date_obj.strftime("%A")

            night_shift = "Emergency"

            # Saturday fully Emergency
            if day_name == "Saturday":
                schedule.append({
                    "Date": date_obj.strftime("%Y-%m-%d"),
                    "Day": day_name,
                    "9 AM - 5 PM": "Emergency",
                    "5 PM - 9 PM": "Emergency",
                    "9 PM - 1 AM": "Emergency",
                    "OFF": ", ".join(agents)
                })
                continue

            # Friday Morning fixed
            if day_name == "Friday":
                morning_shift = ["Nour", "Iheb"]
                afternoon_shift = select_afternoon_agent(agents, morning_shift, week)
            # Sunday Morning alternates
            elif day_name == "Sunday":
                morning_shift = [sunday_morning_agent(week)]
                afternoon_shift = select_afternoon_agent(agents, morning_shift, week)
            else:
                # Monday to Thursday use 3-person rotation
                morning_shift = rotate_agents(agents, week, 3)
                afternoon_shift = select_afternoon_agent(agents, morning_shift, week)

            # Calculate OFF
            working_agents = set(morning_shift)
            if afternoon_shift in agents:
                working_agents.add(afternoon_shift)

            off_agents = [agent for agent in agents if agent not in working_agents]
            off_shift = ", ".join(off_agents) if off_agents else ""

            schedule.append({
                "Date": date_obj.strftime("%Y-%m-%d"),
                "Day": day_name,
                "9 AM - 5 PM": ", ".join(morning_shift),
                "5 PM - 9 PM": afternoon_shift,
                "9 PM - 1 AM": night_shift,
                "OFF": off_shift
            })

    df = pd.DataFrame(schedule)
    return df


# Calculate working hours summary
def calculate_summary(schedule_df):
    summary = {agent: {"Working hours": 0, "4 hours/day": 0, "8 hours/day": 0, "OFF": 0} for agent in agents}

    for _, row in schedule_df.iterrows():
        day = row["Day"]

        if day == "Saturday":
            for agent in agents:
                summary[agent]["OFF"] += 1
            continue

        # Morning shift
        morning_agents = row["9 AM - 5 PM"].split(", ") if row["9 AM - 5 PM"] != "Emergency" else []
        for agent in morning_agents:
            if agent in agents:
                summary[agent]["Working hours"] += 8
                summary[agent]["8 hours/day"] += 1

        # Afternoon shift
        if row["5 PM - 9 PM"] in agents:
            agent = row["5 PM - 9 PM"]
            summary[agent]["Working hours"] += 4
            summary[agent]["4 hours/day"] += 1

        # OFF count
        off_agents = row["OFF"].split(", ") if row["OFF"] else []
        for agent in off_agents:
            if agent in agents:
                summary[agent]["OFF"] += 1

    df_summary = pd.DataFrame.from_dict(summary, orient="index")
    df_summary = df_summary.reset_index().rename(columns={"index": "Agent"})
    return df_summary


# Sidebar inputs
st.sidebar.header("📅 Schedule Settings")
start_date = st.sidebar.date_input("Start Date", value=datetime.today())

if isinstance(start_date, datetime):
    start_date = start_date.date()

# Calculate number of weeks until year end
year_end = date(start_date.year, 12, 31)
days_until_end = (year_end - start_date).days + 1
num_weeks = (days_until_end + 6) // 7  # Round up to full weeks

# Generate schedule
if st.sidebar.button("Generate Schedule"):
    schedule_df = generate_schedule(str(start_date), num_weeks)
    summary_df = calculate_summary(schedule_df)

    st.subheader("📋 Generated Shift Schedule")
    st.dataframe(schedule_df, use_container_width=True, hide_index=True)

    st.subheader("📊 Working Hours Summary")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.success("✅ Schedule and summary generated successfully!")

else:
    st.info("⬅️ Set the start date and click **Generate Schedule**.")


st.markdown("""
---
💡 **Rules Applied:**  
- 🔥 **9 PM – 1 AM is always "Emergency" (no working hours).**  
- 🔥 **Saturday is fully "Emergency" (OFF for all).**  
- 🔥 **Friday Morning:** Fixed to **Nour & Iheb only.**  
- 🔄 **Sunday Morning:** Alternates weekly between **Djelloul** and **Abdennour.**  
- 🔄 Monday–Thursday Morning → **3 agents rotating by week.**  
- 🔄 **Afternoon shift cannot be assigned to someone who worked morning.**  
- 🕒 **9 AM – 5 PM = 8 hours**, **5 PM – 9 PM = 4 hours**, **Night = Emergency (0 hours)**.  
- 🛑 **OFF** is automatically assigned for agents not scheduled that day.  
""")