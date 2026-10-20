from dataclasses import dataclass, field

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

MINUTES_PER_DAY = 24 * 60


def minutesBeforeMidnight(timePreference: str) -> int:
    """Minutes between the day's start for this preference and midnight."""
    hour, minute = TIME_PREFERENCES[timePreference].split(":")
    return MINUTES_PER_DAY - (int(hour) * 60 + int(minute))


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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True


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


@dataclass
class Scheduler:
    owner: Owner
    # Filled in by generatePlan(), read by explainPlan() and the UI.
    plan: list[Task] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)
    generated: bool = False

    def generatePlan(self) -> list[Task]:
        """Build the day's plan by priority, filling plan and skipped."""
        self.plan = []
        self.skipped = []

        allTasks = self.owner.getAllTasks()
        # Clear leftovers from an earlier plan, including tasks now completed.
        for task in allTasks:
            task.startTime = ""
            task.reason = ""
        pending = [t for t in allTasks if not t.completed]
        # Highest priority first; among equals, shorter tasks first so more fit.
        pending.sort(key=lambda t: (-PRIORITY_ORDER[t.priority], t.duration))

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

    def explainPlan(self) -> str:
        """Return a readable summary of the plan and why tasks were skipped."""
        if not self.generated:
            return "No plan yet. Add tasks and generate a plan."
        if not self.plan and not self.skipped:
            return "Nothing to schedule: no tasks, or all are completed."

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
