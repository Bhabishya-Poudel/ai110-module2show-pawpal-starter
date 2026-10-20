# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🛠️ Implementation Summary

The backend in `pawpal_system.py` is built from four classes that nest: an `Owner` has many `Pets`, a `Pet` has many `Tasks`, and a `Scheduler` holds one `Owner`. `Owner` and `Pet` expose `addPet` and `addTask`, and `Owner.getAllTasks()` gathers every pet's tasks into one list so the `Scheduler` never has to search through pets itself. `Task`, `Pet` and `Owner` validate their input when created (priority, duration, time preference, and nothing running past midnight), so bad values fail early with a clear message. `Scheduler.generatePlan()` drops completed tasks, sorts the rest by priority (shorter first on ties), and fits them into the owner's available minutes starting at the preferred time of day. Tasks that don't fit go into a `skipped` list, each with a reason, and `explainPlan()` turns the plan and skipped lists into readable text.

## 🖥️ Sample Output

Output from running `python3 main.py`. Sam has 60 minutes available with a morning preference and two dogs (Rex and Queency) with four tasks in total. Only the fiting tasks are done, so the rest are skipped and the reason for each is shown:

Plan for Sam (60 min available):
- 08:00 Morning walk (Rex, 30 min): high priority, fits in the morning schedule
- 08:30 Play session (Rex, 20 min): medium priority, fits in the morning schedule
Skipped:
- Bathing (Queency): needs 60 min but only 30 min left
- Brush coat (Rex): needs 15 min but only 10 min left

## 🧪 Testing PawPal+

Activate the virtual environment, then run the tests from the project folder:

```bash
source .venv/bin/activate
python -m pytest
```

The 39 tests in `tests/test_pawpal.py` cover:

- **Planning:** tasks are chosen by priority, the plan never exceeds the owner's available minutes, start times are right, skipped tasks get a reason, and replanning clears old start times.
- **Sorting:** tasks come out in chronological "HH:MM" order, untimed tasks go last, and due time breaks ties but never beats priority. Equal-priority tasks stay grouped by pet.
- **Filtering:** by pet name and/or completion status, including an unknown pet, a pet with no tasks, different capitalization, and two pets with the same name.
- **Recurring tasks:** completing a daily task creates one for the next day and a weekly task +7 days. Edge cases: year end, leap day, an overdue task, a task finished early, completing twice (no duplicate), and a task that isn't the owner's.
- **Conflict detection:** a warning when two or more pending tasks share the same date and time (same pet or different pets). Untimed, completed, and different-date tasks are ignored.
- **Validation:** bad priority, duration, due time, due date, and frequency values are rejected, and the same task can't be given to two pets.

Output of a successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/swapnilkafle/CodePath/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 39 items

tests/test_pawpal.py .......................................             [100%]

============================== 39 passed in 0.02s ==============================
```

**Confidence level: ★★★★☆ (4 out of 5).** All 39 tests pass, and they cover both normal use and unusual input (empty owners, overdue and leap-day dates, duplicate times). I'm not giving 5 because: conflict detection only matches identical times and misses partial overlaps (such as a 30-minute task at 09:00 and another at 09:15), the Streamlit interface (`app.py`) has not been tested automatically, and the checks only run when objects are created, so changing a field directly afterwards isn't re-checked.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders by due date, then "HH:MM" due time; tasks with no time go last |
| Priority tie-breaking | `Scheduler.generatePlan()` | Within a priority: earlier due time, then same pet together, then shorter first |
| Filtering | `Scheduler.filter_tasks()`, `Owner.getTasksByPet()`, `Owner.getTasksByStatus()`, `Scheduler.getPlanForPet()` | By pet name and/or completed status |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns when 2+ pending tasks share the same date and time |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.nextOccurrence()` | `daily` = +1 day, `weekly` = +7 days |

**Sorting.** `Scheduler.sort_by_time()` uses `sorted()` with a lambda key. `Task` stores `dueTime` as zero-padded "HH:MM" (so "7:30" becomes "07:30"), which means comparing the strings is the same as comparing the times.

**Filtering.** `Scheduler.filter_tasks(pet_name=None, completed=None)` narrows the owner's tasks by pet (case-insensitive) and/or by completion status. A filter left as `None` is ignored. The Streamlit task table uses the same filters.

**Conflict detection.** `Scheduler.detect_conflicts()` groups pending tasks by (date, time) and returns a list of warning strings, one per clash, for the same pet or different pets. It returns messages instead of raising, so the app keeps running. It only matches identical times and does not check overlapping durations (see `reflection.md`, section 2b).

**Recurring tasks.** A `Task` can have `frequency="daily"` or `"weekly"`. Completing it with `Scheduler.mark_task_complete(task)` marks it done and adds a new copy to the same pet, with the due date moved forward using `datetime.timedelta` (today's date is used if the task has no `dueDate`). If the task is overdue, the next copy is counted from today instead of from the old date. Completing a task twice does not create a second copy. Calling `Task.mark_complete()` directly only flips the flag and does not create the next copy; use `mark_task_complete()` for that. `generatePlan()` leaves out tasks due after today, so tomorrow's copy doesn't appear in today's plan.

Run `python3 main.py` to see sorting, filtering, recurrence and a conflict warning in the terminal.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
