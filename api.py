import asyncio
import time
from contextlib import asynccontextmanager
import io
from datetime import datetime
from enum import Enum, StrEnum, auto
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, Union
from uuid import UUID, uuid4

from data_process import rolling_mean, detect_peaks

import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import selectinload, sessionmaker

from common import *
from sqlalchemy_models import ComplexationInput as DBComplexInput
from sqlalchemy_models import CSVData
from sqlalchemy_models import CyclicVoltammetryInput as DBCVInput
from sqlalchemy_models import PumpInput as DBPumpInput
from sqlalchemy_models import PumpOutput as DBPumpOutput
from sqlalchemy_models import Task as DBTask
from sqlalchemy_models import TaskTime as DBTaskTime
from sqlalchemy_models import RollingMeanInput as DBRollingMean
from sqlalchemy_models import PeakDetectionInput as DBPeakDetect

AsyncSessionLocal: sessionmaker
DATABASE_URL = "postgresql+asyncpg://dummy:pass@127.0.0.1:5432/sdl2"
FUTURES: Dict[UUID, asyncio.Task] = {}
LOCKS: Dict[str, asyncio.Lock] = {
    "pump": asyncio.Lock(),
    "poten": asyncio.Lock(),
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    # Need to work with globals for FastAPI to make connection with the DB
    global engine, AsyncSessionLocal

    engine = create_async_engine(DATABASE_URL, echo=True, future=True)
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(DBTask.metadata.drop_all)
        await conn.run_sync(DBTask.metadata.create_all)

    print("[startup] DB engine & tables ready")
    yield


app = FastAPI(lifespan=lifespan)


async def load_task_with_relationships(db: AsyncSession, task_id: UUID) -> TaskSchema:
    # This helper function is the only way (I have found) to fetch the task with all potentials relationships
    result = await db.execute(
        select(DBTask)
        .where(DBTask.id == task_id)
        .options(
            selectinload(DBTask.time),
            selectinload(DBTask.cv_input),
            selectinload(DBTask.pump_input),
            selectinload(DBTask.csv_output),
            selectinload(DBTask.pump_output),
            selectinload(DBTask.complexation_input),
            selectinload(DBTask.rolling_mean_input),
            selectinload(DBTask.peak_detection_input),
        )
    )
    task = result.scalar_one_or_none()

    if task is None:
        raise HTTPException(404, "Task not found")

    input_data = None
    output_data = None
    match task.type:
        case TaskType.CV:
            input_data = task.cv_input
            output_data = task.csv_output
        case TaskType.PUMP_TRANSFER:
            input_data = task.pump_input
            output_data = task.pump_output
        case TaskType.COMPLEXATION:
            ci = task.complexation_input
            input_data = ComplexationInputSchema(
                buffer=Transfer(compound=ci.buffer_type, amount=ci.buffer_amount),
                ligand=Transfer(compound=ci.ligand_type, amount=ci.ligand_amount),
                metal=Transfer(compound=ci.metal_type, amount=ci.metal_amount),
            )
            output_data = None
        case TaskType.ROLLING_MEAN:
            if task.rolling_mean_input:
                input_data = task.rolling_mean_input
            if task.csv_output:
                output_data = task.csv_output
        case TaskType.PEAK_DETECTION:
            if task.peak_detection_input:
                input_data = task.peak_detection_input
            if task.csv_output:
                output_data = task.csv_output

    # Create a TaskSchema instance with the resolved relationships
    return TaskSchema(
        id=task.id,
        type=task.type,
        status=task.status,
        time=task.time,
        input=input_data,
        output=output_data,
    )


async def get_db() -> AsyncSession:
    if AsyncSessionLocal is None:
        raise RuntimeError("DB not initialised (startup event hasn't run)")
    async with AsyncSessionLocal() as session:
        yield session


async def create_db_task(
    db: AsyncSession, *, task_type: TaskType, input_schema: TaskInputType
) -> DBTask:
    db_task = DBTask(type=task_type, status=TaskStatus.PENDING)
    db.add(db_task)
    await db.flush()

    match task_type:
        case TaskType.CV if isinstance(input_schema, CVInputSchema):
            db.add(
                DBCVInput(
                    task_id=db_task.id,
                    v_range=input_schema.v_range,
                    freq=input_schema.freq,
                )
            )
        case TaskType.PUMP_TRANSFER if isinstance(input_schema, PumpInputSchema):
            db.add(
                DBPumpInput(
                    task_id=db_task.id,
                    source=input_schema.source,
                    target=input_schema.target,
                )
            )
        case TaskType.COMPLEXATION if isinstance(input_schema, ComplexationInputSchema):
            db.add(
                DBComplexInput(
                    task_id=db_task.id,
                    buffer_type=input_schema.buffer.compound,
                    buffer_amount=input_schema.buffer.amount,
                    ligand_type=input_schema.ligand.compound,
                    ligand_amount=input_schema.ligand.amount,
                    metal_type=input_schema.metal.compound,
                    metal_amount=input_schema.metal.amount,
                )
            )
        case TaskType.ROLLING_MEAN if isinstance(input_schema, RollingMeanInputSchema):
            db.add(
                DBRollingMean(
                    task_id=db_task.id,
                    csv_id=input_schema.csv_id,
                    x_col=input_schema.x_col,
                    y_col=input_schema.y_col,
                    window_size=input_schema.window_size,
                    min_periods=input_schema.min_periods,
                )
            )
        case TaskType.PEAK_DETECTION if isinstance(
            input_schema, PeakDetectionInputSchema
        ):
            db.add(
                DBPeakDetect(
                    task_id=db_task.id,
                    csv_id=input_schema.csv_id,
                    x_col=input_schema.x_col,
                    y_col=input_schema.y_col,
                    height=input_schema.height,
                    prominence=input_schema.prominence,
                    distance=input_schema.distance,
                    width=input_schema.width,
                    threshold=input_schema.threshold,
                )
            )
        case _:
            raise HTTPException(400, "Input payload does not match task type")

    await db.commit()
    return await db.get(DBTask, db_task.id)


async def mark_task(db: AsyncSession, task_id: UUID, status: TaskStatus):
    await db.execute(update(DBTask).where(DBTask.id == task_id).values(status=status))
    await db.commit()


async def mark_task_running(db: AsyncSession, task_id: UUID):
    await mark_task(db, task_id, TaskStatus.RUNNING)


async def mark_task_completed(db: AsyncSession, task_id: UUID):
    await mark_task(db, task_id, TaskStatus.COMPLETED)


async def mark_task_error(db: AsyncSession, task_id: UUID, error_message: str = None):
    await mark_task(db, task_id, TaskStatus.ERROR)
    if error_message:
        print(f"Task {task_id} error: {error_message}")


async def get_csv_as_dataframe(
    db: AsyncSession,
    csv_id: UUID,
    task_id: UUID = None,
) -> Optional[pd.DataFrame]:
    source_csv = await db.get(CSVData, csv_id)

    if source_csv is None:
        if task_id:
            await mark_task_error(db, task_id, f"Source CSV with ID {csv_id} not found")
            return None
        else:
            raise HTTPException(404, f"CSV data with ID {csv_id} not found")

    try:
        csv_content = source_csv.content
        df = pd.read_csv(
            io.StringIO(csv_content),
            na_values=["NAN", "NA", "N/A", "nan", "NaN", "-", "#N/A", "NULL", ""],
            keep_default_na=True,
            na_filter=True,
        )

        return df
    except Exception as e:
        if task_id:
            await mark_task_error(db, task_id, f"Failed to parse CSV: {str(e)}")
            return None
        else:
            raise HTTPException(400, f"Failed to parse CSV: {str(e)}")


async def finish_task(
    db: AsyncSession, *, task_id: UUID, start: datetime, output: TaskOutputType
):
    t_row = DBTaskTime(
        init_ts=start,
        end_ts=datetime.now(),
        elapsed=(datetime.now() - start).total_seconds(),
    )
    db.add(t_row)
    await db.flush()

    match output:
        case CSVDataSchema():
            csv_data = CSVData(
                task_id=task_id, type=output.type, content=output.content
            )
            db.add(csv_data)
        case PumpOutputSchema():
            db.add(DBPumpOutput(task_id=task_id))
        case None:
            pass
        case _:
            raise ValueError("Unknown output type")

    await mark_task_completed(db, task_id)


async def execute_cv_task(task_id: UUID, cv: CVInputSchema):
    start = datetime.now()
    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

    async with LOCKS["poten"]:
        await asyncio.sleep(5)
        with open("test.csv", "r") as f:
            csv_content = f.read()

    output = CSVDataSchema(task_id=task_id, type=CSVType.CVRAW, content=csv_content)

    async with AsyncSessionLocal() as db:
        await finish_task(db, task_id=task_id, start=start, output=output)


async def execute_clean_task(task_id: UUID):
    start = datetime.now()

    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

    await asyncio.sleep(5)

    async with AsyncSessionLocal() as db:
        await finish_task(db, task_id=task_id, start=start, output=None)


async def execute_pump_task(task_id: UUID, pump: PumpInputSchema):
    start = datetime.now()
    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

    async with LOCKS["pump"]:  # exclusive access to pump hardware
        await asyncio.sleep(10)

    output = PumpOutputSchema()

    async with AsyncSessionLocal() as db:
        await finish_task(db, task_id=task_id, start=start, output=output)


async def execute_complexation_task(
    task_id: UUID, complexation: ComplexationInputSchema
):
    start = datetime.now()

    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

    # Sissi -> This part will be a single function that executes all the transfers.
    # This is a UO that it is already defined in MEDUSA's code as run_complexation.
    # For now I am just logging some dummy information to simulate the transfers.
    async with LOCKS["pump"]:
        print(
            f"Transferring {complexation.buffer.amount} units of {complexation.buffer.compound}"
        )
        await asyncio.sleep(5)

        print(
            f"Transferring {complexation.ligand.amount} units of {complexation.ligand.compound}"
        )
        await asyncio.sleep(5)

        print(
            f"Transferring {complexation.metal.amount} units of {complexation.metal.compound}"
        )
        await asyncio.sleep(5)

    async with AsyncSessionLocal() as db:
        await finish_task(db, task_id=task_id, start=start, output=None)


async def execute_rolling_mean_task(task_id: UUID, input_data: RollingMeanInputSchema):
    start = datetime.now()

    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

        df = await get_csv_as_dataframe(db, input_data.csv_id, task_id)
        df = df.dropna()
        if df is None:
            return

        result = rolling_mean(
            df,
            input_data.x_col,
            input_data.y_col,
            window_size=input_data.window_size,
            min_periods=input_data.min_periods,
        )

        df[input_data.y_col] = result

        output_content = df.to_csv(index=False)

        output = CSVDataSchema(
            task_id=task_id, type=CSVType.CVPROC, content=output_content
        )

        await finish_task(db, task_id=task_id, start=start, output=output)


async def execute_peak_detection_task(
    task_id: UUID, input_data: PeakDetectionInputSchema
):
    start = datetime.now()

    async with AsyncSessionLocal() as db:
        await mark_task_running(db, task_id)

        df = await get_csv_as_dataframe(db, input_data.csv_id, task_id)
        if df is None:
            return

        mcycle = df["cycle"].max()
        peaks_df = detect_peaks(
            df[df["cycle"] == mcycle],
            input_data.x_col,
            input_data.y_col,
            height=input_data.height,
            prominence=input_data.prominence,
            distance=input_data.distance,
            width=input_data.width,
            threshold=input_data.threshold,
        )

        output_content = peaks_df.to_csv(index=False)

        output = CSVDataSchema(
            task_id=task_id, type=CSVType.CVPROC, content=output_content
        )

        await finish_task(db, task_id=task_id, start=start, output=output)


@app.post("/tasks/cv/", response_model=TaskSchema, status_code=201)
async def create_cv_task(input_data: CVInputSchema, db: AsyncSession = Depends(get_db)):
    db_task = await create_db_task(db, task_type=TaskType.CV, input_schema=input_data)
    FUTURES[db_task.id] = asyncio.create_task(execute_cv_task(db_task.id, input_data))
    return await load_task_with_relationships(db, db_task.id)


@app.post("/tasks/pump/", response_model=TaskSchema, status_code=201)
async def create_pump_task(
    input_data: PumpInputSchema, db: AsyncSession = Depends(get_db)
):
    db_task = await create_db_task(
        db, task_type=TaskType.PUMP_TRANSFER, input_schema=input_data
    )
    FUTURES[db_task.id] = asyncio.create_task(execute_pump_task(db_task.id, input_data))
    return await load_task_with_relationships(db, db_task.id)


@app.post("/tasks/complexation/", response_model=TaskSchema, status_code=201)
async def create_complexation_task_endpoint(
    input_data: ComplexationInputSchema, db: AsyncSession = Depends(get_db)
):
    db_task = await create_db_task(
        db, task_type=TaskType.COMPLEXATION, input_schema=input_data
    )
    FUTURES[db_task.id] = asyncio.create_task(
        execute_complexation_task(db_task.id, input_data)
    )
    return await load_task_with_relationships(db, db_task.id)


@app.post("/tasks/rolling_mean/", response_model=TaskSchema, status_code=201)
async def create_rolling_mean_task(
    input_data: RollingMeanInputSchema, db: AsyncSession = Depends(get_db)
):
    db_task = await create_db_task(
        db, task_type=TaskType.ROLLING_MEAN, input_schema=input_data
    )
    FUTURES[db_task.id] = asyncio.create_task(
        execute_rolling_mean_task(db_task.id, input_data)
    )
    return await load_task_with_relationships(db, db_task.id)


@app.post("/tasks/peak_detection/", response_model=TaskSchema, status_code=201)
async def create_peak_detection_task(
    input_data: PeakDetectionInputSchema, db: AsyncSession = Depends(get_db)
):
    db_task = await create_db_task(
        db, task_type=TaskType.PEAK_DETECTION, input_schema=input_data
    )
    FUTURES[db_task.id] = asyncio.create_task(
        execute_peak_detection_task(db_task.id, input_data)
    )
    return await load_task_with_relationships(db, db_task.id)


@app.post("/tasks/clean/", response_model=TaskSchema, status_code=201)
async def create_clean_task(db: AsyncSession = Depends(get_db)):
    db_task = await create_db_task(db, task_type=TaskType.CLEAN, input_schema=None)
    FUTURES[db_task.id] = asyncio.create_task(execute_clean_task(db_task.id))
    return await load_task_with_relationships(db, db_task.id)


@app.delete("/task/{task_id}", status_code=204)
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    if task_id in FUTURES and not FUTURES[task_id].done():
        raise HTTPException(409, "Task still running; cancel first")

    await db.execute(delete(DBTask).where(DBTask.id == task_id))
    await db.commit()
    FUTURES.pop(task_id, None)


@app.get("/task/{task_id}", response_model=TaskSchema)
async def read_task(task_id: UUID, db: AsyncSession = Depends(get_db)):
    fut = FUTURES.get(task_id)
    if fut and not fut.done():
        try:
            await fut
        except Exception:
            pass

    return await load_task_with_relationships(db, task_id)


@app.get("/csv/{csv_id}", response_model=CSVDataSchema)
async def read_csv_data(csv_id: UUID, db: AsyncSession = Depends(get_db)):
    csv_data = await db.get(CSVData, csv_id)
    if csv_data is None:
        raise HTTPException(404, "CSV data not found")
    return csv_data


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
