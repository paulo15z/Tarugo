"""
Modelos Pydantic flexíveis para respostas da API Dinabox (listagens e detalhes).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DinaboxProjectListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    projects: list[Any] = Field(default_factory=list)
    total: int = 0
    quantity: int = 10
    page: int = 1


class DinaboxProjectDetail(BaseModel):
    model_config = ConfigDict(extra="allow")


class DinaboxGroupListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    project_groups: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1


class DinaboxGroupDetail(BaseModel):
    model_config = ConfigDict(extra="allow")


class DinaboxCustomerListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    customers: list[Any] = Field(default_factory=list)
    total: int = 0


class DinaboxMaterialListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    materials: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1


class DinaboxLabelListResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    labels: list[Any] = Field(default_factory=list)
    total: int = 0
    page: int = 1
