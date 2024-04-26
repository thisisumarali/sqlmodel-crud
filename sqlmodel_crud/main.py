from fastapi import FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager

class TaskBase(SQLModel):
    title: str = Field(index=True)
    todays_task: str = Field(index=True)
    

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

class TaskCreate(TaskBase):
    todays_task: str
    
class TaskRead(TaskBase):
    id: int

class TaskUpdate(SQLModel):
    title: str | None = None
    todays_task: str | None = None
   

sqlite_url = f"postgresql://neondb_owner:XhBf08ANGyWr@ep-bold-heart-a569u7gt.us-east-2.aws.neon.tech/neondb?sslmode=require"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    create_db_and_tables()
    yield

# Create FastAPI app instance
app: FastAPI = FastAPI(lifespan=lifespan)

@app.post("/todos/", response_model=TaskRead)
def create_task(task: TaskCreate):
    with Session(engine) as session:
        db_task = Task.model_validate(task)
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task

@app.get("/todos/", response_model=list[TaskRead])  
def read_tasks(offset: int = 0, limit: int = Query(default=100, le=100)):
    with Session(engine) as session:
        tasks = session.exec(select(Task).offset(offset).limit(limit)).all()
        return tasks

@app.get("/todos/{task_id}", response_model=TaskRead)
def read_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

@app.put("/todos/{task_id}", response_model=TaskRead)
def update_task(task_id: int, task: TaskUpdate):
    with Session(engine) as session:
        db_task = session.get(Task, task_id)
        if not db_task:
            raise HTTPException(status_code=404, detail="Task not found")
        task_data = task.model_dump(exclude_unset=True)
        for key, value in task_data.items():
            setattr(db_task, key, value)
        session.add(db_task)
        session.commit()
        session.refresh(db_task)
        return db_task

@app.delete("/todos/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
        return {"ok": True}
