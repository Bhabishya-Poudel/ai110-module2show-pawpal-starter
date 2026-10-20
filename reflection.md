# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

My initial UML has four classes that model the owner, their pets, the care tasks, and the scheduling.

Owner: stores the owner's name, available minutes, and time preferences, and holds a list of their pets. It adds pets, adds tasks to a pet, and collects all tasks across pets.

Pet: stores the pet's name, species, breed, and age, and holds that pet's list of tasks.

Task: represents one care activity, with a title, duration, priority, and completed status.

Scheduler: takes an owner, builds the daily plan from their tasks, and explains why it chose that plan.

Owner has many Pets, Pet has many Tasks, and Scheduler uses Owner. Each class has one job.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. A few changes made the scheduler workable:

- Time preferences: Owner.timePreferences started as free string, which the scheduler can't act on. I limited it to `morning`, `afternoon`, or `evening`, each mapped to a plan start time using a dictionary. 

- Priority order: I kept priority as a string to match the UI, but sorting strings alphabetically gives the wrong order (high, low, medium). A `PRIORITY_ORDER` mapping (low = 1, medium = 2, high = 3) fixes the sort.

- Plan details on `Task`:`Task` now holds `startTime` and `reason`, and `Scheduler` keeps `plan` and `skipped` lists. `generatePlan()` fills these in and `explainPlan()` reads them.

- `petName` as a string: Once all tasks are merged into one list, a task no longer shows which pet it belongs to, so Task stores petName. I used the pet's name (text) instead of the Pet object, because if a pet and its tasks pointed at each other, printing them would loop forever.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

The scheduler looks at these things:

- The owner's available minutes. A task that doesn't fit in the time left is skipped.
- Task priority (low, medium, high). Higher priority is planned first.
- The owner's preferred time of day, which sets when the plan starts (08:00, 13:00, or 18:00). Nothing is allowed to run past midnight.
- Whether a task is already completed, and whether it is due later than today.
- A task's due time, and which pet it belongs to. These only break ties between tasks with the same priority.

Time and priority mattered most, because the owner's real problem is not having enough time, so the most important care has to come first. Due time and pet grouping are only tie-breakers on purpose. If a low-priority task could jump ahead of a high-priority one just because it had an earlier time, a plan could skip something important like medication.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

My `Scheduler.detect_conflicts()` only flags tasks that have the exact same date and time. It does not check whether the durations overlap, so a 30-minute walk at 09:00 and a 10-minute task at 09:15 are not reported even though they run into each other.

I kept it this way because I wanted a lightweight check. It makes one pass over the tasks, groups them by date and time, and returns warning messages, which is easy to read and easy to test. For a pet owner, the most useful warning is "you put two things at 9:00". Checking overlaps would need a start and end time for every task and a rule for tasks that are back to back. The downside is that partial overlaps get missed, so that would be the next thing I add.

I also looked at whether `detect_conflicts()` could be simpler. It could be shorter with `itertools.groupby`, but then the grouping hides behind an import and a sort I could easily forget. I kept the `defaultdict` version because I can see the grouping right there. `sort_by_time()` works the same way: it compares the "HH:MM" strings with a lambda instead of parsing them. That only works because `Task` stores `dueTime` zero-padded, so that cleanup is part of the design.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used the AI assistant to understand the design, write the method bodies, and hunt for bugs. The most helpful prompts were the ones where I said what I didn't understand. When I asked how the `Scheduler` should get all tasks from the owner's pets, the answer was that it shouldn't search pets at all: it asks `Owner.getAllTasks()`, and the `Owner` knows how pets store their tasks. That cleared up the fourth class for me. Asking it to "think" about what could break the code was also useful, because it ran the code against 15 edge cases (wrong capitalization, string durations, a negative duration, the same task given to two pets, plans running past midnight) instead of only describing them.

Prompts that were direct and focused on 1 single task instead of "do this do that yes no." Implement this class with a has is relation, etc type of command prompts were useful. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

For the explain() function, AI wanted to add 2 more classes. I rejected that due to added complexity and more reference to classes. I instead asked AI to change the data type of certain attributes within Pet to string to avoid infinite loop of self referencing or referencing to other classes and those classes referencing back. 

I asked AI to break the code itself, think of edge cases, when it corrected the code, retry those edgecases and if it worked, think of a new way to break it.

**What the AI suggested, and what I accepted or rejected:**

- **Accepted:** the implementation of `addPet`, `addTask`, `getAllTasks`, `generatePlan` and `explainPlan`. This includes sorting by `PRIORITY_ORDER` and skipping a task that doesn't fit while still trying later, smaller ones.
- **Rejected:** the AI first made `addTask` raise an error when the pet hadn't been added to the owner. I asked for the pet to be added automatically instead, and it changed that.
- **Accepted:** its list of fixes for the edge cases. These were validation when objects are created (priority, duration, time preference), ignoring a pet that is added twice, clearing old start times when replanning, and a flag so `explainPlan` can tell "no plan yet" from "nothing to schedule".
- **Changed:** the AI's plan for tasks that would run past midnight was to skip them and give a clearer reason. I wanted it blocked and warned about when the value is entered, so `Owner` and `addTask` now reject those values with a message saying what to change. The scheduler's skip stays only as a fallback.
- **Caught:** when I asked for a test of `mark_complete()`, the method didn't exist. The AI added it rather than writing a test for something that wasn't there.

