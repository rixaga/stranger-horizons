"""Logging to the console and, optionally, to an episode log file."""
from __future__ import annotations

import logging
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def get_logger(name: str, log_file: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    """Idempotent: calling again with the same name and file adds no duplicate handlers."""
    logger = logging.getLogger(f"shpipe.{name}")
    logger.setLevel(level)
    logger.propagate = False
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(console)
    if log_file is not None:
        log_file = Path(log_file).resolve()
        if not any(isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_file for h in logger.handlers):
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(logging.Formatter(FORMAT))
            logger.addHandler(fh)
    return logger
