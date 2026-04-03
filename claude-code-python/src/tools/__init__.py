"""Tool system for CCP"""

from .base import Tool, ToolContext, ValidationResult
from .registry import ToolRegistry
from .bash import BashTool, BashInput
from .file_read import FileReadTool, FileReadInput
from .file_edit import FileEditTool, FileEditInput
from .file_write import FileWriteTool, FileWriteInput
from .file_write_batch import FileWriteBatchTool, FileWriteBatchInput
from .grep import GrepTool, GrepInput
from .glob import GlobTool, GlobInput
from .mkdir import MkdirTool, MkdirInput
from .project_template import ProjectTemplateTool, ProjectTemplateInput

__all__ = [
    # Base
    "Tool",
    "ToolContext",
    "ValidationResult",
    "ToolRegistry",
    # Bash
    "BashTool",
    "BashInput",
    # File operations
    "FileReadTool",
    "FileReadInput",
    "FileEditTool",
    "FileEditInput",
    "FileWriteTool",
    "FileWriteInput",
    "FileWriteBatchTool",
    "FileWriteBatchInput",
    # Directory
    "MkdirTool",
    "MkdirInput",
    # Search
    "GrepTool",
    "GrepInput",
    "GlobTool",
    "GlobInput",
    # Project
    "ProjectTemplateTool",
    "ProjectTemplateInput",
]
