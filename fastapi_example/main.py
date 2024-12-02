from datetime import datetime

import uvicorn
from fastapi import HTTPException, Depends, APIRouter, FastAPI
from sqlalchemy.orm import Session
from core.models.tasks import Task
from core.schemas.tasks import TaskCreate, TaskUpdate, TaskInDB
from core.config import settings
from api import router as api_router
from create_fastapi_app import create_app
from fastapi import HTTPException, Depends, APIRouter, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from core.models.tasks import Task
from core.schemas.tasks import TaskCreate, TaskUpdate, TaskInDB
from core.database import get_session

main_app = create_app(
    create_custom_static_urls=True,
)

main_app.include_router(
    api_router,
)
app = FastAPI()




@api_router.get("/tasks/", response_model=list[TaskInDB], tags=["tasks"])
async def read_tasks(limit: int = 10, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Task).limit(limit))
    tasks = result.scalars().all()
    return tasks


@api_router.get("/tasks/{task_id}", response_model=TaskInDB, tags=["tasks"])
async def read_task(task_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@api_router.post("/tasks/", response_model=TaskInDB, tags=["tasks"])
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_session)):
    new_task = Task(**task.dict())
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


@api_router.put("/tasks/{task_id}", response_model=TaskInDB, tags=["tasks"])
async def update_task(task_id: int, task: TaskUpdate, db: AsyncSession = Depends(get_session)):

    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()

    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")


    for key, value in task.dict(exclude_unset=True).items():
        if isinstance(value, datetime):

            value = value.replace(tzinfo=None)
        setattr(db_task, key, value)
    db_task.is_completed = True

    await db.commit()
    await db.refresh(db_task)
    return db_task

@api_router.delete("/tasks/{task_id}", tags=["tasks"])
async def delete_task(task_id: int, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    db_task = result.scalar_one_or_none()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(db_task)
    await db.commit()
    return {"message": "Task deleted"}

app.include_router(api_router)
if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        # reload=True,
        reload=False,
    )