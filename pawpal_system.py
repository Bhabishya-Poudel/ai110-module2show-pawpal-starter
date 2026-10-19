from dataclasses import dataclass, field


@dataclass
class Task:
    title: str
    duration: int  # minutes
    priority: str  # "low", "medium", or "high"
    completed: bool = False


@dataclass
class Pet:
    name: str
    species: str
    breed: str
    age: int
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Owner:
    name: str
    availableMinutes: int
    timePreferences: str
    pets: list[Pet] = field(default_factory=list)

    def addPet(self, pet: Pet) -> None:
        pass

    def addTask(self, pet: Pet, task: Task) -> None:
        pass

    def getAllTasks(self) -> list[Task]:
        pass


@dataclass
class Scheduler:
    owner: Owner

    def generatePlan(self) -> list[Task]:
        pass

    def explainPlan(self) -> str:
        pass
