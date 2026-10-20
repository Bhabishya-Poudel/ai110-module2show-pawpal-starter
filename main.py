from pawpal_system import Owner, Pet, Task, Scheduler, minutesBeforeMidnight

owner  = Owner("Sam", 60, "morning")

rex = Pet("Rex", "dog", "Labrador", 3)
Queency = Pet("Queency", "dog", "Japanese Spitz", 11)

owner.addPet(rex)
owner.addPet(Queency)

owner.addTask(rex, Task("Morning walk", 30, "high"))
owner.addTask(Queency, Task("Bathing", 60, "high"))
owner.addTask(rex, Task("Brush coat", 15, "low"))
owner.addTask(rex, Task("Play session", 20, "medium"))

scheduler = Scheduler(owner)
scheduler.generatePlan()
print(scheduler.explainPlan())

# --- Smarter scheduling demo -------------------------------------------
def show(label, tasks):
    print(f"\n{label}")
    for t in tasks:
        status = "done" if t.completed else "pending"
        print(f"  {t.dueDate or 'today'} {t.dueTime or '--:--'}  {t.title} ({t.petName}, {status})")


jordan = Owner("Jordan", 120, "morning")
milo = Pet("Milo", "cat", "Tabby", 4)
luna = Pet("Luna", "dog", "Beagle", 2)

# Added out of order on purpose, two of them at the same time (09:00).
jordan.addTask(milo, Task("Evening meds", 5, "high", dueTime="18:00", frequency="daily"))
jordan.addTask(luna, Task("Vet call", 15, "medium", dueTime="09:00"))
breakfast = Task("Breakfast", 10, "high", dueTime="7:30", frequency="daily")
jordan.addTask(milo, breakfast)
jordan.addTask(milo, Task("Nail trim", 10, "low", dueTime="09:00"))
jordan.addTask(luna, Task("Park trip", 40, "low"))

jordanScheduler = Scheduler(jordan)

show("Sorted by time:", jordanScheduler.sort_by_time())

jordanScheduler.mark_task_complete(breakfast)
show("Milo's tasks (breakfast done, tomorrow's copy added):", jordanScheduler.filter_tasks(pet_name="Milo"))
show("Pending only:", jordanScheduler.filter_tasks(completed=False))
show("Completed only:", jordanScheduler.filter_tasks(completed=True))

print("\nConflict check:")
for warning in jordanScheduler.detect_conflicts() or ["No conflicts."]:
    print(f"  WARNING: {warning}")
