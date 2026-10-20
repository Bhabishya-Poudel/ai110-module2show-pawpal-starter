import os

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

# --- Saved data --------------------------------------------------------
# Owner, pets and tasks are saved to data.json (next to this file) after every
# change and loaded again the first time the page opens.
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def save() -> None:
    """Save the current owner to data.json, showing an error instead of crashing."""
    try:
        st.session_state.owner.save_to_json(DATA_FILE)
    except OSError as e:
        st.error(f"Couldn't save your data: {e}")


if "owner" not in st.session_state and os.path.exists(DATA_FILE):
    try:
        st.session_state.owner = Owner.load_from_json(DATA_FILE)
        st.toast("Loaded your saved data.")
    except ValueError as e:
        st.warning(f"Couldn't read the saved data ({e}). Starting fresh.")

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
                    save()
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
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)  # otherwise the saved data would load right back
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
            save()
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

# A message saved before st.rerun(), so it still shows after the page refreshes.
if "flash" in st.session_state:
    kind, text = st.session_state.pop("flash")
    getattr(st, kind)(text)

if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    with st.form("task_form", clear_on_submit=True):
        petIndex = st.selectbox(
            "Pet", range(len(owner.pets)), format_func=lambda i: owner.pets[i].name
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            title = st.text_input("Task title")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", list(PRIORITY_ORDER), index=2)
        col4, col5 = st.columns(2)
        with col4:
            dueTime = st.text_input("Time (HH:MM, optional)")
        with col5:
            frequency = st.selectbox("Repeats", ["once", "daily", "weekly"])
        if st.form_submit_button("Add task"):
            if not title.strip():
                st.error("Please enter a task title.")
            else:
                try:
                    owner.pets[petIndex].addTask(
                        Task(title.strip(), int(duration), priority, dueTime=dueTime,
                             frequency="" if frequency == "once" else frequency)
                    )
                    st.session_state.pop("scheduler", None)
                    save()
                except ValueError as e:
                    st.error(str(e))

    # A Scheduler over the owner's current tasks, used for sorting, filtering,
    # completing, and conflict checks. The saved plan lives in session_state.
    view = Scheduler(owner)

    # Conflicts go right above the task list, where the owner can act on them.
    conflicts = view.detect_conflicts()
    for message in conflicts:
        st.warning(f"{message}. Change one task's time so you aren't doing both at once.")
    if not conflicts and any(t.dueTime for t in view.filter_tasks(completed=False)):
        st.success("No time conflicts.")

    fcol1, fcol2 = st.columns(2)
    with fcol1:
        petFilter = st.selectbox("Show pet", ["All"] + [p.name for p in owner.pets])
    with fcol2:
        statusFilter = st.selectbox("Show status", ["All", "Pending", "Completed"])
    shown = view.sort_by_time(
        view.filter_tasks(
            pet_name=None if petFilter == "All" else petFilter,
            completed={"All": None, "Pending": False, "Completed": True}[statusFilter],
        )
    )
    if shown:
        st.caption("Sorted by date and time. Tasks with no time are listed last.")
        st.table(
            [
                {"When": f"{t.dueDate or 'today'} {t.dueTime}".strip(),
                 "Pet": t.petName, "Task": t.title, "Minutes": t.duration,
                 "Priority": t.priority, "Repeats": t.frequency or "once",
                 "Status": "Done" if t.completed else "Pending"}
                for t in shown
            ]
        )
    else:
        st.info("No tasks match. Add one above or change the filters.")

    with st.expander("Find a free time slot"):
        with st.form("slot_form"):
            slotMinutes = st.number_input("How many minutes do you need?", min_value=1, value=30)
            if st.form_submit_button("Find next free slot"):
                slot = view.find_next_available_slot(int(slotMinutes))
                if slot is None:
                    st.warning("No free slot today that finishes before midnight.")
                else:
                    st.info(
                        f"Earliest free {int(slotMinutes)}-minute slot today: {slot} "
                        "(avoids every task that has a time set)."
                    )

    pending = view.filter_tasks(completed=False)
    if pending:
        with st.form("complete_form"):
            doneIndex = st.selectbox(
                "Mark a task complete",
                range(len(pending)),
                format_func=lambda i: (
                    f"{pending[i].title} ({pending[i].petName}) "
                    f"{pending[i].dueTime or 'no time'}"
                ),
            )
            if st.form_submit_button("Mark complete"):
                task = pending[doneIndex]
                nextTask = view.mark_task_complete(task)
                save()
                st.session_state.pop("scheduler", None)
                if nextTask is None:
                    st.session_state.flash = ("success", f"Marked '{task.title}' complete.")
                else:
                    st.session_state.flash = (
                        "success",
                        f"Marked '{task.title}' complete. Added the next {task.frequency} "
                        f"'{task.title}' for {nextTask.dueDate}.",
                    )
                st.rerun()

st.divider()

# --- Schedule ----------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    scheduler.generatePlan()
    st.session_state.scheduler = scheduler

if "scheduler" in st.session_state:
    scheduler = st.session_state.scheduler
    clashes = scheduler.detect_conflicts()
    if clashes:
        st.warning(
            f"{len(clashes)} time conflict(s) in your tasks (see the Tasks section). "
            "The plan below still runs, but you may want to fix them first."
        )
    if scheduler.plan:
        used = sum(t.duration for t in scheduler.plan)
        st.success(
            f"Scheduled {len(scheduler.plan)} task(s): {used} of "
            f"{owner.availableMinutes} minutes used."
        )
        st.table(
            [
                {"Start": t.startTime, "Pet": t.petName, "Task": t.title,
                 "Minutes": t.duration, "Priority": t.priority, "Why": t.reason}
                for t in scheduler.plan
            ]
        )
    if scheduler.skipped:
        st.warning("Skipped:\n" + "\n".join(
            f"- {t.title} ({t.petName}): {t.reason}" for t in scheduler.skipped
        ))
    if not scheduler.plan and not scheduler.skipped:
        st.info(scheduler.explainPlan())
