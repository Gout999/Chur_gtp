"""
EduGuide memory layer: Working, External, Archive, and shared namespace access.
See DEVELOPER_GUIDE.md and PRD §3.
"""
from .working import WorkingMemory
from .external import ExternalMemory
from .archive import ArchiveMemory
from .shared import shared_memory

__all__ = ["WorkingMemory", "ExternalMemory", "ArchiveMemory", "shared_memory"]
