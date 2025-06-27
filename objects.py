#
# Author: Sean O'Beirne
# Date: 6-23-2025
# File: state.py
#

#
# Dat classes for projectarium
#

from dataclasses import dataclass
from typing import Optional


@dataclass
class Project:
    id: int
    name: str
    description: str
    path: str
    file: Optional[str]
    priority: int
    status: str
    language: Optional[str]
    todo_count: int = 0  # derived, not stored in DB


@dataclass
class TodoItem:
    id: int
    description: str
    priority: int
    deleted: bool
    project_id: int
