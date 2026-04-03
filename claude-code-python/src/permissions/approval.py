"""Approval management for permission requests"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)


class ApprovalStatus(Enum):
    """Status of an approval request"""
    
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """
    A request for user approval.
    
    Attributes:
        id: Unique identifier
        tool_name: Tool requesting approval
        tool_input: Tool input data
        resource: Resource being accessed
        reason: Why approval is needed
        created_at: Request creation time
        expires_at: Request expiration time
        status: Current status
        response: User's response (if any)
    """
    
    id: str
    tool_name: str
    tool_input: dict[str, Any]
    resource: str | None = None
    command: str | None = None
    reason: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    response: str | None = None
    responded_at: datetime | None = None
    
    @property
    def is_pending(self) -> bool:
        """Check if request is still pending"""
        return self.status == ApprovalStatus.PENDING
    
    @property
    def is_expired(self) -> bool:
        """Check if request has expired"""
        if self.expires_at and datetime.now() > self.expires_at:
            return True
        return False
    
    def approve(self, response: str | None = None) -> None:
        """Mark request as approved"""
        self.status = ApprovalStatus.APPROVED
        self.response = response
        self.responded_at = datetime.now()
        logger.info("Approval request approved", id=self.id)
    
    def deny(self, response: str | None = None) -> None:
        """Mark request as denied"""
        self.status = ApprovalStatus.DENIED
        self.response = response
        self.responded_at = datetime.now()
        logger.info("Approval request denied", id=self.id)
    
    def cancel(self) -> None:
        """Cancel the request"""
        self.status = ApprovalStatus.CANCELLED
        self.responded_at = datetime.now()
        logger.info("Approval request cancelled", id=self.id)
    
    def expire(self) -> None:
        """Mark request as expired"""
        self.status = ApprovalStatus.EXPIRED
        logger.info("Approval request expired", id=self.id)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "resource": self.resource,
            "command": self.command,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.value,
            "response": self.response,
        }
    
    def __str__(self) -> str:
        return f"ApprovalRequest({self.id}, {self.tool_name}, {self.status.value})"


@dataclass
class ApprovalConfig:
    """Configuration for approval manager"""
    
    # Timeout settings
    default_timeout_seconds: int = 300  # 5 minutes
    max_timeout_seconds: int = 3600  # 1 hour
    
    # Memory settings
    max_pending_requests: int = 100
    history_retention_minutes: int = 60
    
    # Callback settings
    on_request_callback: Callable[[ApprovalRequest], None] | None = None
    on_response_callback: Callable[[ApprovalRequest], None] | None = None


class ApprovalManager:
    """
    Manager for handling approval requests.
    
    Features:
    - Create and track approval requests
    - Timeout handling
    - Response callbacks
    - Request history
    
    Usage:
        manager = ApprovalManager()
        
        # Create request
        request = manager.create_request(
            tool_name="bash",
            tool_input={"command": "rm -rf test"},
            reason="Dangerous command",
        )
        
        # Wait for response (async)
        result = await manager.wait_for_approval(request.id)
        
        if result.status == ApprovalStatus.APPROVED:
            # Execute
        else:
            # Deny
    """
    
    def __init__(self, config: ApprovalConfig | None = None):
        self.config = config or ApprovalConfig()
        self._requests: dict[str, ApprovalRequest] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._cleanup_task: asyncio.Task | None = None
    
    @property
    def pending_count(self) -> int:
        """Get count of pending requests"""
        return sum(1 for r in self._requests.values() if r.is_pending)
    
    @property
    def pending_requests(self) -> list[ApprovalRequest]:
        """Get all pending requests"""
        return [r for r in self._requests.values() if r.is_pending]
    
    @property
    def recent_requests(self) -> list[ApprovalRequest]:
        """Get recent requests (sorted by creation time)"""
        return sorted(
            self._requests.values(),
            key=lambda r: r.created_at,
            reverse=True,
        )[:20]
    
    async def start(self) -> None:
        """Start the approval manager (background cleanup)"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Approval manager started")
    
    async def stop(self) -> None:
        """Stop the approval manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Approval manager stopped")
    
    def create_request(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        resource: str | None = None,
        command: str | None = None,
        reason: str = "",
        timeout_seconds: int | None = None,
    ) -> ApprovalRequest:
        """
        Create a new approval request.
        
        Args:
            tool_name: Name of the requesting tool
            tool_input: Tool input data
            resource: Resource being accessed
            command: Command string (for bash)
            reason: Why approval is needed
            timeout_seconds: Request timeout
        
        Returns:
            New ApprovalRequest
        """
        import uuid
        
        # Determine timeout
        timeout = timeout_seconds or self.config.default_timeout_seconds
        timeout = min(timeout, self.config.max_timeout_seconds)
        
        # Create request
        from datetime import timedelta
        
        request = ApprovalRequest(
            id=str(uuid.uuid4())[:8],
            tool_name=tool_name,
            tool_input=tool_input,
            resource=resource,
            command=command,
            reason=reason,
            expires_at=datetime.now() + timedelta(seconds=timeout),
        )
        
        # Store request
        self._requests[request.id] = request
        self._events[request.id] = asyncio.Event()
        
        # Check limit
        if self.pending_count > self.config.max_pending_requests:
            # Cancel oldest pending request
            pending = self.pending_requests
            if pending:
                oldest = pending[-1]
                oldest.cancel()
                logger.warning(
                    "Cancelled oldest approval request due to limit",
                    id=oldest.id,
                )
        
        # Notify callback
        if self.config.on_request_callback:
            try:
                self.config.on_request_callback(request)
            except Exception as e:
                logger.error("Error in on_request_callback", error=str(e))
        
        logger.info(
            "Approval request created",
            id=request.id,
            tool=tool_name,
            timeout=timeout,
        )
        
        return request
    
    def get_request(self, request_id: str) -> ApprovalRequest | None:
        """Get a request by ID"""
        return self._requests.get(request_id)
    
    def approve(self, request_id: str, response: str | None = None) -> bool:
        """
        Approve a request.
        
        Args:
            request_id: Request ID
            response: Optional response message
        
        Returns:
            True if request was found and approved
        """
        request = self.get_request(request_id)
        if not request:
            return False
        
        if not request.is_pending:
            logger.warning("Cannot approve non-pending request", id=request_id)
            return False
        
        request.approve(response)
        self._signal_response(request_id)
        return True
    
    def deny(self, request_id: str, response: str | None = None) -> bool:
        """
        Deny a request.
        
        Args:
            request_id: Request ID
            response: Optional response message
        
        Returns:
            True if request was found and denied
        """
        request = self.get_request(request_id)
        if not request:
            return False
        
        if not request.is_pending:
            logger.warning("Cannot deny non-pending request", id=request_id)
            return False
        
        request.deny(response)
        self._signal_response(request_id)
        return True
    
    async def wait_for_approval(
        self,
        request_id: str,
        timeout: float | None = None,
    ) -> ApprovalRequest:
        """
        Wait for a request to be resolved.
        
        Args:
            request_id: Request ID
            timeout: Wait timeout (uses request timeout if not specified)
        
        Returns:
            Resolved ApprovalRequest
        """
        request = self.get_request(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        event = self._events.get(request_id)
        if not event:
            return request
        
        # Calculate timeout
        if timeout is None and request.expires_at:
            timeout = (request.expires_at - datetime.now()).total_seconds()
            timeout = max(0, timeout)
        
        try:
            await asyncio.wait_for(event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            request.expire()
            logger.info("Approval request timed out", id=request_id)
        
        return request
    
    def _signal_response(self, request_id: str) -> None:
        """Signal that a request has been resolved"""
        event = self._events.get(request_id)
        if event:
            event.set()
        
        # Notify callback
        request = self.get_request(request_id)
        if request and self.config.on_response_callback:
            try:
                self.config.on_response_callback(request)
            except Exception as e:
                logger.error("Error in on_response_callback", error=str(e))
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup of expired requests"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                expired = [
                    r for r in self._requests.values()
                    if r.expires_at and r.is_pending and now > r.expires_at
                ]
                
                for request in expired:
                    request.expire()
                    self._signal_response(request.id)
                
                # Clean up old history
                cutoff = now - asyncio.get_event_loop().time().__class__().fromtimestamp(self.config.history_retention_minutes * 60).__class__().utcfromtimestamp(0).__class__()
                
                # Fix: proper cutoff calculation
                from datetime import timedelta
                cutoff = now - timedelta(minutes=self.config.history_retention_minutes)
                
                old_ids = [
                    rid for rid, r in self._requests.items()
                    if r.responded_at and r.responded_at < cutoff
                ]
                
                for rid in old_ids:
                    del self._requests[rid]
                    if rid in self._events:
                        del self._events[rid]
                
                if expired:
                    logger.info("Cleaned up expired requests", count=len(expired))
                if old_ids:
                    logger.debug("Cleaned up old history", count=len(old_ids))
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in cleanup loop", error=str(e))
    
    def list_requests(
        self,
        status: ApprovalStatus | None = None,
        limit: int = 20,
    ) -> list[ApprovalRequest]:
        """List requests with optional status filter"""
        requests = list(self._requests.values())
        
        if status:
            requests = [r for r in requests if r.status == status]
        
        return sorted(requests, key=lambda r: r.created_at, reverse=True)[:limit]
    
    def clear_history(self) -> int:
        """Clear resolved request history"""
        resolved_ids = [
            rid for rid, r in self._requests.items()
            if not r.is_pending
        ]
        
        for rid in resolved_ids:
            del self._requests[rid]
            if rid in self._events:
                del self._events[rid]
        
        logger.info("Cleared resolved request history", count=len(resolved_ids))
        return len(resolved_ids)
    
    def __repr__(self) -> str:
        return f"ApprovalManager(pending={self.pending_count}, total={len(self._requests)})"
