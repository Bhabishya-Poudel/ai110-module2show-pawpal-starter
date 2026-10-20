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

To run the tests, I activate the virtual environment and run pytest from the project folder:

```bash
source .venv/bin/activate
python -m pytest
```

My 39 tests are in `tests/test_pawpal.py`. They check these things:

- Planning: tasks are picked by priority, the plan never goes over the owner's available minutes, start times are correct, skipped tasks get a reason, and replanning clears the old start times.
- Sorting: tasks come back in "HH:MM" order with untimed tasks last. Due time only breaks ties and never beats priority, and equal-priority tasks stay grouped by pet.
- Filtering: by pet name and/or completion status. This includes an unknown pet, a pet with no tasks, different capitalization, and two pets with the same name.
- Recurring tasks: finishing a daily task makes a new one for the next day, and a weekly task adds 7 days. I also tested year end, leap day, an overdue task, a task finished early, finishing twice (no duplicate), and a task that isn't the owner's.
- Conflict detection: a warning when two or more pending tasks have the same date and time, for one pet or different pets. Untimed, completed, and different-date tasks are ignored.
- Validation: bad priority, duration, due time, due date, and frequency values are rejected, and one task can't be given to two pets.

Output from a successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/swapnilkafle/CodePath/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 39 items

tests/test_pawpal.py .......................................             [100%]

============================== 39 passed in 0.02s ==============================
```

Confidence level: 4 out of 5 stars (★★★★☆). All 39 tests pass and they cover normal use and unusual input like empty owners, overdue dates, leap days, and duplicate times. I didn't give it 5 stars for three reasons. Conflict detection only matches identical times, so it misses a 30-minute task at 09:00 and another at 09:15. The Streamlit app (`app.py`) has no automatic tests. And the checks only run when objects are created, so changing a field directly afterwards isn't checked.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders by due date, then "HH:MM" due time; tasks with no time go last |
| Priority tie-breaking | `Scheduler.generatePlan()` | Within a priority: earlier due time, then same pet together, then shorter first |
| Filtering | `Scheduler.filter_tasks()`, `Owner.getTasksByPet()`, `Owner.getTasksByStatus()`, `Scheduler.getPlanForPet()` | By pet name and/or completed status |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns when 2+ pending tasks share the same date and time |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.nextOccurrence()` | `daily` = +1 day, `weekly` = +7 days |

Sorting: `Scheduler.sort_by_time()` uses `sorted()` with a lambda as the key. I store `dueTime` as zero-padded "HH:MM" (so "7:30" becomes "07:30"), which means comparing the strings gives the same order as comparing the times.

Filtering: `Scheduler.filter_tasks(pet_name=None, completed=None)` narrows the owner's tasks by pet (not case sensitive) and/or by completion status. If a filter is left as `None` it is ignored. The task table in the Streamlit app uses the same filters.

Conflict detection: `Scheduler.detect_conflicts()` groups the pending tasks by date and time and returns a list of warning messages, one for each clash. It works for the same pet or different pets. It returns messages instead of raising an error, so the program keeps running. It only matches identical times and doesn't check overlapping durations (see section 2b in `reflection.md`).

Recurring tasks: a `Task` can have `frequency="daily"` or `"weekly"`. When I finish one with `Scheduler.mark_task_complete(task)`, it marks the task done and adds a new copy to the same pet, with the due date moved forward using `datetime.timedelta`. If the task has no `dueDate`, today's date is used. If the task is overdue, the next copy counts from today instead of the old date. Finishing the same task twice doesn't make a second copy. Calling `Task.mark_complete()` directly only flips the flag and doesn't make the next copy, so `mark_task_complete()` is the one to use. `generatePlan()` leaves out tasks due after today, so tomorrow's copy doesn't show up in today's plan.

Run `python3 main.py` to see sorting, filtering, recurrence, and a conflict warning in the terminal.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
