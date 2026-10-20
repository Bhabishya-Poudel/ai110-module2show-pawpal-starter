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

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

`Scheduler.detect_conflicts()` only flags tasks whose due date and time match exactly. It does not check whether durations overlap, so a 30-minute walk at 09:00 and a 10-minute task at 09:15 are not reported even though they collide. I kept it this way because a lightweight check can be one pass over the tasks that groups them by (date, time) and returns warning strings, and it is easy to read and test. A pet owner mostly needs to hear "you put two things at 9:00", and an overlap check would need start/end times for every task, plus a rule for back-to-back tasks. The cost is missed partial overlaps, which would be the next thing to add.

I also reviewed `detect_conflicts()` for simplification. A shorter version is possible by sorting the tasks and using `itertools.groupby`, but it hides the "group by time" idea behind an import and an easy-to-forget sort. I kept the `defaultdict` version because a reader can see the grouping directly. Similarly, `sort_by_time()` compares the "HH:MM" strings with a lambda key instead of parsing them. This is only correct because `Task` stores `dueTime` zero-padded, so that normalization is part of the design.

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

**How I verified it:** I didn't trust the explanations alone. I ran the edge-case script before and after each fix and compared the outputs, ran `main.py` and pasted its real output into the README, and ran the tests with pytest, which pass (3 passed). Two limits remain. Validation only runs when objects are created or tasks are added, so later direct changes to fields like `owner.timePreferences` aren't re-checked. And `app.py` doesn't use these classes yet, so the Streamlit interface isn't tested.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
