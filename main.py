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