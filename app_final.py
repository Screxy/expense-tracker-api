"""Expense Tracker API: a small FastAPI service for tracking personal expenses."""

import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import date
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

APP_NAME = os.getenv("APP_NAME", "Expense Tracker API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CURRENCY = os.getenv("CURRENCY", "RUB")
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET", "50000"))

CATEGORIES = ["food", "transport", "housing", "health", "entertainment", "other"]

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("expense_tracker")


class ExpenseIn(BaseModel):
    amount: float = Field(..., gt=0, description="Expense amount, must be positive")
    category: str = Field(..., description=f"One of: {', '.join(CATEGORIES)}")
    description: str = Field("", max_length=200)
    spent_on: date = Field(default_factory=date.today)


class Expense(ExpenseIn):
    id: int


# In-memory storage: enough for a learning project, resets on restart.
expenses: Dict[int, Expense] = {}
next_id = 1


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info(
        "Starting %s v%s (currency=%s, monthly_budget=%.2f)",
        APP_NAME, APP_VERSION, CURRENCY, MONTHLY_BUDGET,
    )
    yield
    logger.info("Shutting down %s", APP_NAME)


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)

STARTED_AT = time.time()


@app.get("/")
def root():
    return {"service": APP_NAME, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "uptime_seconds": round(time.time() - STARTED_AT, 1)}


@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION}


@app.get("/categories")
def list_categories():
    return {"categories": CATEGORIES}


@app.post("/expenses", response_model=Expense, status_code=201)
def create_expense(data: ExpenseIn):
    global next_id
    category = data.category.lower()
    if category not in CATEGORIES:
        logger.warning("Rejected expense with unknown category '%s'", data.category)
        raise HTTPException(
            status_code=422,
            detail=f"Unknown category '{data.category}'. Allowed: {', '.join(CATEGORIES)}",
        )
    expense = Expense(id=next_id, **data.model_dump(exclude={"category"}), category=category)
    expenses[expense.id] = expense
    next_id += 1
    logger.info("Created expense #%d: %.2f %s (%s)", expense.id, expense.amount, CURRENCY, category)
    return expense


@app.get("/expenses", response_model=List[Expense])
def list_expenses(category: Optional[str] = Query(None, description="Filter by category")):
    items = list(expenses.values())
    if category:
        items = [e for e in items if e.category == category.lower()]
    return items


@app.get("/expenses/{expense_id}", response_model=Expense)
def get_expense(expense_id: int):
    expense = expenses.get(expense_id)
    if expense is None:
        logger.info("Expense #%d not found", expense_id)
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    if expenses.pop(expense_id, None) is None:
        raise HTTPException(status_code=404, detail=f"Expense {expense_id} not found")
    logger.info("Deleted expense #%d", expense_id)
