from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


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


# --- sorting, filtering, and grouping -----------------------------------


def _names(tasks):
    return [t.title for t in tasks]


def test_earlier_due_time_wins_priority_tie():
    owner = Owner("Sam", 120, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addTask(rex, Task("No due", 10, "high"))
    owner.addTask(rex, Task("Due late", 10, "high", dueTime="17:00"))
    owner.addTask(rex, Task("Due early", 10, "high", dueTime="09:00"))

    plan = Scheduler(owner)
    plan.generatePlan()

    assert _names(plan.plan) == ["Due early", "Due late", "No due"]


def test_due_time_never_beats_priority():
    owner = Owner("Sam", 120, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addTask(rex, Task("Urgent play", 10, "low", dueTime="08:30"))
    owner.addTask(rex, Task("Walk", 10, "high"))

    plan = Scheduler(owner)
    plan.generatePlan()

    assert _names(plan.plan) == ["Walk", "Urgent play"]


def test_equal_priority_tasks_are_grouped_by_pet():
    owner = Owner("Sam", 120, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    kit = Pet("Kit", "cat", "Tabby", 2)
    owner.addPet(rex)
    owner.addPet(kit)
    # Shorter durations alternate between pets if grouping is ignored.
    owner.addTask(rex, Task("Rex long", 30, "medium"))
    owner.addTask(kit, Task("Kit short", 10, "medium"))
    owner.addTask(rex, Task("Rex short", 20, "medium"))
    owner.addTask(kit, Task("Kit long", 25, "medium"))

    plan = Scheduler(owner)
    plan.generatePlan()

    assert [t.petName for t in plan.plan] == ["Rex", "Rex", "Kit", "Kit"]


def test_invalid_due_time_is_rejected():
    for bad in ("9am", "25:00", "12:61", "12"):
        try:
            Task("Walk", 10, "high", dueTime=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should have been rejected")


def test_get_tasks_by_pet_and_status():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    kit = Pet("Kit", "cat", "Tabby", 2)
    done = Task("Walk", 10, "high")
    owner.addTask(rex, done)
    owner.addTask(rex, Task("Brush", 10, "low"))
    owner.addTask(kit, Task("Feed", 5, "high"))
    done.mark_complete()

    assert _names(owner.getTasksByPet("rex")) == ["Walk", "Brush"]
    assert _names(owner.getTasksByStatus(True)) == ["Walk"]
    assert _names(owner.getTasksByStatus(False)) == ["Brush", "Feed"]


def test_get_plan_for_pet():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    kit = Pet("Kit", "cat", "Tabby", 2)
    owner.addTask(rex, Task("Walk", 10, "high"))
    owner.addTask(kit, Task("Feed", 5, "high"))

    scheduler = Scheduler(owner)
    scheduler.generatePlan()

    assert _names(scheduler.getPlanForPet("Kit")) == ["Feed"]


# --- smarter scheduling: sort, filter, recurrence, conflicts -------------


def _owner_with_pet():
    owner = Owner("Sam", 120, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addPet(rex)
    return owner, rex


def test_sort_by_time_orders_hhmm_and_puts_untimed_last():
    owner, rex = _owner_with_pet()
    owner.addTask(rex, Task("Evening", 5, "low", dueTime="18:00"))
    owner.addTask(rex, Task("Untimed", 5, "low"))
    owner.addTask(rex, Task("Early", 5, "low", dueTime="7:05"))  # unpadded input
    owner.addTask(rex, Task("Noon", 5, "low", dueTime="12:00"))

    assert _names(Scheduler(owner).sort_by_time()) == ["Early", "Noon", "Evening", "Untimed"]


def test_filter_tasks_by_pet_and_status():
    owner, rex = _owner_with_pet()
    kit = Pet("Kit", "cat", "Tabby", 2)
    done = Task("Walk", 10, "high")
    owner.addTask(rex, done)
    owner.addTask(kit, Task("Feed", 5, "high"))
    done.mark_complete()
    scheduler = Scheduler(owner)

    assert _names(scheduler.filter_tasks()) == ["Walk", "Feed"]
    assert _names(scheduler.filter_tasks(pet_name="kit")) == ["Feed"]
    assert _names(scheduler.filter_tasks(completed=True)) == ["Walk"]
    assert scheduler.filter_tasks(pet_name="Kit", completed=True) == []


def test_completing_daily_task_creates_task_for_tomorrow():
    owner, rex = _owner_with_pet()
    meds = Task("Meds", 5, "high", frequency="daily")  # no dueDate means "today"
    owner.addTask(rex, meds)

    new = Scheduler(owner).mark_task_complete(meds)

    assert meds.completed is True
    assert new.dueDate == date.today() + timedelta(days=1)
    assert new.completed is False and new in rex.tasks and new.petName == "Rex"


def test_daily_task_crosses_a_year_boundary():
    # A far-future date, so it is never "overdue" no matter when the test runs.
    owner, rex = _owner_with_pet()
    meds = Task("Meds", 5, "high", frequency="daily", dueDate=date(2099, 12, 31))
    owner.addTask(rex, meds)

    assert Scheduler(owner).mark_task_complete(meds).dueDate == date(2100, 1, 1)


def test_completing_weekly_task_adds_seven_days_and_defaults_to_today():
    owner, rex = _owner_with_pet()
    bath = Task("Bath", 20, "low", frequency="weekly")
    owner.addTask(rex, bath)

    new = Scheduler(owner).mark_task_complete(bath)

    assert new.dueDate == date.today() + timedelta(days=7)


def test_non_recurring_or_already_completed_task_creates_nothing():
    owner, rex = _owner_with_pet()
    once = Task("Vet", 30, "high")
    daily = Task("Meds", 5, "high", frequency="daily")
    owner.addTask(rex, once)
    owner.addTask(rex, daily)
    scheduler = Scheduler(owner)

    assert scheduler.mark_task_complete(once) is None
    assert scheduler.mark_task_complete(daily) is not None
    assert scheduler.mark_task_complete(daily) is None  # no duplicate
    assert len(rex.tasks) == 3


def test_future_occurrence_is_not_planned_today():
    owner, rex = _owner_with_pet()
    meds = Task("Meds", 5, "high", frequency="daily")
    owner.addTask(rex, meds)
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(meds)

    scheduler.generatePlan()

    assert scheduler.plan == [] and scheduler.skipped == []


def test_invalid_frequency_is_rejected():
    try:
        Task("Walk", 10, "high", frequency="monthly")
    except ValueError:
        return
    raise AssertionError("frequency 'monthly' should have been rejected")


def test_detect_conflicts_warns_for_same_time_across_pets():
    owner, rex = _owner_with_pet()
    kit = Pet("Kit", "cat", "Tabby", 2)
    owner.addTask(rex, Task("Walk", 10, "high", dueTime="09:00"))
    owner.addTask(kit, Task("Feed", 5, "high", dueTime="9:00"))
    owner.addTask(kit, Task("Play", 5, "low", dueTime="10:00"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1
    assert "09:00" in warnings[0] and "Walk (Rex)" in warnings[0] and "Feed (Kit)" in warnings[0]


def test_detect_conflicts_ignores_completed_and_different_dates():
    owner, rex = _owner_with_pet()
    done = Task("Walk", 10, "high", dueTime="09:00")
    owner.addTask(rex, done)
    owner.addTask(rex, Task("Feed", 5, "high", dueTime="09:00"))
    owner.addTask(rex, Task("Meds", 5, "high", dueTime="09:00",
                            dueDate=date.today() + timedelta(days=1)))
    done.mark_complete()

    assert Scheduler(owner).detect_conflicts() == []


# --- edge cases ---------------------------------------------------------


def test_due_date_accepts_iso_string_and_datetime_and_rejects_junk():
    from datetime import datetime

    assert Task("a", 5, "low", dueDate="2026-10-21").dueDate == date(2026, 10, 21)
    assert Task("a", 5, "low", dueDate=datetime(2026, 10, 21, 9, 30)).dueDate == date(2026, 10, 21)
    assert Task("a", 5, "low", dueDate="").dueDate is None
    for bad in (5, "tomorrow", "2026-13-01"):
        try:
            Task("a", 5, "low", dueDate=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should have been rejected")


def test_due_time_edge_formats():
    assert Task("a", 5, "low", dueTime=" 9:5 ").dueTime == "09:05"
    for bad in ("09:00:30", "24:00", "-1:30", "ab:cd", None, 900):
        try:
            Task("a", 5, "low", dueTime=bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad!r} should have been rejected")


def test_overdue_recurring_task_repeats_from_today_not_from_the_past():
    owner, rex = _owner_with_pet()
    meds = Task("Meds", 5, "high", frequency="daily",
                dueDate=date.today() - timedelta(days=7))
    owner.addTask(rex, meds)

    new = Scheduler(owner).mark_task_complete(meds)

    assert new.dueDate == date.today() + timedelta(days=1)


def test_recurring_task_finished_early_keeps_its_slot():
    owner, rex = _owner_with_pet()
    meds = Task("Meds", 5, "high", frequency="daily",
                dueDate=date.today() + timedelta(days=3))
    owner.addTask(rex, meds)

    new = Scheduler(owner).mark_task_complete(meds)

    assert new.dueDate == date.today() + timedelta(days=4)


def test_leap_day_and_chained_completions():
    owner, rex = _owner_with_pet()
    task = Task("a", 5, "low", frequency="daily", dueDate=date(2096, 2, 28))  # 2096 is a leap year
    owner.addTask(rex, task)
    assert Scheduler(owner).mark_task_complete(task).dueDate == date(2096, 2, 29)

    chain = Task("b", 5, "low", frequency="daily")
    owner.addTask(rex, chain)
    scheduler = Scheduler(owner)
    for _ in range(3):
        chain = scheduler.mark_task_complete(chain)
    assert chain.dueDate == date.today() + timedelta(days=3)


def test_failed_recurrence_leaves_task_pending():
    owner, rex = _owner_with_pet()
    last = Task("a", 5, "low", frequency="daily", dueDate=date.max)
    owner.addTask(rex, last)

    try:
        Scheduler(owner).mark_task_complete(last)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError past date.max")

    assert last.completed is False and len(rex.tasks) == 1


def test_complete_task_not_owned_raises_and_changes_nothing():
    owner, rex = _owner_with_pet()
    stray = Task("stray", 5, "low", frequency="daily")

    try:
        Scheduler(owner).mark_task_complete(stray)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")

    assert stray.completed is False


def test_sort_and_filter_on_empty_inputs():
    owner, rex = _owner_with_pet()
    scheduler = Scheduler(owner)

    assert scheduler.sort_by_time() == []
    assert scheduler.sort_by_time([]) == []
    assert scheduler.filter_tasks(pet_name="Nobody") == []


def test_sort_by_time_orders_dates_before_times():
    owner, rex = _owner_with_pet()
    tomorrow = date.today() + timedelta(days=1)
    owner.addTask(rex, Task("tomorrow 08", 5, "low", dueTime="08:00", dueDate=tomorrow))
    owner.addTask(rex, Task("today 20", 5, "low", dueTime="20:00"))

    assert _names(Scheduler(owner).sort_by_time()) == ["today 20", "tomorrow 08"]


def test_filter_by_pet_name_matches_duplicate_names_ignoring_case_and_spaces():
    owner = Owner("Sam", 60, "morning")
    owner.addTask(Pet("Max", "dog", "x", 1), Task("A", 5, "low"))
    owner.addTask(Pet("max", "cat", "y", 1), Task("B", 5, "low"))

    assert _names(Scheduler(owner).filter_tasks(pet_name=" MAX ")) == ["A", "B"]


def test_three_tasks_at_one_time_give_one_warning_and_untimed_never_conflict():
    owner, rex = _owner_with_pet()
    for name in "abc":
        owner.addTask(rex, Task(name, 5, "low", dueTime="09:00"))
    owner.addTask(rex, Task("u1", 5, "low"))
    owner.addTask(rex, Task("u2", 5, "low"))

    warnings = Scheduler(owner).detect_conflicts()

    assert len(warnings) == 1 and all(n in warnings[0] for n in ("a (", "b (", "c ("))


def test_next_occurrence_that_collides_with_existing_task_is_flagged():
    owner, rex = _owner_with_pet()
    tomorrow = date.today() + timedelta(days=1)
    daily = Task("a", 5, "low", dueTime="09:00", frequency="daily")
    owner.addTask(rex, daily)
    owner.addTask(rex, Task("b", 5, "low", dueTime="09:00", dueDate=tomorrow))
    scheduler = Scheduler(owner)
    scheduler.mark_task_complete(daily)

    assert len(scheduler.detect_conflicts()) == 1


def test_due_today_is_planned_and_due_later_is_not_until_that_day():
    owner, rex = _owner_with_pet()
    tomorrow = date.today() + timedelta(days=1)
    owner.addTask(rex, Task("now", 5, "low", dueDate=date.today()))
    owner.addTask(rex, Task("later", 5, "low", dueDate=tomorrow))
    scheduler = Scheduler(owner)

    scheduler.generatePlan()
    assert _names(scheduler.plan) == ["now"]

    scheduler.generatePlan(today=tomorrow)
    assert _names(scheduler.plan) == ["now", "later"]


def test_explain_plan_when_only_future_tasks_exist():
    owner, rex = _owner_with_pet()
    owner.addTask(rex, Task("later", 5, "low", dueDate=date.today() + timedelta(days=1)))
    scheduler = Scheduler(owner)
    scheduler.generatePlan()

    assert "Nothing to schedule" in scheduler.explainPlan()


# --- core planning behaviors: happy paths and empty cases ----------------


def test_plan_fills_available_minutes_by_priority_and_sets_start_times():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addTask(rex, Task("Brush", 15, "low"))
    owner.addTask(rex, Task("Walk", 30, "high"))
    owner.addTask(rex, Task("Play", 20, "medium"))
    scheduler = Scheduler(owner)

    scheduler.generatePlan()

    assert _names(scheduler.plan) == ["Walk", "Play"]
    assert [t.startTime for t in scheduler.plan] == ["08:00", "08:30"]
    assert _names(scheduler.skipped) == ["Brush"]
    assert "only 10 min left" in scheduler.skipped[0].reason


def test_plan_never_exceeds_available_minutes():
    owner = Owner("Sam", 45, "afternoon")
    rex = Pet("Rex", "dog", "Labrador", 3)
    for i, (mins, prio) in enumerate([(30, "high"), (20, "high"), (10, "medium"), (5, "low")]):
        owner.addTask(rex, Task(f"t{i}", mins, prio))
    scheduler = Scheduler(owner)

    scheduler.generatePlan()

    assert sum(t.duration for t in scheduler.plan) <= 45
    assert scheduler.plan[0].startTime == "13:00"


def test_pet_with_no_tasks_and_owner_with_no_pets():
    owner = Owner("Sam", 60, "morning")
    scheduler = Scheduler(owner)
    assert owner.getAllTasks() == []
    assert scheduler.explainPlan().startswith("No plan yet")

    scheduler.generatePlan()
    assert scheduler.plan == [] and scheduler.skipped == []
    assert "Nothing to schedule" in scheduler.explainPlan()

    owner.addPet(Pet("Rex", "dog", "Labrador", 3))  # pet exists but has no tasks
    scheduler.generatePlan()
    assert scheduler.plan == []
    assert scheduler.filter_tasks(pet_name="Rex") == []
    assert scheduler.detect_conflicts() == []


def test_zero_available_minutes_skips_everything():
    owner = Owner("Sam", 0, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    owner.addTask(rex, Task("Walk", 10, "high"))
    scheduler = Scheduler(owner)

    scheduler.generatePlan()

    assert scheduler.plan == [] and _names(scheduler.skipped) == ["Walk"]


def test_completed_tasks_are_left_out_and_replanning_clears_old_times():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    walk = Task("Walk", 30, "high")
    play = Task("Play", 20, "medium")
    owner.addTask(rex, walk)
    owner.addTask(rex, play)
    scheduler = Scheduler(owner)
    scheduler.generatePlan()
    assert walk.startTime == "08:00"

    walk.mark_complete()
    scheduler.generatePlan()

    assert _names(scheduler.plan) == ["Play"]
    assert walk.startTime == "" and play.startTime == "08:00"


def test_same_task_object_cannot_be_given_to_two_pets():
    owner = Owner("Sam", 60, "morning")
    rex = Pet("Rex", "dog", "Labrador", 3)
    kit = Pet("Kit", "cat", "Tabby", 2)
    shared = Task("Walk", 10, "high")
    owner.addTask(rex, shared)

    try:
        owner.addTask(kit, shared)
    except ValueError:
        return
    raise AssertionError("the same task should not be assignable to two pets")


# --- next available slot --------------------------------------------------


def _slot_owner(*timed):
    """An owner with one pet and timed tasks given as (title, minutes, "HH:MM")."""
    owner, rex = _owner_with_pet()
    for title, mins, at in timed:
        owner.addTask(rex, Task(title, mins, "low", dueTime=at))
    return owner, rex, Scheduler(owner)


def test_next_slot_is_the_start_of_the_day_when_nothing_is_booked():
    _, _, scheduler = _slot_owner()
    assert scheduler.find_next_available_slot(30) == "08:00"  # morning start


def test_next_slot_skips_busy_blocks_and_merges_overlaps():
    _, _, scheduler = _slot_owner(("a", 30, "08:00"), ("b", 60, "08:30"), ("c", 10, "09:00"))
    assert scheduler.find_next_available_slot(15) == "09:30"


def test_next_slot_uses_a_gap_between_tasks_only_if_it_is_big_enough():
    _, _, scheduler = _slot_owner(("a", 30, "08:00"), ("b", 20, "08:40"))
    assert scheduler.find_next_available_slot(10) == "08:30"  # 10-minute gap fits
    assert scheduler.find_next_available_slot(11) == "09:00"  # it doesn't


def test_next_slot_honors_after_and_ignores_earlier_blocks():
    _, _, scheduler = _slot_owner(("a", 60, "08:00"))
    assert scheduler.find_next_available_slot(20, after="10:00") == "10:00"
    assert scheduler.find_next_available_slot(20, after="08:30") == "09:00"


def test_next_slot_ignores_completed_untimed_and_other_day_tasks():
    owner, rex, scheduler = _slot_owner(("done", 60, "08:00"))
    rex.tasks[0].mark_complete()
    owner.addTask(rex, Task("untimed", 60, "low"))
    owner.addTask(rex, Task("tomorrow", 60, "low", dueTime="08:00",
                            dueDate=date.today() + timedelta(days=1)))

    assert scheduler.find_next_available_slot(30) == "08:00"
    assert scheduler.find_next_available_slot(30, day=date.today() + timedelta(days=1)) == "09:00"


def test_next_slot_returns_none_when_it_would_run_past_midnight():
    _, _, scheduler = _slot_owner()
    assert scheduler.find_next_available_slot(45, after="23:30") is None
    assert scheduler.find_next_available_slot(30, after="23:30") == "23:30"  # ends exactly at midnight


def test_next_slot_rejects_bad_input():
    _, _, scheduler = _slot_owner()
    for bad in (0, -5, "abc"):
        try:
            scheduler.find_next_available_slot(bad)
        except ValueError:
            continue
        raise AssertionError(f"duration {bad!r} should have been rejected")
    try:
        scheduler.find_next_available_slot(10, after="25:00")
    except ValueError:
        return
    raise AssertionError("bad 'after' time should have been rejected")


# --- saving and loading ---------------------------------------------------


def _saved_owner():
    owner = Owner("Sam", 90, "afternoon")
    rex = Pet("Rex", "dog", "Labrador", 3)
    kit = Pet("Kit", "cat", "Tabby", 2)
    done = Task("Walk", 30, "high", dueTime="9:00", frequency="daily",
                dueDate=date(2099, 1, 2))
    owner.addTask(rex, done)
    owner.addTask(rex, Task("Brush", 15, "low"))
    owner.addTask(kit, Task("Feed", 5, "medium", dueTime="07:30"))
    done.mark_complete()
    return owner


def test_save_and_load_round_trip_keeps_everything(tmp_path):
    path = tmp_path / "data.json"
    original = _saved_owner()

    original.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    assert (loaded.name, loaded.availableMinutes, loaded.timePreferences) == ("Sam", 90, "afternoon")
    assert [(p.name, p.species, p.breed, p.age) for p in loaded.pets] == [
        ("Rex", "dog", "Labrador", 3), ("Kit", "cat", "Tabby", 2)]
    walk = loaded.getTasksByPet("Rex")[0]
    assert (walk.title, walk.duration, walk.priority, walk.completed) == ("Walk", 30, "high", True)
    assert (walk.dueTime, walk.frequency, walk.dueDate) == ("09:00", "daily", date(2099, 1, 2))
    assert _names(loaded.getAllTasks()) == _names(original.getAllTasks())
    assert all(p.owner is loaded for p in loaded.pets)


def test_loaded_owner_plans_the_same_as_the_original(tmp_path):
    path = tmp_path / "data.json"
    original = _saved_owner()
    original.save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    a, b = Scheduler(original), Scheduler(loaded)
    a.generatePlan()
    b.generatePlan()

    assert [(t.title, t.startTime) for t in a.plan] == [(t.title, t.startTime) for t in b.plan]
    assert _names(a.skipped) == _names(b.skipped)


def test_loaded_data_keeps_working_after_load(tmp_path):
    path = tmp_path / "data.json"
    _saved_owner().save_to_json(str(path))
    loaded = Owner.load_from_json(str(path))

    loaded.addTask(loaded.pets[0], Task("New", 5, "low"))
    loaded.save_to_json(str(path))

    assert "New" in _names(Owner.load_from_json(str(path)).getAllTasks())


def test_save_overwrites_and_leaves_no_temp_files(tmp_path):
    path = tmp_path / "data.json"
    owner = _saved_owner()
    owner.save_to_json(str(path))
    owner.save_to_json(str(path))

    assert [f.name for f in tmp_path.iterdir()] == ["data.json"]


def test_load_missing_file_raises_file_not_found(tmp_path):
    try:
        Owner.load_from_json(str(tmp_path / "nope.json"))
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")


def test_save_to_missing_folder_raises_and_creates_nothing(tmp_path):
    try:
        _saved_owner().save_to_json(str(tmp_path / "no_such_folder" / "data.json"))
    except FileNotFoundError:
        assert list(tmp_path.iterdir()) == []
        return
    raise AssertionError("expected FileNotFoundError")


def _load_text(tmp_path, text):
    path = tmp_path / "data.json"
    path.write_text(text, encoding="utf-8")
    return Owner.load_from_json(str(path))


def test_load_rejects_corrupt_and_malformed_files(tmp_path):
    bad_files = [
        "{ not json",
        "",
        "[]",
        '{"name": "Sam"}',
        '{"name": "Sam", "availableMinutes": 60, "timePreferences": "morning", "pets": "x"}',
        '{"name": "Sam", "availableMinutes": 60, "timePreferences": "morning", "pets": [{"name": "Rex"}]}',
    ]
    for text in bad_files:
        try:
            _load_text(tmp_path, text)
        except ValueError:
            continue
        raise AssertionError(f"{text!r} should have been rejected with ValueError")


def test_load_rejects_hand_edited_invalid_values(tmp_path):
    def file_with(task):
        return ('{"name": "Sam", "availableMinutes": 60, "timePreferences": "morning", '
                '"pets": [{"name": "Rex", "species": "dog", "breed": "x", "age": 1, '
                f'"tasks": [{task}]}}]}}')

    for task in (
        '{"title": "a", "duration": -5, "priority": "low"}',
        '{"title": "a", "duration": 10, "priority": "urgent"}',
        '{"title": "a", "duration": 10, "priority": "low", "dueTime": "99:99"}',
        '{"title": "a", "duration": 10, "priority": "low", "dueDate": "next week"}',
        '{"title": "a", "duration": 10, "priority": "low", "frequency": "monthly"}',
        '{"title": "a", "priority": "low"}',
    ):
        try:
            _load_text(tmp_path, file_with(task))
        except ValueError:
            continue
        raise AssertionError(f"{task} should have been rejected")
