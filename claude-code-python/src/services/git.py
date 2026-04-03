"""Git service for version control operations"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class GitStatus:
    """Git repository status"""
    branch: str
    ahead: int = 0
    behind: int = 0
    staged: list[str] = field(default_factory=list)
    unstaged: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)


@dataclass
class GitCommit:
    """Git commit information"""
    hash: str
    short_hash: str
    author: str
    email: str
    date: datetime
    message: str
    parent: str | None = None


@dataclass
class GitDiff:
    """Git diff information"""
    file_path: str
    additions: int
    deletions: int
    patch: str


class GitService:
    """
    Git service for version control operations.
    
    Features:
    - Status checking
    - Commit operations
    - Push/Pull
    - Branch management
    - Diff viewing
    - History browsing
    """
    
    def __init__(self, repo_path: str | Path | None = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self._is_repo: bool | None = None
    
    @property
    def is_repo(self) -> bool:
        """Check if current directory is a git repo"""
        if self._is_repo is None:
            self._is_repo = self._check_repo()
        return self._is_repo
    
    def _check_repo(self) -> bool:
        """Check if directory is a git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run git command"""
        cmd = ["git"] + args
        logger.debug("Running git command", cmd=cmd)
        
        result = subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        
        if check and result.returncode != 0:
            raise GitError(f"Git command failed: {result.stderr.strip()}")
        
        return result
    
    async def status(self) -> GitStatus:
        """Get repository status"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        # Get current branch
        branch_result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
        branch = branch_result.stdout.strip()
        
        # Get remote tracking info
        ahead = behind = 0
        try:
            result = self._run(["rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"])
            parts = result.stdout.strip().split()
            if len(parts) == 2:
                behind, ahead = map(int, parts)
        except GitError:
            pass
        
        # Get staged files
        staged_result = self._run(["diff", "--cached", "--name-only"])
        staged = [f for f in staged_result.stdout.strip().split("\n") if f]
        
        # Get unstaged files
        unstaged_result = self._run(["diff", "--name-only"])
        unstaged = [f for f in unstaged_result.stdout.strip().split("\n") if f]
        
        # Get untracked files
        untracked_result = self._run(["ls-files", "--others", "--exclude-standard"])
        untracked = [f for f in untracked_result.stdout.strip().split("\n") if f]
        
        return GitStatus(
            branch=branch,
            ahead=ahead,
            behind=behind,
            staged=staged,
            unstaged=unstaged,
            untracked=untracked,
        )
    
    async def add(self, files: list[str] | Literal["."]) -> str:
        """Stage files"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["add"]
        if isinstance(files, str) and files == ".":
            args.append(".")
        else:
            args.extend(files)
        
        self._run(args)
        
        return f"Staged {len(files) if isinstance(files, list) else 'all'} files"
    
    async def commit(self, message: str, amend: bool = False) -> GitCommit:
        """Create a commit"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["commit", "-m", message]
        if amend:
            args.append("--amend")
        
        self._run(args)
        
        # Get commit info
        return await self.get_latest_commit()
    
    async def push(
        self,
        remote: str = "origin",
        branch: str | None = None,
    ) -> str:
        """Push commits to remote"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        if branch is None:
            branch_result = self._run(["rev-parse", "--abbrev-ref", "HEAD"])
            branch = branch_result.stdout.strip()
        
        args = ["push", remote, branch]
        result = self._run(args)
        
        return result.stdout.strip() or "Pushed successfully"
    
    async def pull(
        self,
        remote: str = "origin",
        branch: str | None = None,
    ) -> str:
        """Pull changes from remote"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["pull", remote]
        if branch:
            args.append(branch)
        
        result = self._run(args)
        
        return result.stdout.strip() or "Pulled successfully"
    
    async def get_latest_commit(self) -> GitCommit:
        """Get latest commit info"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        result = self._run([
            "log", "-1",
            "--format=%H|%h|%an|%ae|%ai|%s|%P"
        ])
        
        parts = result.stdout.strip().split("|")
        
        return GitCommit(
            hash=parts[0],
            short_hash=parts[1],
            author=parts[2],
            email=parts[3],
            date=datetime.fromisoformat(parts[4]),
            message=parts[5],
            parent=parts[6].split()[0] if parts[6] else None,
        )
    
    async def get_diff(self, file_path: str | None = None) -> list[GitDiff]:
        """Get diff of staged changes"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["diff", "--cached", "--numstat"]
        if file_path:
            args.append("--")
            args.append(file_path)
        
        result = self._run(args)
        
        diffs = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                additions, deletions, path = int(parts[0]), int(parts[1]), parts[2]
                
                # Get patch
                patch_result = self._run([
                    "diff", "--cached", "--", path
                ])
                
                diffs.append(GitDiff(
                    file_path=path,
                    additions=additions,
                    deletions=deletions,
                    patch=patch_result.stdout,
                ))
        
        return diffs
    
    async def get_log(self, limit: int = 10) -> list[GitCommit]:
        """Get commit history"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        result = self._run([
            "log", f"-{limit}",
            "--format=%H|%h|%an|%ae|%ai|%s|%P"
        ])
        
        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|")
            commits.append(GitCommit(
                hash=parts[0],
                short_hash=parts[1],
                author=parts[2],
                email=parts[3],
                date=datetime.fromisoformat(parts[4]),
                message=parts[5],
                parent=parts[6].split()[0] if parts[6] else None,
            ))
        
        return commits
    
    async def create_branch(self, name: str, start_point: str | None = None) -> str:
        """Create a new branch"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["branch", name]
        if start_point:
            args.append(start_point)
        
        self._run(args)
        
        return f"Created branch: {name}"
    
    async def checkout(self, branch: str, create: bool = False) -> str:
        """Checkout a branch"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        args = ["checkout"]
        if create:
            args.append("-b")
        args.append(branch)
        
        self._run(args)
        
        return f"Switched to branch: {branch}"
    
    async def get_remote_url(self, remote: str = "origin") -> str | None:
        """Get remote URL"""
        
        if not self.is_repo:
            raise GitError("Not a git repository")
        
        try:
            result = self._run(["remote", "get-url", remote])
            return result.stdout.strip()
        except GitError:
            return None
    
    async def get_stats(self) -> dict[str, Any]:
        """Get repository statistics"""
        
        if not self.is_repo:
            return {"is_repo": False}
        
        status = await self.status()
        latest_commit = await self.get_latest_commit()
        
        return {
            "is_repo": True,
            "path": str(self.repo_path),
            "branch": status.branch,
            "ahead": status.ahead,
            "behind": status.behind,
            "staged_count": len(status.staged),
            "unstaged_count": len(status.unstaged),
            "untracked_count": len(status.untracked),
            "latest_commit": {
                "hash": latest_commit.short_hash,
                "message": latest_commit.message,
                "author": latest_commit.author,
            },
        }


class GitError(Exception):
    """Git operation error"""
    pass
