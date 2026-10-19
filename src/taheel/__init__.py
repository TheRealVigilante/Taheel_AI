"""
Taheel AI (تأهيل)
=================
Enterprise 30-60-90 Day Employee Onboarding & Probation Governance Engine
Aligned with Saudi Labor Law (Article 53).
"""

import logging
import sys

__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Package-level logging setup
# ---------------------------------------------------------------------------
# Only configure if no handlers are attached yet (avoids double-config when
# uvicorn or pytest already set up logging).
_root_logger = logging.getLogger("taheel")
if not _root_logger.handlers:
    _handler = logging.StreamHandler(sys.stdout)
    _handler.setLevel(logging.DEBUG)
    _formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    _root_logger.addHandler(_handler)
    _root_logger.setLevel(logging.DEBUG)
    _root_logger.propagate = False  # Don't double-log via root logger
