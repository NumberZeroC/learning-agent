"""Project template tool for creating complete project structures"""

from __future__ import annotations

from typing import Any

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult

logger = structlog.get_logger(__name__)


# Project templates
TEMPLATES = {
    "python_cli": {
        "name": "Python CLI Project",
        "description": "Command-line application with modern Python structure",
        "files": [
            {
                "path": "pyproject.toml",
                "content": """[project]
name = "{{project_name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
]

[project.scripts]
{{project_name}} = "{{project_name}}.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
            },
            {
                "path": "{{project_name}}/__init__.py",
                "content": """\"\"\"{{project_name}} - {{description}}\"\"\"

__version__ = "0.1.0"
"""
            },
            {
                "path": "{{project_name}}/cli.py",
                "content": """\"\"\"Command-line interface\"\"\"

import click
from . import __version__


@click.command()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def main(verbose: bool = False):
    \"\"\"{{project_name}} - {{description}}\"\"\"
    click.echo(f"{{project_name}} v{__version__}")
    if verbose:
        click.echo("Verbose mode enabled")


if __name__ == "__main__":
    main()
"""
            },
            {
                "path": "{{project_name}}/main.py",
                "content": """\"\"\"Main module\"\"\"


def main_function():
    \"\"\"Main function\"\"\"
    return "Hello from {{project_name}}!"


if __name__ == "__main__":
    print(main_function())
"""
            },
            {
                "path": "README.md",
                "content": """# {{project_name}}

{{description}}

## Installation

```bash
pip install -e .
```

## Usage

```bash
{{project_name}} --help
```

## Development

```bash
pip install -e ".[dev]"
```

## License

MIT
"""
            },
            {
                "path": ".gitignore",
                "content": """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
.egg/
.eggs/
dist/
build/
*.egg-info/
"""
            },
            {
                "path": "tests/__init__.py",
                "content": "# Tests package"
            },
            {
                "path": "tests/test_main.py",
                "content": """\"\"\"Tests for {{project_name}}\"\"\"

import pytest
from {{project_name}}.main import main_function


def test_main_function():
    \"\"\"Test main function\"\"\"
    result = main_function()
    assert result == "Hello from {{project_name}}!"
"""
            },
        ]
    },
    
    "python_package": {
        "name": "Python Package",
        "description": "Reusable Python package with tests and docs",
        "files": [
            {
                "path": "pyproject.toml",
                "content": """[project]
name = "{{project_name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
            },
            {
                "path": "{{project_name}}/__init__.py",
                "content": """\"\"\"{{project_name}} - {{description}}\"\"\"

__version__ = "0.1.0"
"""
            },
            {
                "path": "{{project_name}}/core.py",
                "content": """\"\"\"Core functionality\"\"\"


def main_feature():
    \"\"\"Main feature implementation\"\"\"
    return "Feature result"
"""
            },
            {
                "path": "README.md",
                "content": """# {{project_name}}

{{description}}

## Installation

```bash
pip install {{project_name}}
```

## Usage

```python
import {{project_name}}

result = {{project_name}}.main_feature()
```

## License

MIT
"""
            },
            {
                "path": "tests/test_core.py",
                "content": """\"\"\"Tests for {{project_name}}\"\"\"

from {{project_name}}.core import main_feature


def test_main_feature():
    \"\"\"Test main feature\"\"\"
    result = main_feature()
    assert result == "Feature result"
"""
            },
        ]
    },
    
    "web_api": {
        "name": "Web API Project",
        "description": "FastAPI web API with async support",
        "files": [
            {
                "path": "pyproject.toml",
                "content": """[project]
name = "{{project_name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
    "pydantic>=2.0.0",
]

[project.scripts]
{{project_name}} = "{{project_name}}.main:run"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
            },
            {
                "path": "{{project_name}}/__init__.py",
                "content": """\"\"\"{{project_name}} - {{description}}\"\"\"

__version__ = "0.1.0"
"""
            },
            {
                "path": "{{project_name}}/main.py",
                "content": """\"\"\"Main application\"\"\"

from fastapi import FastAPI
import uvicorn

app = FastAPI(
    title="{{project_name}}",
    description="{{description}}",
    version="0.1.0",
)


@app.get("/")
async def root():
    \"\"\"Root endpoint\"\"\"
    return {"message": "Welcome to {{project_name}}", "version": "0.1.0"}


@app.get("/health")
async def health():
    \"\"\"Health check\"\"\"
    return {"status": "healthy"}


def run():
    \"\"\"Run the server\"\"\"
    uvicorn.run("{{project_name}}.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
"""
            },
            {
                "path": "README.md",
                "content": """# {{project_name}}

{{description}}

## Installation

```bash
pip install -e .
```

## Usage

```bash
{{project_name}}
```

Then visit http://localhost:8000

## API Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
"""
            },
        ]
    },
}


class ProjectTemplateInput(ToolInput):
    """Input for project template tool"""
    
    template: str
    project_name: str
    description: str = "A new project"
    output_dir: str | None = None


class ProjectTemplateTool(Tool[ProjectTemplateInput]):
    """
    Tool for creating project from template.
    
    Features:
    - Multiple project templates
    - Variable substitution
    - Directory creation
    - Progress reporting
    """
    
    name = "project_template"
    description = "Create a new project from template"
    
    input_schema = {
        "type": "object",
        "properties": {
            "template": {
                "type": "string",
                "enum": list(TEMPLATES.keys()),
                "description": "Template to use"
            },
            "project_name": {
                "type": "string",
                "description": "Project name"
            },
            "description": {
                "type": "string",
                "description": "Project description"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory (default: project_name)"
            }
        },
        "required": ["template", "project_name"]
    }
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        templates_list = ", ".join(TEMPLATES.keys())
        return f"""Use the `project_template` tool to create a new project from template.

Available templates: {templates_list}

Example:

Create a CLI project:
{{
    "template": "python_cli",
    "project_name": "my_project",
    "description": "My awesome CLI tool"
}}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate input"""
        
        template = tool_input.get("template")
        if not template:
            return ValidationResult.fail("Template is required")
        
        if template not in TEMPLATES:
            return ValidationResult.fail(
                f"Unknown template: {template}. Available: {', '.join(TEMPLATES.keys())}",
                error_code="UNKNOWN_TEMPLATE"
            )
        
        project_name = tool_input.get("project_name")
        if not project_name:
            return ValidationResult.fail("Project name is required")
        
        # Validate project name
        if not project_name.replace("_", "").replace("-", "").isalnum():
            return ValidationResult.fail(
                f"Invalid project name: {project_name}",
                error_code="INVALID_NAME"
            )
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: dict | ProjectTemplateInput, context: ToolContext) -> ToolResult:
        """Execute project template creation"""
        
        from .file_write_batch import FileWriteBatchInput, FileWriteBatchTool
        
        # Convert dict to Pydantic model if needed
        if isinstance(tool_input, dict):
            tool_input = ProjectTemplateInput(**tool_input)
        
        # Get template
        template = TEMPLATES[tool_input.template]
        
        # Prepare files with variable substitution
        files = []
        for file_template in template["files"]:
            path = file_template["path"].replace("{{project_name}}", tool_input.project_name)
            content = file_template["content"].replace("{{project_name}}", tool_input.project_name)
            content = content.replace("{{description}}", tool_input.description or "A new project")
            
            # Add output_dir if specified
            if tool_input.output_dir:
                path = os.path.join(tool_input.output_dir, path)
            
            files.append({
                "path": path,
                "content": content,
            })
        
        # Use batch file write tool
        batch_tool = FileWriteBatchTool()
        batch_input = FileWriteBatchInput(
            files=files,
            overwrite=False,
        )
        
        batch_context = ToolContext(
            session_id=context.session_id,
            working_directory=context.working_directory,
        )
        
        result = await batch_tool.execute(batch_input, batch_context)
        
        # Add summary
        summary = [
            f"🎉 Project created from template: {template['name']}",
            f"📁 Project name: {tool_input.project_name}",
            f"📝 Description: {tool_input.description}",
            "",
            "Next steps:",
            f"  cd {tool_input.project_name}",
            "  pip install -e .",
            f"  {tool_input.project_name} --help",
            "",
            result.to_text(),
        ]
        
        return ToolResult.success([
            {"type": "text", "text": "\n".join(summary)}
        ])