**How I verified it:** I didn't trust the explanations alone. I ran the edge-case script before and after each fix and compared the outputs, ran `main.py` and pasted its real output into the README, and ran the tests with pytest, which now pass (54 passed). Two limits remain. Validation only runs when objects are created or tasks are added, so later direct changes to fields like `owner.timePreferences` aren't re-checked. And the Streamlit interface in `app.py` has no automatic tests, so I only checked that it parses.

**c. AI strategy**

*Which AI features were most effective?* Three things worked best. First, asking the assistant to try to break my code. When I had it probe edge cases against the new features, it found three real bugs I hadn't thought of: a `dueDate` typed as a string crashed the planner, an overdue daily task repeated into the past, and a date past the maximum raised a raw error. Second, having it make changes across several files at once (the scheduler, `app.py`, the tests, and the docs) so they stayed in step with each other. Third, having it run the code and the tests after each change instead of only describing what should happen.

*One suggestion I rejected or changed.* The clearest one is in 3b above. For `explainPlan()` the AI wanted to add two more classes. I said no because it added more classes that reference each other for very little benefit, and I had the attributes changed to plain strings instead, which avoids the infinite self-reference loop. I used the same approach later: for conflict detection I kept the simple exact-time check instead of a full overlap check, and for due time I kept it as a tie-breaker instead of letting it override priority.

*Separate chat sessions.* I worked in phases (design and UML, then the scheduling logic, then tests, then the UI and docs), and finishing one phase before starting the next kept each conversation about one job. When something broke in testing, I knew it was a test problem or a scheduler problem and not a design question. 

*What I learned about being the lead architect.* The AI is fast at writing code, but it doesn't decide what the system should be. I had to decide the classes, what each one is responsible for, which behaviors mattered, and what "done" meant. The AI would happily keep adding things, so my job was to say no to extra complexity and to check its work by running it. The best results came when I gave it one clear task and then verified the result myself.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I picked five core behaviors in `pawpal_system.py` and tested each one with a normal case and an edge case:

1. Planning by priority within the time budget (`generatePlan`): high priority goes first, nothing goes over the owner's available minutes, and tasks that don't fit are skipped with a reason. Edge cases: 0 available minutes, an afternoon start time, and replanning after a task is completed (old start times get cleared).
2. Sorting by time (`sort_by_time`, plus the due-time and same-pet tie-breaks): "HH:MM" order, untimed tasks last, earlier dates before later ones. Edge cases: unpadded input like "7:30", an empty task list, and due time never beating priority.
3. Filtering (`filter_tasks`): by pet, by status, or both. Edge cases: a pet with no tasks, an unknown pet name, different capitalization, and two pets with the same name.
4. Recurring tasks (`mark_task_complete`, `nextOccurrence`): daily adds 1 day and weekly adds 7. Edge cases: year end, leap day, an overdue task, a task finished early, completing twice (no duplicate), a task that doesn't belong to the owner, and a date past the maximum (the task stays pending).
5. Conflict detection (`detect_conflicts`): a warning when two pending tasks share the same date and time, for one pet or two. Edge cases: three tasks at one time give one warning, untimed tasks never conflict, and completed tasks and different dates are ignored.

These matter because the owner trusts whatever plan the scheduler shows. A wrong order or a double-booked time fails quietly, so I wanted tests that would catch it. I also tested empty inputs (an owner with no pets, a pet with no tasks) because a new user will hit those first.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I'm fairly confident in the scheduler, about 4 out of 5. All 54 tests pass, and they cover normal use and unusual input like an owner with no pets, overdue and leap-day dates, and tasks at the same time. I'm not at 5 because the conflict check misses partial overlaps and the Streamlit app has no automatic tests.

If I had more time I would test: overlapping durations (a 30-minute task at 09:00 and another at 09:15), changing a field like `owner.timePreferences` after the object was created, the Streamlit app itself, and a task that was added to a pet before the pet was added to an owner.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with how the pieces fit together: the plan explains itself (every task has a reason), the validation catches bad input early, and the test suite covers both normal use and edge cases. Finding and fixing real bugs through the edge-case checks made me trust the code more.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I would make the plan use the times the owner enters. Right now a task's time only affects ordering and conflict warnings, and the plan's start times come from the available minutes, which can look confusing in the app. I would also check for overlapping durations, let a `Task` know which pet it belongs to so that `mark_complete()` alone could create the next copy, and add automatic tests for the Streamlit app.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The AI can write code quickly, but I am the one responsible for the design. Keeping the classes simple, deciding what each one does, and checking the results by running them mattered more than how fast the code was written. Small, focused requests and testing every change worked much better than asking for everything at once.
