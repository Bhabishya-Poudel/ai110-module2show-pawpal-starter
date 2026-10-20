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

## ✨ Features

- **Priority-based daily plan:** `Scheduler.generatePlan()` fits tasks into the owner's available minutes, highest priority first. A task that doesn't fit is skipped, and the scheduler keeps trying smaller ones after it.
- **Preferred time of day:** the plan starts at 08:00 (morning), 13:00 (afternoon), or 18:00 (evening). Nothing is allowed to run past midnight.
- **Explained plans:** every planned task gets a reason, every skipped task says why it was skipped, and `explainPlan()` turns both into readable text.
- **Sorting by time:** `Scheduler.sort_by_time()` orders tasks by due date and "HH:MM" time, with untimed tasks last.
- **Smart tie-breaking:** when priorities are equal, the earlier due time goes first, then tasks for the same pet stay together, then shorter tasks go first so more of them fit.
- **Filtering:** `Scheduler.filter_tasks()` narrows tasks by pet and/or completion status.
- **Conflict warnings:** `Scheduler.detect_conflicts()` warns when two or more pending tasks share the same date and time, for one pet or different pets. It returns messages and never crashes the program.
- **Daily and weekly recurrence:** finishing a repeating task with `Scheduler.mark_task_complete()` adds the next one (+1 day or +7 days) to the same pet. Overdue tasks repeat from today, and finishing a task twice doesn't create a duplicate.
- **Next free slot (stretch):** `Scheduler.find_next_available_slot()` finds the earliest time a task of a given length fits without overlapping any timed task, and returns nothing if it would run past midnight.
- **Saved data (stretch):** `Owner.save_to_json()` and `Owner.load_from_json()` keep my pets and tasks in `data.json` between runs. See the Data Persistence section.
- **Input validation:** bad priorities, durations, times, dates, and frequencies are rejected with a clear message when the task is created.

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

## 💾 Data Persistence

My pets and tasks are saved to `data.json` so they are still there the next time I open the app.

**How it works**

1. When the app opens, it looks for `data.json` next to `app.py`. If the file is there, `Owner.load_from_json()` rebuilds the owner, their pets, and every task from it.
2. After every change (creating the owner, adding a pet, adding a task, marking a task complete), the app calls `Owner.save_to_json()` to write the file again.
3. "Start over" deletes `data.json`. Without that, the saved data would just load back in.

**Converting objects to JSON.** I used my own dictionary conversion instead of a library like marshmallow, because the objects are small. `Task`, `Pet`, and `Owner` each have a `to_dict()` that returns plain Python types, and `Task.from_dict()` builds a task back from a dictionary. Dates are saved as ISO text ("2026-10-21"). I don't save `petName`, `startTime`, or `reason`, because the scheduler fills those in again every time it builds a plan.

**Safety.**
- Loading goes through the same checks as typing a value in, so a hand-edited file with a bad priority, duration, time, or date is rejected with a `ValueError` instead of breaking the app later.
- A missing file raises `FileNotFoundError`. A corrupt or incomplete file raises `ValueError`, and the app shows a warning and starts fresh instead of crashing.
- Saving writes to a temporary file first and then moves it into place, so a crash in the middle of a save can't leave a half-written `data.json`.
- `data.json` is listed in `.gitignore` because it is personal data that changes every time I use the app.

**Files modified for this feature:** `pawpal_system.py` (the `to_dict`, `from_dict`, `save_to_json`, and `load_from_json` methods), `app.py` (loading on startup, saving after each change, "Start over"), `main.py` (a save and reload demo that uses a temporary file, so it never touches my real `data.json`), `tests/test_pawpal.py` (the round trip and error cases), `.gitignore`, `diagrams/uml_final.mmd`, and this README.

## 📐 System Architecture (UML)

The final class diagram is in `diagrams/uml_final.mmd` (Mermaid source). Compared to my first draft (`diagrams/uml.mmd`), the final version adds:

- `Task`: `dueTime`, `frequency`, `dueDate`, plus `nextOccurrence()` which creates the next copy of a repeating task, and `to_dict()` / `from_dict()` for saving.
- `Pet`: an `owner` back-reference, `addTask()` (which asks the owner to check the task), and `to_dict()`.
- `Owner`: `getTasksByPet()`, `getTasksByStatus()`, the private `_checkNewTask()` validation, and `save_to_json()` / `load_from_json()`.
- `Scheduler`: `sort_by_time()`, `filter_tasks()`, `mark_task_complete()`, `detect_conflicts()`, `find_next_available_slot()`, `getPlanForPet()`, and a `generated` flag.

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

My 54 tests are in `tests/test_pawpal.py`. They check these things:

