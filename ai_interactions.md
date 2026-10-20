# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

I used Claude Code as an agent that could read my project, edit several files, and run commands (the tests, `main.py`, and the Streamlit app's test harness). I gave it one phase at a time and checked what it did by running the results.

**What task did you give the agent?**

1. Suggest small algorithm and logic improvements for the scheduler, then implement three of them: filter helpers, due-time tie-breaking, and grouping tasks by pet.
2. The "Smarter Scheduling" phase: sorting by time, filtering by pet and status, daily and weekly recurring tasks, and conflict detection. Update `main.py` to demo each one, and document them in the README and reflection.
3. Check for edge cases and test them, then write a test suite (sorting, recurrence, and conflict tests at minimum) and fix what fails.
4. Update the Streamlit UI to use the new Scheduler methods, and show conflict warnings in a helpful way.
5. Update the UML to match the final code, polish the README (Features list and Demo Walkthrough), and fill in the reflection.
6. Challenge 1 and Challenge 2: add a "next available slot" algorithm, and save and load the data in `data.json`.

**What did the agent do?**

- Files it modified: `pawpal_system.py`, `app.py`, `main.py`, `tests/test_pawpal.py`, `README.md`, `reflection.md`, `diagrams/uml_final.mmd` (new), `.gitignore`, and this file.
- In `pawpal_system.py` it added `Scheduler.sort_by_time()`, `filter_tasks()`, `mark_task_complete()`, `detect_conflicts()`, `find_next_available_slot()`, and `Owner.save_to_json()` / `load_from_json()`. It also added `Task.nextOccurrence()`, the `dueTime`, `dueDate`, and `frequency` fields with validation, and the `to_dict()` / `from_dict()` conversions.
- It wrote 54 tests and ran them with pytest after each change. It also wrote throwaway scripts to probe about 40 edge cases and to walk through the Streamlit app with Streamlit's test harness (adding a pet, adding tasks, completing a task, saving, reopening, a corrupt file, "Start over").
- It committed and pushed to `main` when I asked.

**What did you have to verify or fix manually?**

- Bugs the edge-case checks found in the agent's first version, which I had it fix: a `dueDate` typed as a string crashed the planner, an overdue daily task repeated into the past, and a date past the maximum raised a raw `OverflowError` (and left the task marked done). It also fixed a misleading "nothing to schedule" message.
- Mistakes in the agent's own checks: a fake-clock test setup that was wrong (9 false failures), a test that expected the wrong date in a chain of completions, and two tests with hard-coded dates that would have started failing after those dates passed. The agent fixed these and re-ran everything with the clock set to 2030 to prove the tests don't depend on today's date.
- The README and reflection first came out in the AI's wording. I had it rewrite my sections in my own language, and I left my AI Collaboration section (3a and 3b) as my own account. It also had to update two numbers in my reflection that were out of date (the test count, and a line saying the app didn't use the classes yet).
- I picked which challenges to do. The agent asked first instead of doing all five.
- Things I still checked by hand: I have not opened the Streamlit app in a browser (only the scripted walkthrough), and I have not rendered the Mermaid diagram.

---

## Prompt Comparison (SF11)

**Task:** the logic for rescheduling a repeating task. When a daily or weekly task is completed, create the next one. I picked this because it has several tricky date cases (overdue tasks, month and year ends, tasks with no date).

**How I ran it.** I gave the exact same prompt to two different Claude models, Haiku and Opus, each with no access to my code and no tools, so the answers came only from the prompt. I could only use Claude models here, so this is a comparison of two models from the same family, not of two different companies' tools. I then ran both answers through the same 12 test cases I use for my own version (the harness and both answers were run outside the project, so my files weren't affected).

The prompt (identical for both): I showed a trimmed `Task` dataclass (`title`, `duration`, `priority`, `completed`, `dueTime`, `frequency` of `""`, `"daily"` or `"weekly"`, and `dueDate`, where `None` means today) and asked: "Write the method `Task.nextOccurrence(self) -> "Task | None"`. When a repeating task is completed, it should return a brand-new Task for the next time it is due (or None if the task doesn't repeat). Daily tasks repeat every day and weekly tasks repeat every 7 days." I asked for the code and a short explanation of how it handles dates.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Haiku (through Claude Code) | Claude Opus (through Claude Code) |
| **Prompt** | The prompt above | The same prompt |
| **Response summary** | A short method: look up 1 or 7 days from a dictionary, return `None` if the frequency isn't in it, start from `dueDate` (or today if it is `None`), and return `dataclasses.replace(self, completed=False, dueDate=base + timedelta(...))`. | Almost the same method, but it lowercases and strips the frequency first, and it stores the steps as `timedelta` objects. It says on purpose that the next date counts from the task's own due date, so the schedule stays fixed even if the task is completed late. |
| **What was useful** | Very short and easy to read. `replace()` copies every other field and also runs the dataclass's validation, so there is no field-by-field copying. Passed the normal cases: next-day, +7 days, year end, leap day, a task with no date, and a task finished early. | Same strengths as Haiku, plus it handles `"Daily"` and `"  daily "` (Haiku quietly treated that as not repeating). Its explanation stated its date rule out loud, which made it easy to see where it differs from what I wanted. |
| **Problems noticed** | Failed 3 of my 12 cases (see below). Also, `replace()` copies the scheduler's `startTime`, `reason`, and `petName` into the new task, because the prompt didn't show those fields. | Failed the same 3 of 12 cases, and has the same `replace()` problem with stale `startTime` and `reason`. |
| **Decision** | Not used. | Not used, but I noted its frequency clean-up idea. |

**The 3 cases both models failed (and my version passes):**
1. An overdue daily task (due 7 days ago) produced a task due 6 days ago, which is already in the past. Both models count from the old due date. For a pet owner, a daily task that is a week late should come back tomorrow, not repeat through a week of missed days.
2. The same problem for an overdue weekly task (due 10 days ago produced a date that was still in the past).
3. A daily task due on the last possible date raised a raw `OverflowError`. Mine raises a clear `ValueError` and leaves the task unfinished.

Both models passed the other 9 (non-repeating returns `None`, daily and weekly with no date, year end, leap day, fields copied correctly, new object and not the original, finished early, and an unknown frequency). My own version passes all 12 once the harness's missing validation is accounted for: it only failed the "monthly" case in my harness because that test class doesn't validate `frequency`, while my real `Task` rejects `"monthly"` when it is created.

I also checked the `replace()` concern on my real `Task`: after the scheduler planned a task, a model-style copy kept `startTime='08:00'` and the old `reason`, while my `nextOccurrence()` gives a clean task with empty values. It's mostly harmless because the next plan resets those fields, but the new task would show a stale start time until then.

**Which approach did you use in your final implementation and why?**

I kept my own `Task.nextOccurrence()`. The two models' answers were nearly identical, and both were shorter and more "Pythonic" thanks to `dataclasses.replace`. But they miss the most realistic case for this app: a task completed late. Counting from `max(dueDate, today)` fixes that, and building the new `Task` explicitly means no stale scheduler data is copied. My version is a few lines longer but I can read each line and know what it does, so I picked readability and correctness over the shortest code. I didn't need Opus's lowercasing of the frequency because `Task.__post_init__` already cleans it up when the task is created.

The main thing I learned: the bigger model was not noticeably better on this task. The prompt was the limiting factor. Neither model asked what should happen for an overdue task, and neither could know my class had extra fields, so my own edge-case tests mattered more than which model wrote the code.
