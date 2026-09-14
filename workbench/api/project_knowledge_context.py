"""Inspectable API for controlled project knowledge context."""

from typing import Protocol

from fastapi import APIRouter, Header, HTTPException, Path

from workbench.application.project_knowledge_context_service import ProjectKnowledgeContextService
from workbench.domain.knowledge import ProjectKnowledgeContext, ProjectKnowledgeContextPolicy


class _ContextServiceFactory(Protocol):
    def __call__(self, actor_id: str) -> ProjectKnowledgeContextService: ...


def create_project_knowledge_context_router(*, service_factory: _ContextServiceFactory) -> APIRouter:
    router = APIRouter(prefix="/api/v1/projects", tags=["knowledge-context"])

    @router.get("/{project_id}/knowledge-context", response_model=ProjectKnowledgeContext)
    async def get_context(
        project_id: str = Path(min_length=1, max_length=255),
        x_user_id: str = Header(default=""),
    ):
        actor_id = x_user_id.strip()
        if not actor_id or len(actor_id) > 255:
            raise HTTPException(status_code=401, detail="X-User-ID is required")
        try:
            return service_factory(actor_id).build(
                project_id=project_id, policy=ProjectKnowledgeContextPolicy(),
            )
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error

    return router
