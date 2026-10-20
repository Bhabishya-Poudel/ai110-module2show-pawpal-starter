import streamlit as st
from pawpal_system import (
    PRIORITY_ORDER,
    TIME_PREFERENCES,
    Owner,
    Pet,
    Scheduler,
    Task,
    minutesBeforeMidnight,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care around the time you have.")

st.divider()

# --- Owner -------------------------------------------------------------
# Streamlit re-runs this whole file on every interaction, so the Owner lives
# in session_state. The form only shows until an Owner has been created.
st.subheader("Owner")

if "owner" not in st.session_state:
    with st.form("owner_form"):
        name = st.text_input("Your name")
        minutes = st.number_input("Minutes available today", min_value=1, value=60)
        pref = st.selectbox("Preferred time of day", list(TIME_PREFERENCES))
        if st.form_submit_button("Create owner"):
            if not name.strip():
                st.error("Please enter your name.")
            else:
                try:
                    st.session_state.owner = Owner(name.strip(), int(minutes), pref)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    st.stop()  # nothing below makes sense without an owner

owner: Owner = st.session_state.owner
st.success(
    f"Planning for {owner.name}: {owner.availableMinutes} min, "
    f"{owner.timePreferences} start ({TIME_PREFERENCES[owner.timePreferences]}). "
    f"Max {minutesBeforeMidnight(owner.timePreferences)} min before midnight."
)
if st.button("Start over"):
    del st.session_state["owner"]
    st.session_state.pop("scheduler", None)
    st.rerun()

st.divider()

# --- Pets --------------------------------------------------------------
st.subheader("Pets")

with st.form("pet_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        pet_name = st.text_input("Pet name")
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col2:
        breed = st.text_input("Breed")
        age = st.number_input("Age (years)", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter the pet's name.")
        else:
            owner.addPet(Pet(pet_name.strip(), species, breed.strip(), int(age)))
            st.session_state.pop("scheduler", None)  # old plan is out of date

if owner.pets:
    st.table(
        [
            {"Name": p.name, "Species": p.species, "Breed": p.breed, "Age": p.age,
             "Tasks": len(p.tasks)}
            for p in owner.pets
        ]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks -------------------------------------------------------------
st.subheader("Tasks")

if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("task_form", clear_on_submit=True):
        petIndex = st.selectbox(
            "Pet", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name
        )
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            title = st.text_input("Task title")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", list(PRIORITY_ORDER), index=2)
        with col4:
            dueTime = st.text_input("Due by (HH:MM, optional)")
        if st.form_submit_button("Add task"):
            if not title.strip():
                st.error("Please enter a task title.")
            else:
                try:
                    owner.pets[petIndex].addTask(Task(title.strip(), int(duration), priority, dueTime=dueTime))
                    st.session_state.pop("scheduler", None)
                except ValueError as e:
                    st.error(str(e))

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        petFilter = st.selectbox("Show pet", ["All"] + [p.name for p in owner.pets])
    with fcol2:
        statusFilter = st.selectbox("Show status", ["All", "Pending", "Completed"])
    tasks = owner.getAllTasks() if petFilter == "All" else owner.getTasksByPet(petFilter)
    if statusFilter != "All":
        tasks = [t for t in tasks if t.completed == (statusFilter == "Completed")]
    if tasks:
        st.table(
            [
                {"Pet": t.petName, "Task": t.title, "Minutes": t.duration,
                 "Priority": t.priority, "Due": t.dueTime or "-"}
                for t in tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ----------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    scheduler.generatePlan()
    st.session_state.scheduler = scheduler

if "scheduler" in st.session_state:
    scheduler = st.session_state.scheduler
    for warning in scheduler.detect_conflicts():
        st.warning(warning)
    if scheduler.plan:
        st.table(
            [
                {"Start": t.startTime, "Pet": t.petName, "Task": t.title,
                 "Minutes": t.duration, "Why": t.reason}
                for t in scheduler.plan
            ]
        )
    if scheduler.skipped:
        st.warning("Skipped:\n" + "\n".join(
            f"- {t.title} ({t.petName}): {t.reason}" for t in scheduler.skipped
        ))
    if not scheduler.plan and not scheduler.skipped:
        st.info(scheduler.explainPlan())
