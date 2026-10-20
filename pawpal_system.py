import json
import os
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

# Priorities stay as strings (matches the UI dropdown). Sorting alphabetically
# would give high, low, medium, so the scheduler sorts by this mapping instead.
PRIORITY_ORDER = {"low": 1, "medium": 2, "high": 3}

# Allowed values for Owner.timePreferences, mapped to the time the day's plan
# starts when that preference is chosen.
TIME_PREFERENCES = {
    "morning": "08:00",
    "afternoon": "13:00",
    "evening": "18:00",
}

# Allowed values for Task.frequency, mapped to the days until the next occurrence.
RECURRENCE_DAYS = {"daily": 1, "weekly": 7}

MINUTES_PER_DAY = 24 * 60


def minutesBeforeMidnight(timePreference: str) -> int:
    """Minutes between the day's start for this preference and midnight."""
    hour, minute = TIME_PREFERENCES[timePreference].split(":")
    return MINUTES_PER_DAY - (int(hour) * 60 + int(minute))


def _toMinutes(value: str, label: str) -> int:
    """Convert an "HH:MM" string to minutes since midnight, rejecting bad formats."""
    try:
        hour, minute = str(value).strip().split(":")
        hour, minute = int(hour), int(minute)
    except ValueError:
        raise ValueError(f"{label} must look like HH:MM, got {value!r}") from None
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise ValueError(f"{label} must be a time between 00:00 and 23:59, got {value!r}")
    return hour * 60 + minute


