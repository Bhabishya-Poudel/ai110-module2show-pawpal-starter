from pawpal_system import Owner, Pet, Task


def test_mark_complete_changes_task_status():
    task = Task("Morning walk", 30, "high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_adding_task_increases_pet_task_count():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addPet(rex)
    assert len(rex.tasks) == 0

    owner.addTask(rex, Task("Morning walk", 30, "high"))
    assert len(rex.tasks) == 1

    owner.addTask(rex, Task("Brush coat", 15, "low"))
    assert len(rex.tasks) == 2


def test_adding_task_through_pet_increases_pet_task_count():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addPet(rex)

    rex.addTask(Task("Morning walk", 30, "high"))

    assert len(rex.tasks) == 1
    assert owner.getAllTasks()[0].petName == "Rex"
