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

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output (`pytest -v`, with the virtual environment active):

```
test_mark_complete_changes_task_status PASSED
test_adding_task_increases_pet_task_count PASSED
test_adding_task_through_pet_increases_pet_task_count PASSED
test_earlier_due_time_wins_priority_tie PASSED
test_due_time_never_beats_priority PASSED
test_equal_priority_tasks_are_grouped_by_pet PASSED
test_invalid_due_time_is_rejected PASSED
test_get_tasks_by_pet_and_status PASSED
test_get_plan_for_pet PASSED
test_sort_by_time_orders_hhmm_and_puts_untimed_last PASSED
test_filter_tasks_by_pet_and_status PASSED
test_completing_daily_task_creates_task_for_tomorrow PASSED
test_completing_weekly_task_adds_seven_days_and_defaults_to_today PASSED
test_non_recurring_or_already_completed_task_creates_nothing PASSED
test_future_occurrence_is_not_planned_today PASSED
test_invalid_frequency_is_rejected PASSED
test_detect_conflicts_warns_for_same_time_across_pets PASSED
test_detect_conflicts_ignores_completed_and_different_dates PASSED
test_due_date_accepts_iso_string_and_datetime_and_rejects_junk PASSED
test_due_time_edge_formats PASSED
test_overdue_recurring_task_repeats_from_today_not_from_the_past PASSED
test_recurring_task_finished_early_keeps_its_slot PASSED
test_leap_day_and_chained_completions PASSED
test_failed_recurrence_leaves_task_pending PASSED
test_complete_task_not_owned_raises_and_changes_nothing PASSED
test_sort_and_filter_on_empty_inputs PASSED
test_sort_by_time_orders_dates_before_times PASSED
test_filter_by_pet_name_matches_duplicate_names_ignoring_case_and_spaces PASSED
test_three_tasks_at_one_time_give_one_warning_and_untimed_never_conflict PASSED
test_next_occurrence_that_collides_with_existing_task_is_flagged PASSED
test_due_today_is_planned_and_due_later_is_not_until_that_day PASSED
test_explain_plan_when_only_future_tasks_exist PASSED
============================== 32 passed in 0.02s ==============================
```

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
