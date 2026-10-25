"""Expense Tracker API: a small FastAPI service for tracking personal expenses."""

import logging

from fastapi import FastAPI

APP_VERSION = "0.1.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("expense_tracker")

app = FastAPI(title="Expense Tracker API", version=APP_VERSION)


@app.get("/")
def root():
    return {"service": "Expense Tracker API", "docs": "/docs"}
