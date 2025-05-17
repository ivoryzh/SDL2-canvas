from enum import Enum, StrEnum, auto
from typing import Any, Optional, Union
from uuid import UUID, uuid4
from datetime import datetime
from typing import NamedTuple, Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class Metal(StrEnum):
    V = "V"
    FE = "Fe"
    CU = "Cu"


class Ligand(StrEnum):
    L1 = "L1"
    L2 = "L2"


class Buffer(StrEnum):
    PH7 = "PH7"
    PH3 = "PH3"


class Transfer[T](NamedTuple):
    compound: T
    amount: float


class CSVType(StrEnum):
    CVRAW = auto()
    CVPROC = auto()


class TaskType(StrEnum):
    CV = auto()
    PUMP_TRANSFER = auto()
    COMPLEXATION = auto()
    ROLLING_MEAN = auto()
    PEAK_DETECTION = auto()
    CLEAN = auto()


class TaskStatus(Enum):
    PENDING = 0
    COMPLETED = 1
    RUNNING = 2
    ERROR = 3


class CSVDataSchema(BaseModel):
    id: Optional[UUID] = None
    task_id: UUID
    type: CSVType
    content: str
    created_at: Optional[datetime] = None

    model_config = dict(from_attributes=True)


class TaskTimeSchema(BaseModel):
    init_ts: datetime
    end_ts: datetime
    elapsed: float

    model_config = dict(from_attributes=True)


class CVInputSchema(BaseModel):
    v_range: list[float]
    freq: float

    model_config = dict(from_attributes=True)


class PumpInputSchema(BaseModel):
    source: int
    target: int

    model_config = dict(from_attributes=True)


class PumpOutputSchema(BaseModel):
    msg: str = "done"  # placeholder – extend later

    model_config = dict(from_attributes=True)


class CVProcessInputSchema(BaseModel):
    x_col: str | int
    y_col: str | int


class ComplexationInputSchema(BaseModel):
    buffer: Transfer[Buffer]
    ligand: Transfer[Ligand]
    metal: Transfer[Metal]


class RollingMeanInputSchema(BaseModel):
    csv_id: UUID
    x_col: str | int
    y_col: str | int
    window_size: int = 20
    min_periods: Optional[int] = None

    model_config = dict(from_attributes=True)


class PeakDetectionInputSchema(BaseModel):
    csv_id: UUID
    x_col: str | int
    y_col: str | int
    height: Optional[float] = None
    prominence: float = 1.0
    distance: Optional[int] = None
    width: Optional[int] = None
    threshold: Optional[float] = None

    model_config = dict(from_attributes=True)


TaskInputType = Union[
    CVInputSchema,
    PumpInputSchema,
    ComplexationInputSchema,
    RollingMeanInputSchema,
    PeakDetectionInputSchema,
    None,
]
TaskOutputType = Union[CSVDataSchema, PumpOutputSchema, None]


class TaskSchema(BaseModel):
    id: UUID
    type: TaskType
    status: TaskStatus
    time: Optional[TaskTimeSchema]
    input: Optional[TaskInputType]
    output: Optional[TaskOutputType]

    model_config = dict(from_attributes=True)
