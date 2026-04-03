"""Git tool for version control operations"""

from __future__ import annotations

from typing import Any, Literal

import structlog

from .base import Tool, ToolContext, ValidationResult
from ..models.tools import ToolInput, ToolResult
from ..services.git import GitService, GitError

logger = structlog.get_logger(__name__)


class GitInput(ToolInput):
    """Input for Git tool"""
    
    operation: Literal[
        "status", "add", "commit", "push", "pull",
        "diff", "log", "branch", "checkout"
    ]
    files: list[str] | None = None
    message: str | None = None
    branch: str | None = None
    repo_path: str | None = None
    amend: bool = False
    limit: int = 10


class GitTool(Tool[GitInput]):
    """
    Tool for Git version control operations.
    
    Features:
    - Status checking
    - Stage/Add files
    - Commit with message
    - Push/Pull remote
    - View diffs
    - Commit history
    - Branch management
    """
    
    name = "git"
    description = "Perform Git version control operations"
    
    input_schema = {
        "type": "object",
        "properties": {
            "operation": {
                "type": "string",
                "enum": ["status", "add", "commit", "push", "pull", "diff", "log", "branch", "checkout"],
                "description": "Git operation to perform"
            },
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Files to operate on (for add)"
            },
            "message": {
                "type": "string",
                "description": "Commit message (for commit)"
            },
            "branch": {
                "type": "string",
                "description": "Branch name (for push/pull/branch/checkout)"
            },
            "repo_path": {
                "type": "string",
                "description": "Repository path (default: current directory)"
            },
            "amend": {
                "type": "boolean",
                "description": "Amend last commit (for commit)"
            },
            "limit": {
                "type": "integer",
                "description": "Number of commits to show (for log)"
            }
        },
        "required": ["operation"]
    }
    
    def get_prompt(self) -> str:
        """Get prompt describing how to use this tool"""
        return """Use the `git` tool to perform version control operations.

Operations:
- status: Check repository status
- add: Stage files (files: ["file1", "file2"] or ".")
- commit: Create commit (message: "commit message")
- push: Push to remote (branch: "main")
- pull: Pull from remote
- diff: View staged changes
- log: View commit history (limit: 10)
- branch: Create branch (branch: "feature")
- checkout: Switch branch (branch: "main")

Examples:

Check status:
{
    "operation": "status"
}

Stage all files:
{
    "operation": "add",
    "files": ["."]
}

Commit:
{
    "operation": "commit",
    "message": "Add new feature"
}

Push to remote:
{
    "operation": "push",
    "branch": "main"
}"""
    
    async def validate_input(
        self,
        tool_input: dict,
        context: ToolContext,
    ) -> ValidationResult:
        """Validate git input"""
        
        operation = tool_input.get("operation")
        
        if not operation:
            return ValidationResult.fail("Operation is required")
        
        # Check operation-specific requirements
        if operation == "commit" and not tool_input.get("message"):
            return ValidationResult.fail("Commit message is required")
        
        if operation == "add" and not tool_input.get("files"):
            return ValidationResult.fail("Files to add are required")
        
        return ValidationResult.ok()
    
    async def execute(self, tool_input: GitInput, context: ToolContext) -> ToolResult:
        """Execute git operation"""
        
        repo_path = tool_input.repo_path or context.working_directory
        
        logger.info(
            "Git operation requested",
            operation=tool_input.operation,
            repo_path=repo_path,
        )
        
        try:
            git = GitService(repo_path)
            
            if not git.is_repo:
                return ToolResult.error("Not a git repository")
            
            result = await self._execute_operation(git, tool_input)
            
            return ToolResult.success([
                {"type": "text", "text": result}
            ])
            
        except GitError as e:
            logger.warning("Git operation failed", error=str(e))
            return ToolResult.error(str(e))
        except Exception as e:
            logger.exception("Git error")
            return ToolResult.error(f"Git error: {str(e)}")
    
    async def _execute_operation(self, git: GitService, input: GitInput) -> str:
        """Execute specific git operation"""
        
        op = input.operation
        
        if op == "status":
            return await self._status(git)
        elif op == "add":
            return await self._add(git, input.files or [])
        elif op == "commit":
            return await self._commit(git, input.message or "", input.amend)
        elif op == "push":
            return await self._push(git, input.branch)
        elif op == "pull":
            return await self._pull(git, input.branch)
        elif op == "diff":
            return await self._diff(git)
        elif op == "log":
            return await self._log(git, input.limit)
        elif op == "branch":
            return await self._branch(git, input.branch)
        elif op == "checkout":
            return await self._checkout(git, input.branch)
        else:
            raise GitError(f"Unknown operation: {op}")
    
    async def _status(self, git: GitService) -> str:
        """Get repository status"""
        status = await git.status()
        
        lines = [
            f"📍 Branch: **{status.branch}**",
        ]
        
        if status.ahead or status.behind:
            lines.append(f"📡 Remote: +{status.ahead} ahead, -{status.behind} behind")
        
        if status.staged:
            lines.append(f"\n✅ Staged ({len(status.staged)}):")
            for f in status.staged[:10]:
                lines.append(f"   - {f}")
            if len(status.staged) > 10:
                lines.append(f"   ... and {len(status.staged) - 10} more")
        
        if status.unstaged:
            lines.append(f"\n📝 Modified ({len(status.unstaged)}):")
            for f in status.unstaged[:10]:
                lines.append(f"   - {f}")
        
        if status.untracked:
            lines.append(f"\n❓ Untracked ({len(status.untracked)}):")
            for f in status.untracked[:10]:
                lines.append(f"   - {f}")
        
        if not any([status.staged, status.unstaged, status.untracked]):
            lines.append("\n✨ Working tree clean")
        
        return "\n".join(lines)
    
    async def _add(self, git: GitService, files: list[str]) -> str:
        """Stage files"""
        result = await git.add(files)
        return f"✅ {result}"
    
    async def _commit(self, git: GitService, message: str, amend: bool) -> str:
        """Create commit"""
        commit = await git.commit(message, amend)
        
        return (
            f"✅ Committed: {commit.short_hash}\n"
            f"📝 {commit.message}\n"
            f"👤 {commit.author}"
        )
    
    async def _push(self, git: GitService, branch: str | None) -> str:
        """Push to remote"""
        result = await git.push(branch=branch)
        return f"✅ {result}"
    
    async def _pull(self, git: GitService, branch: str | None) -> str:
        """Pull from remote"""
        result = await git.pull(branch=branch)
        return f"✅ {result}"
    
    async def _diff(self, git: GitService) -> str:
        """View staged changes"""
        diffs = await git.get_diff()
        
        if not diffs:
            return "📭 No staged changes"
        
        lines = [f"📊 Staged changes ({len(diffs)} files):"]
        
        for diff in diffs[:5]:
            lines.append(
                f"\n📄 {diff.file_path} "
                f"(+{diff.additions}/-{diff.deletions})"
            )
            # Show first few lines of patch
            patch_lines = diff.patch.split("\n")[:10]
            for line in patch_lines:
                if line.startswith("+") or line.startswith("-"):
                    lines.append(f"  `{line}`")
        
        if len(diffs) > 5:
            lines.append(f"\n... and {len(diffs) - 5} more files")
        
        return "\n".join(lines)
    
    async def _log(self, git: GitService, limit: int) -> str:
        """View commit history"""
        commits = await git.get_log(limit)
        
        if not commits:
            return "📭 No commits found"
        
        lines = [f"📜 Recent commits ({len(commits)}):"]
        
        for commit in commits:
            lines.append(
                f"\n`{commit.short_hash}` - {commit.message[:50]}"
                f"\n   👤 {commit.author} • {commit.date.strftime('%Y-%m-%d %H:%M')}"
            )
        
        return "\n".join(lines)
    
    async def _branch(self, git: GitService, branch: str | None) -> str:
        """Create branch"""
        if not branch:
            raise GitError("Branch name is required")
        
        result = await git.create_branch(branch)
        return f"✅ {result}"
    
    async def _checkout(self, git: GitService, branch: str | None) -> str:
        """Switch branch"""
        if not branch:
            raise GitError("Branch name is required")
        
        result = await git.checkout(branch)
        return f"✅ {result}"