def _toHHMM(minutes: int) -> str:
    """Format minutes since midnight as a zero-padded "HH:MM" string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _toInt(value, label: str) -> int:
    """Accept ints and numeric strings (e.g. from a UI text box); reject the rest."""
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a whole number, got {value!r}")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number, got {value!r}") from None


@dataclass
class Task:
    title: str
    duration: int  # minutes
    priority: str  # one of PRIORITY_ORDER's keys
    completed: bool = False
    dueTime: str = ""  # optional "HH:MM"; earlier-due tasks win priority ties
    frequency: str = ""  # "", or one of RECURRENCE_DAYS' keys
    dueDate: date | None = None  # None means "today"
    # Filled in by the scheduler when it builds the plan.
    petName: str = ""
    startTime: str = ""  # "HH:MM"
    reason: str = ""

    def __post_init__(self) -> None:
        """Normalize priority and duration, rejecting invalid values."""
        # Clean and validate here so bad input fails at creation, not mid-plan.
        self.priority = str(self.priority).strip().lower()
        if self.priority not in PRIORITY_ORDER:
            raise ValueError(
                f"priority must be one of {list(PRIORITY_ORDER)}, got {self.priority!r}"
            )
        self.duration = _toInt(self.duration, "duration")
        if self.duration <= 0:
            raise ValueError(f"duration must be positive, got {self.duration}")
        self.dueTime = str(self.dueTime).strip()
        if self.dueTime:
            # Store as zero-padded HH:MM so plain string sorting is time order.
            minutes = _toMinutes(self.dueTime, "dueTime")
            self.dueTime = f"{minutes // 60:02d}:{minutes % 60:02d}"
        self.dueDate = self._toDate(self.dueDate)
        self.frequency = str(self.frequency).strip().lower()
        if self.frequency and self.frequency not in RECURRENCE_DAYS:
            raise ValueError(
                f"frequency must be empty or one of {list(RECURRENCE_DAYS)}, "
                f"got {self.frequency!r}"
            )

    @staticmethod
    def _toDate(value) -> "date | None":
        """Accept None, a date, a datetime, or an ISO "YYYY-MM-DD" string; reject the rest."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime):  # check first: datetime is a date subclass
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value).strip())
        except ValueError:
            raise ValueError(f"dueDate must be a date or YYYY-MM-DD, got {value!r}") from None

    def mark_complete(self) -> None:
        """Mark this task as done.

        This only flips the flag. Use Scheduler.mark_task_complete() to also
        create the next occurrence of a daily or weekly task.
        """
        self.completed = True

    def to_dict(self) -> dict:
        """Return the fields worth saving as plain JSON types.

        petName, startTime and reason are left out on purpose: the scheduler
        fills them in again every time it builds a plan.
        """
        return {
            "title": self.title,
            "duration": self.duration,
            "priority": self.priority,
            "completed": self.completed,
            "dueTime": self.dueTime,
            "frequency": self.frequency,
            "dueDate": self.dueDate.isoformat() if self.dueDate else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuild a Task from to_dict() output, going through the normal validation."""
        return cls(
            data["title"],
            data["duration"],
            data["priority"],
            completed=bool(data.get("completed", False)),
            dueTime=data.get("dueTime", ""),
            frequency=data.get("frequency", ""),
            dueDate=data.get("dueDate"),
        )

    def nextOccurrence(self) -> "Task | None":
        """Return a fresh copy of this task for its next due date, or None if it doesn't repeat.

        The next date is counted from the later of the task's due date and
        today, so an overdue task repeats from today (daily -> tomorrow)
        instead of landing in the past, while one finished early keeps its slot.
        """
        if not self.frequency:
            return None
        # timedelta does the calendar math, so month and year ends are handled.
        base = max(self.dueDate or date.today(), date.today())
        try:
            nextDate = base + timedelta(days=RECURRENCE_DAYS[self.frequency])
        except OverflowError:
            raise ValueError(f"no next {self.frequency} date after {base}") from None
        return Task(
            self.title,
            self.duration,
            self.priority,
            dueTime=self.dueTime,
            frequency=self.frequency,
            dueDate=nextDate,
        )


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)
    # Set by Owner.addPet so the pet can apply the owner's rules. Left out of
    # repr/compare to avoid an Owner <-> Pet loop.
    owner: "Owner | None" = field(default=None, repr=False, compare=False)

    def to_dict(self) -> dict:
        """Return this pet and its tasks as plain JSON types."""
        return {
            "name": self.name,
            "species": self.species,
            "breed": self.breed,
            "age": self.age,
            "tasks": [t.to_dict() for t in self.tasks],
        }

    def addTask(self, task: Task) -> None:
        """Add a task to this pet, applying the owner's rules if it has one."""
        if self.owner is not None:
            self.owner._checkNewTask(task)
        elif any(t is task for t in self.tasks):
            raise ValueError(f"task {task.title!r} is already assigned to a pet")
        task.petName = self.name
        self.tasks.append(task)


@dataclass
class Owner:
    name: str
    availableMinutes: int
    timePreferences: str  # one of TIME_PREFERENCES' keys
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Normalize and validate the time preference and available minutes."""
        self.timePreferences = str(self.timePreferences).strip().lower()
        if self.timePreferences not in TIME_PREFERENCES:
            raise ValueError(
                f"timePreferences must be one of {list(TIME_PREFERENCES)}, "
                f"got {self.timePreferences!r}"
            )
        self.availableMinutes = _toInt(self.availableMinutes, "availableMinutes")
        if self.availableMinutes < 0:
            raise ValueError("availableMinutes cannot be negative")
        limit = minutesBeforeMidnight(self.timePreferences)
        if self.availableMinutes > limit:
            raise ValueError(
                f"{self.timePreferences} starts at "
                f"{TIME_PREFERENCES[self.timePreferences]}, leaving only {limit} min "
                f"before midnight, but availableMinutes is {self.availableMinutes}. "
                f"Enter {limit} or less, or pick an earlier time preference."
            )

    def _checkNewTask(self, task: Task) -> None:
        """Raise ValueError if the task is already assigned or runs past midnight."""
        # One Task object can only live in one place, since the scheduler
        # writes petName/startTime onto it.
        if any(t is task for p in self.pets for t in p.tasks):
            raise ValueError(f"task {task.title!r} is already assigned to a pet")
        limit = minutesBeforeMidnight(self.timePreferences)
        if task.duration > limit:
            raise ValueError(
                f"{task.title!r} takes {task.duration} min, but {self.timePreferences} "
                f"leaves only {limit} min before midnight. Shorten the task or pick "
                f"an earlier time preference."
            )

    def addPet(self, pet: Pet) -> None:
        """Add a pet to this owner, ignoring a pet that is already added."""
        # Identity check: two different pets could compare equal as dataclasses.
        # Adding the same pet twice would schedule its tasks twice.
        if any(p is pet for p in self.pets):
            return
        if pet.owner is not None and pet.owner is not self:
            raise ValueError(f"{pet.name} already belongs to {pet.owner.name}")
        # The pet may arrive with tasks added before it had an owner.
        for task in pet.tasks:
            self._checkNewTask(task)
        pet.owner = self
        self.pets.append(pet)

    def addTask(self, pet: Pet, task: Task) -> None:
        """Add a task to a pet, adding the pet to this owner first if needed."""
        # Kept alongside Pet.addTask. Checking first means a rejected task
        # doesn't leave a half-added pet behind.
        self._checkNewTask(task)
        self.addPet(pet)
        pet.addTask(task)

    def getAllTasks(self) -> list[Task]:
        """Return every task from all of this owner's pets as one flat list."""
        allTasks = []
        for pet in self.pets:
            for task in pet.tasks:
                task.petName = pet.name
                allTasks.append(task)
        return allTasks

    def getTasksByPet(self, petName: str) -> list[Task]:
        """Return the tasks of every pet with this name (case-insensitive)."""
        wanted = petName.strip().lower()
        return [
            task
            for pet in self.pets
            if pet.name.lower() == wanted
            for task in pet.tasks
        ]

    def getTasksByStatus(self, completed: bool) -> list[Task]:
        """Return all tasks that are completed (True) or still pending (False)."""
        return [t for t in self.getAllTasks() if t.completed == completed]

    def to_dict(self) -> dict:
        """Return the owner, their pets and every task as plain JSON types."""
        return {
            "name": self.name,
            "availableMinutes": self.availableMinutes,
            "timePreferences": self.timePreferences,
            "pets": [p.to_dict() for p in self.pets],
        }

    def save_to_json(self, path: str = "data.json") -> None:
        """Save this owner, their pets and tasks to a JSON file.

        The file is written to a temporary file first and then moved into
        place, so a crash mid-save can't leave a half-written data file.
        """
        folder = os.path.dirname(os.path.abspath(path))
        fd, tmpPath = tempfile.mkstemp(dir=folder, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            os.replace(tmpPath, path)
        except BaseException:
            if os.path.exists(tmpPath):
                os.remove(tmpPath)
            raise

    @classmethod
    def load_from_json(cls, path: str = "data.json") -> "Owner":
        """Load an owner saved by save_to_json().

        Raises FileNotFoundError if the file doesn't exist and ValueError if
        it isn't valid JSON or has missing or invalid values. Every value goes
        through the same validation as when it is typed in, so a hand-edited
        file can't sneak in a bad task.
        """
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:  # a ValueError subclass, with a clearer message
                raise ValueError(f"{path} is not valid JSON: {e}") from None
        try:
            owner = cls(data["name"], data["availableMinutes"], data["timePreferences"])
            for petData in data["pets"]:
                pet = Pet(
                    petData["name"], petData["species"], petData["breed"],
                    _toInt(petData["age"], "age"),
                )
                owner.addPet(pet)
                for taskData in petData["tasks"]:
                    pet.addTask(Task.from_dict(taskData))
        except (KeyError, TypeError, AttributeError) as e:
            raise ValueError(f"{path} has missing or malformed data ({type(e).__name__}: {e})") from None
        return owner


@dataclass
class Scheduler:
    owner: Owner
    # Filled in by generatePlan(), read by explainPlan() and the UI.
    plan: list[Task] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)
    generated: bool = False

    def generatePlan(self, today: date | None = None) -> list[Task]:
        """Build the day's plan by priority, filling plan and skipped.

        Tasks whose dueDate is after `today` (default: the real date) are left
        out, so a recurring task's next occurrence doesn't show up early.
        """
        today = today or date.today()
        self.plan = []
        self.skipped = []

        allTasks = self.owner.getAllTasks()
        # Clear leftovers from an earlier plan, including tasks now completed.
        for task in allTasks:
            task.startTime = ""
            task.reason = ""
        pending = [
            t for t in allTasks
            if not t.completed and (t.dueDate is None or t.dueDate <= today)
        ]
        # Position of each task's pet, so equal tasks can be grouped by pet.
        petOrder = {id(t): i for i, pet in enumerate(self.owner.pets) for t in pet.tasks}
        # Highest priority first. Among equals: earlier due time (tasks with no
        # due time last), then keep one pet's tasks together, then shorter
        # tasks first so more fit.
        pending.sort(
            key=lambda t: (
                -PRIORITY_ORDER[t.priority],
                _toMinutes(t.dueTime, "dueTime") if t.dueTime else MINUTES_PER_DAY,
                petOrder[id(t)],
                t.duration,
            )
        )

        startHour, startMinute = TIME_PREFERENCES[self.owner.timePreferences].split(":")
        clock = int(startHour) * 60 + int(startMinute)
        remaining = self.owner.availableMinutes

        for task in pending:
            if clock + task.duration > MINUTES_PER_DAY:
                task.reason = "would run past midnight"
                self.skipped.append(task)
            elif task.duration <= remaining:
                task.startTime = f"{clock // 60:02d}:{clock % 60:02d}"
                task.reason = (
                    f"{task.priority} priority, fits in the "
                    f"{self.owner.timePreferences} schedule"
                )
                clock += task.duration
                remaining -= task.duration
                self.plan.append(task)
            else:
                task.reason = (
                    f"needs {task.duration} min but only {remaining} min left"
                )
                self.skipped.append(task)

        self.generated = True
        return self.plan

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks ordered by due date, then due time; tasks without a time go last.

        Defaults to all of the owner's tasks. Because dueTime is always stored
        as zero-padded "HH:MM", comparing the strings is the same as comparing
        the times, so no parsing is needed.
        """
        if tasks is None:
            tasks = self.owner.getAllTasks()
        today = date.today()
        return sorted(tasks, key=lambda t: (t.dueDate or today, t.dueTime or "99:99"))

    def filter_tasks(
        self, pet_name: str | None = None, completed: bool | None = None
    ) -> list[Task]:
        """Return the owner's tasks, narrowed by pet name and/or completion status.

        A filter left as None is ignored, so no arguments returns every task.
        """
        tasks = self.owner.getAllTasks() if pet_name is None else self.owner.getTasksByPet(pet_name)
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def mark_task_complete(self, task: Task) -> Task | None:
        """Mark a task done and, if it is daily or weekly, add its next occurrence to the same pet.

        Returns the new task, or None if the task doesn't repeat or was already
        complete (so completing twice can't create duplicates).
        """
        pet = next((p for p in self.owner.pets if any(t is task for t in p.tasks)), None)
        if pet is None:
            raise ValueError(f"task {task.title!r} does not belong to any of this owner's pets")
        if task.completed:
            return None
        # Build the next copy first, so a failure leaves the task still pending.
        nextTask = task.nextOccurrence()
        task.mark_complete()
        if nextTask is not None:
            pet.addTask(nextTask)
        return nextTask

    def find_next_available_slot(
        self, duration: int, day: date | None = None, after: str | None = None
    ) -> str | None:
        """Return the earliest "HH:MM" where a task of `duration` minutes fits without
        overlapping any timed, pending task on `day` (default: today).

        The search starts at `after` if given, otherwise at the owner's preferred
        start time, and the task must finish before midnight. Returns None if
        there is no gap. Tasks without a dueTime are not counted as busy.
        """
        duration = _toInt(duration, "duration")
        if duration <= 0:
            raise ValueError(f"duration must be positive, got {duration}")
        day = day or date.today()
        startText = after if after else TIME_PREFERENCES[self.owner.timePreferences]
        cursor = _toMinutes(startText, "after")

        busy = sorted(
            (_toMinutes(t.dueTime, "dueTime"), _toMinutes(t.dueTime, "dueTime") + t.duration)
            for t in self.owner.getAllTasks()
            if t.dueTime and not t.completed and (t.dueDate or date.today()) == day
        )
        # Sweep through the busy blocks in time order. If the gap before a block
        # is big enough, take it. Otherwise move the cursor to the block's end.
        for blockStart, blockEnd in busy:
            if blockStart >= cursor + duration:
                break
            cursor = max(cursor, blockEnd)
        return _toHHMM(cursor) if cursor + duration <= MINUTES_PER_DAY else None

    def detect_conflicts(self) -> list[str]:
        """Return a warning for each date and time that has more than one pending task.

        Lightweight on purpose: it only matches identical due times (it does not
        check whether durations overlap) and returns messages instead of raising,
        so the program keeps running.
        """
        today = date.today()
        slots = defaultdict(list)
        for task in self.owner.getAllTasks():
            if task.dueTime and not task.completed:
                slots[(task.dueDate or today, task.dueTime)].append(task)
        return [
            f"Conflict at {day.isoformat()} {time}: "
            + ", ".join(f"{t.title} ({t.petName})" for t in tasks)
            for (day, time), tasks in sorted(slots.items())
            if len(tasks) > 1
        ]

    def getPlanForPet(self, petName: str) -> list[Task]:
        """Return the planned tasks that belong to this pet (case-insensitive)."""
        wanted = petName.strip().lower()
        return [t for t in self.plan if t.petName.lower() == wanted]

    def explainPlan(self) -> str:
        """Return a readable summary of the plan and why tasks were skipped."""
        if not self.generated:
            return "No plan yet. Add tasks and generate a plan."
        if not self.plan and not self.skipped:
            return "Nothing to schedule today: no tasks, all are completed, or the rest are due later."

        lines = [f"Plan for {self.owner.name} ({self.owner.availableMinutes} min available):"]
        for task in self.plan:
            lines.append(
                f"- {task.startTime} {task.title} ({task.petName}, "
                f"{task.duration} min): {task.reason}"
            )
        if self.skipped:
            lines.append("Skipped:")
            for task in self.skipped:
                lines.append(f"- {task.title} ({task.petName}): {task.reason}")
        return "\n".join(lines)
