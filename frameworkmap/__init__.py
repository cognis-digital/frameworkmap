"""FRAMEWORKMAP - crosswalk compliance controls across frameworks.

Maps controls across NIST SP 800-53, ISO/IEC 27001, SOC 2 (TSC),
CMMC, and PCI DSS using a shared catalog of common control objectives.
"""
from .core import (
    Crosswalk,
    FRAMEWORKS,
    map_control,
    crosswalk_framework,
    coverage_report,
    find_gaps,
    load_catalog,
)

TOOL_NAME = "frameworkmap"
TOOL_VERSION = "1.0.0"

__all__ = [
    "Crosswalk",
    "FRAMEWORKS",
    "map_control",
    "crosswalk_framework",
    "coverage_report",
    "find_gaps",
    "load_catalog",
    "TOOL_NAME",
    "TOOL_VERSION",
]
