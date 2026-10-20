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

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

> Fill in once you've implemented scheduling logic.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | | e.g., by priority, duration |
| Filtering | | e.g., skip tasks if time runs out |
| Conflict handling | | e.g., overlapping time slots |
| Recurring tasks | | e.g., daily vs. weekly |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