- Planning: tasks are picked by priority, the plan never goes over the owner's available minutes, start times are correct, skipped tasks get a reason, and replanning clears the old start times.
- Sorting: tasks come back in "HH:MM" order with untimed tasks last. Due time only breaks ties and never beats priority, and equal-priority tasks stay grouped by pet.
- Filtering: by pet name and/or completion status. This includes an unknown pet, a pet with no tasks, different capitalization, and two pets with the same name.
- Recurring tasks: finishing a daily task makes a new one for the next day, and a weekly task adds 7 days. I also tested year end, leap day, an overdue task, a task finished early, finishing twice (no duplicate), and a task that isn't the owner's.
- Conflict detection: a warning when two or more pending tasks have the same date and time, for one pet or different pets. Untimed, completed, and different-date tasks are ignored.
- Validation: bad priority, duration, due time, due date, and frequency values are rejected, and one task can't be given to two pets.
- Next free slot: the earliest gap that fits, skipping busy blocks and merging overlapping ones. Edge cases: completed, untimed, and other-day tasks are ignored, a slot that would run past midnight returns nothing, and bad input is rejected.
- Saving and loading: a full round trip keeps every field, a loaded owner plans the same as the original, saving leaves no temp files, and a missing file, corrupt JSON, missing keys, and hand-edited bad values all give a clear error.

Output from a successful run:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.15, pytest-9.1.1, pluggy-1.7.0
rootdir: /Users/swapnilkafle/CodePath/ai110-module2show-pawpal-starter
plugins: anyio-4.15.1
collected 54 items

tests/test_pawpal.py ................................................... [ 94%]
...                                                                      [100%]

