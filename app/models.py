"""Pydantic models for API responses."""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class LinkModel(BaseModel):
    """A single link within a category."""
    label: str = Field(..., description="Display label for the link")
    url: str = Field(..., description="Full URL")


class CategoryModel(BaseModel):
    """A category of links with status."""
    id: str = Field(..., description="Unique category identifier")
    label: str = Field(..., description="Display label for the category")
    icon: str = Field(..., description="Emoji icon for the category")
    status: Literal["ok", "empty", "error"] = Field(..., description="Category status")
    message: Optional[str] = Field(None, description="Status message for empty/error states")
    links: List[LinkModel] = Field(default_factory=list, description="List of links in this category")


class ResourceMetadata(BaseModel):
    """Metadata about discovered Kubernetes resources."""
    argocd_app: bool = Field(..., description="Whether ArgoCD application was found")
    deployment: bool = Field(..., description="Whether deployment was found")
    pods_found: int = Field(..., description="Number of pods found")
    external_secrets_found: int = Field(..., description="Number of ExternalSecrets found")


class ResponseMetadata(BaseModel):
    """Response metadata."""
    generated_at: datetime = Field(..., description="When this response was generated")
    version: str = Field(default="v1", description="API version")
    resources: ResourceMetadata = Field(..., description="Resource discovery metadata")


class LinksResponse(BaseModel):
    """Complete response model for links API."""
    app_name: str = Field(..., description="ArgoCD application name")
    namespace: str = Field(..., description="Kubernetes namespace")
    service_name: str = Field(..., description="Derived service name from application name")
    last_updated: datetime = Field(..., description="When this data was last updated (UTC)")
    categories: List[CategoryModel] = Field(..., description="List of link categories")
    metadata: ResponseMetadata = Field(..., description="Response metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(default="v1", description="API version")


class ReadyResponse(BaseModel):
    """Readiness check response."""
    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict = Field(..., description="Individual component readiness")
    timestamp: datetime = Field(..., description="Current timestamp")
