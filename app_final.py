"""Expense Tracker API: a small FastAPI service for tracking personal expenses."""

import logging
import os
import time

from fastapi import FastAPI

APP_NAME = os.getenv("APP_NAME", "Expense Tracker API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CURRENCY = os.getenv("CURRENCY", "RUB")
MONTHLY_BUDGET = float(os.getenv("MONTHLY_BUDGET", "50000"))

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("expense_tracker")

app = FastAPI(title=APP_NAME, version=APP_VERSION)

STARTED_AT = time.time()


@app.on_event("startup")
def on_startup():
    logger.info(
        "Starting %s v%s (currency=%s, monthly_budget=%.2f)",
        APP_NAME, APP_VERSION, CURRENCY, MONTHLY_BUDGET,
    )


@app.get("/")
def root():
    return {"service": APP_NAME, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok", "uptime_seconds": round(time.time() - STARTED_AT, 1)}


@app.get("/version")
def version():
    return {"name": APP_NAME, "version": APP_VERSION}
