import uuid
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    text,
    ForeignKey,
    Enum as SQLEnum,
    ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship

from common import TaskType, TaskStatus, CSVType, Buffer, Ligand, Metal


class Base(AsyncAttrs, DeclarativeBase):
    pass


class CSVData(Base):
    __tablename__ = "csv_data"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    type = Column(SQLEnum(CSVType, name="csv_type"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    task = relationship("Task", back_populates="csv_output", lazy="selectin")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(SQLEnum(TaskType, name="task_type"), nullable=False)
    status = Column(
        SQLEnum(TaskStatus, name="task_status"),
        nullable=False,
        default=TaskStatus.PENDING,
    )
    time_id = Column(
        PGUUID(as_uuid=True), ForeignKey("task_times.id"), unique=True, nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    time = relationship(
        "TaskTime", back_populates="task", uselist=False, lazy="selectin"
    )
    cv_input = relationship(
        "CyclicVoltammetryInput", back_populates="task", uselist=False, lazy="selectin"
    )
    pump_input = relationship(
        "PumpInput", back_populates="task", uselist=False, lazy="selectin"
    )
    csv_output = relationship(
        "CSVData", back_populates="task", uselist=False, lazy="selectin"
    )
    pump_output = relationship(
        "PumpOutput", back_populates="task", uselist=False, lazy="selectin"
    )
    complexation_input = relationship(
        "ComplexationInput", back_populates="task", uselist=False, lazy="selectin"
    )
    rolling_mean_input = relationship(
        "RollingMeanInput", back_populates="task", uselist=False, lazy="selectin"
    )
    peak_detection_input = relationship(
        "PeakDetectionInput", back_populates="task", uselist=False, lazy="selectin"
    )

    @property
    def input(self):
        return (
            self.cv_input
            or self.pump_input
            or self.complexation_input
            or self.rolling_mean_input
            or self.peak_detection_input
        )

    @property
    def output(self):
        return self.csv_output or self.pump_output


class TaskTime(Base):
    __tablename__ = "task_times"
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    init_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    elapsed = Column(Float, nullable=False)

    task = relationship("Task", back_populates="time", lazy="selectin")


class CyclicVoltammetryInput(Base):
    __tablename__ = "cv_inputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    v_range = Column(ARRAY(Float), nullable=False)
    freq = Column(Float, nullable=False)

    task = relationship("Task", back_populates="cv_input", lazy="selectin")


class PumpInput(Base):
    __tablename__ = "pump_inputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    source = Column(Integer, nullable=False)
    target = Column(Integer, nullable=False)

    task = relationship("Task", back_populates="pump_input", lazy="selectin")


class PumpOutput(Base):
    __tablename__ = "pump_outputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)

    task = relationship("Task", back_populates="pump_output", lazy="selectin")


class ComplexationInput(Base):
    __tablename__ = "complexation_inputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)

    buffer_type = Column(SQLEnum(Buffer, name="buffer_type"), nullable=False)
    buffer_amount = Column(Float, nullable=False)

    ligand_type = Column(SQLEnum(Ligand, name="ligand_type"), nullable=False)
    ligand_amount = Column(Float, nullable=False)

    metal_type = Column(SQLEnum(Metal, name="metal_type"), nullable=False)
    metal_amount = Column(Float, nullable=False)

    created_at = Column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    task = relationship("Task", back_populates="complexation_input", lazy="selectin")


class RollingMeanInput(Base):
    __tablename__ = "rolling_mean_inputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    csv_id = Column(PGUUID(as_uuid=True), ForeignKey("csv_data.id"), nullable=False)
    x_col = Column(String, nullable=False)
    y_col = Column(String, nullable=False)
    window_size = Column(Integer, nullable=False, default=20)
    min_periods = Column(Integer, nullable=True)

    task = relationship("Task", back_populates="rolling_mean_input", lazy="selectin")
    source_csv = relationship("CSVData", foreign_keys=[csv_id], lazy="selectin")


class PeakDetectionInput(Base):
    __tablename__ = "peak_detection_inputs"
    task_id = Column(PGUUID(as_uuid=True), ForeignKey("tasks.id"), primary_key=True)
    csv_id = Column(PGUUID(as_uuid=True), ForeignKey("csv_data.id"), nullable=False)
    x_col = Column(String, nullable=False)
    y_col = Column(String, nullable=False)
    height = Column(Float, nullable=True)
    prominence = Column(Float, nullable=False, default=1.0)
    distance = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    threshold = Column(Float, nullable=True)

    task = relationship("Task", back_populates="peak_detection_input", lazy="selectin")
    source_csv = relationship("CSVData", foreign_keys=[csv_id], lazy="selectin")


if __name__ == "__main__":
    # Debugging
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker

    engine = create_async_engine(
        "postgresql+asyncpg://dummy:pass@127.0.0.1:5432/sdl2", echo=True, future=True
    )
    AsyncSessionLocal = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