============================== 54 passed in 0.03s ==============================
```

Confidence level: 4 out of 5 stars (★★★★☆). All 54 tests pass and they cover normal use and unusual input like empty owners, overdue dates, leap days, and duplicate times. I didn't give it 5 stars for three reasons. Conflict detection only matches identical times, so it misses a 30-minute task at 09:00 and another at 09:15. The Streamlit app (`app.py`) has no automatic tests. And the checks only run when objects are created, so changing a field directly afterwards isn't checked.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders by due date, then "HH:MM" due time; tasks with no time go last |
| Priority tie-breaking | `Scheduler.generatePlan()` | Within a priority: earlier due time, then same pet together, then shorter first |
| Filtering | `Scheduler.filter_tasks()`, `Owner.getTasksByPet()`, `Owner.getTasksByStatus()`, `Scheduler.getPlanForPet()` | By pet name and/or completed status |
| Conflict handling | `Scheduler.detect_conflicts()` | Warns when 2+ pending tasks share the same date and time |
| Recurring tasks | `Scheduler.mark_task_complete()`, `Task.nextOccurrence()` | `daily` = +1 day, `weekly` = +7 days |
| Next free slot | `Scheduler.find_next_available_slot()` | Earliest gap that fits a task of N minutes, avoiding timed tasks |

Sorting: `Scheduler.sort_by_time()` uses `sorted()` with a lambda as the key. I store `dueTime` as zero-padded "HH:MM" (so "7:30" becomes "07:30"), which means comparing the strings gives the same order as comparing the times.

Filtering: `Scheduler.filter_tasks(pet_name=None, completed=None)` narrows the owner's tasks by pet (not case sensitive) and/or by completion status. If a filter is left as `None` it is ignored. The task table in the Streamlit app uses the same filters.

Conflict detection: `Scheduler.detect_conflicts()` groups the pending tasks by date and time and returns a list of warning messages, one for each clash. It works for the same pet or different pets. It returns messages instead of raising an error, so the program keeps running. It only matches identical times and doesn't check overlapping durations (see section 2b in `reflection.md`).

Recurring tasks: a `Task` can have `frequency="daily"` or `"weekly"`. When I finish one with `Scheduler.mark_task_complete(task)`, it marks the task done and adds a new copy to the same pet, with the due date moved forward using `datetime.timedelta`. If the task has no `dueDate`, today's date is used. If the task is overdue, the next copy counts from today instead of the old date. Finishing the same task twice doesn't make a second copy. Calling `Task.mark_complete()` directly only flips the flag and doesn't make the next copy, so `mark_task_complete()` is the one to use. `generatePlan()` leaves out tasks due after today, so tomorrow's copy doesn't show up in today's plan.

Next free slot: `Scheduler.find_next_available_slot(duration, day=None, after=None)` is my extra algorithm. It treats every pending task that has a time as a busy block (its time plus its duration), sorts the blocks, and sweeps through them with a cursor that starts at the owner's preferred start time (or at `after`). If the gap before the next block is big enough, that's the answer. Otherwise the cursor jumps to the end of the block. Overlapping blocks are handled because the cursor only moves forward (it uses `max`). It returns `None` if the task would run past midnight, and it ignores completed tasks, untimed tasks, and tasks on other days. In the app it's in the "Find a free time slot" box, which helps when I need somewhere to move a task that has a conflict.

In the Streamlit app (`app.py`), the Tasks section shows these features. Conflicts appear as a `st.warning` right above the task list, naming the time and both tasks and pets, with a tip to change one task's time. The task table is sorted with `sort_by_time()` and can be filtered by pet and status. A "Mark complete" form uses `mark_task_complete()`, so finishing a daily or weekly task shows a `st.success` message saying when the next one was added. After I generate a schedule, a summary says how many minutes were used, and a short warning reminds me about any conflicts. Plan start times come from my available minutes, so a time I enter on a task affects ordering and conflict checks but not the plan's start time.

Run `python3 main.py` to see sorting, filtering, recurrence, and a conflict warning in the terminal.

## 📸 Demo Walkthrough

### What the app lets you do

Run the app with `streamlit run app.py`. The page has four parts, top to bottom:

1. **Owner:** enter my name, the minutes I have today, and a preferred time of day (morning, afternoon, or evening). A green message confirms the plan start time and how many minutes fit before midnight. "Start over" resets everything.
2. **Pets:** add a pet with a name, species, breed, and age. A table lists my pets and how many tasks each has.
3. **Tasks:** add a task for a pet with a title, duration, priority, an optional time (HH:MM), and how often it repeats (once, daily, or weekly). Below the form I can filter the task list by pet and status, and mark a task complete.
4. **Build Schedule:** press "Generate schedule" to see today's plan with start times, the reason for each task, and a list of skipped tasks.

### Example workflow

1. Create an owner: "Jordan", 120 minutes, morning.
2. Add two pets: Milo (cat) and Luna (dog).
3. Add tasks out of order: Milo's "Evening meds" at 18:00 (daily), Luna's "Vet call" at 09:00, and Milo's "Nail trim" at 9:00.
4. A yellow warning appears above the task list: both "Nail trim" and "Vet call" are at 09:00, with a tip to change one time.
5. The task table is already sorted by time, even though I added the tasks in a different order. I switch "Show pet" to Luna to see only her tasks.
6. Mark "Evening meds" complete. A green message says the next daily "Evening meds" was added for tomorrow, and it shows up in the table.
7. Press "Generate schedule" to see today's plan, a summary of the minutes used, and a short reminder about the conflict.

### Scheduler behaviors shown

- **Sorting:** tasks are listed by date and time no matter what order I added them.
- **Filtering:** by pet and by pending or completed status.
- **Conflict warnings:** two tasks at the same time produce a warning that names both tasks and pets.
- **Recurrence:** completing a daily or weekly task creates the next one automatically.
- **Priority planning:** high-priority tasks are scheduled first, and tasks that don't fit are skipped with a reason.

### Sample CLI output

Output from `python3 main.py`. The first part is the priority plan for Sam. The second part is the smarter scheduling demo for Jordan, with tasks added out of order, filtered, one daily task completed, two tasks at 09:00 flagged as a conflict, the next free slot, and a save and reload. The dates shown are from the day I ran it.

```
Plan for Sam (60 min available):
- 08:00 Morning walk (Rex, 30 min): high priority, fits in the morning schedule
- 08:30 Play session (Rex, 20 min): medium priority, fits in the morning schedule
Skipped:
- Bathing (Queency): needs 60 min but only 30 min left
- Brush coat (Rex): needs 15 min but only 10 min left

Sorted by time:
  today 07:30  Breakfast (Milo, pending)
  today 09:00  Nail trim (Milo, pending)
  today 09:00  Vet call (Luna, pending)
  today 18:00  Evening meds (Milo, pending)
  today --:--  Park trip (Luna, pending)

Milo's tasks (breakfast done, tomorrow's copy added):
  today 18:00  Evening meds (Milo, pending)
  today 07:30  Breakfast (Milo, done)
  today 09:00  Nail trim (Milo, pending)
  2026-10-21 07:30  Breakfast (Milo, pending)

Pending only:
  today 18:00  Evening meds (Milo, pending)
  today 09:00  Nail trim (Milo, pending)
  2026-10-21 07:30  Breakfast (Milo, pending)
  today 09:00  Vet call (Luna, pending)
  today --:--  Park trip (Luna, pending)

Completed only:
  today 07:30  Breakfast (Milo, done)

Conflict check:
  WARNING: Conflict at 2026-10-20 09:00: Nail trim (Milo), Vet call (Luna)

Next free slot (30 min), starting at the morning start: 08:00
Next free slot (30 min), searching from 09:00: 09:15

Saved and reloaded Jordan: 2 pets, 6 tasks (original had 6).
```

I haven't added a screenshot, so the steps above describe what the app shows.
