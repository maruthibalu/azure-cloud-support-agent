from typing import Optional
from pydantic import BaseModel, Field


class Solution(BaseModel):
    """Data model for a knowledge base solution"""
    article_id: str = Field(..., description="Unique article identifier")
    title: str = Field(..., description="Solution title")
    category: str = Field(..., description="Solution category")
    keywords: list[str] = Field(..., description="Keywords for search")
    solution_summary: str = Field(..., description="Brief summary of the solution")
    steps: list[str] = Field(..., description="Step-by-step instructions")
    prerequisites: Optional[list[str]] = Field(None, description="Prerequisites")
    related_articles: Optional[list[str]] = Field(None, description="Related article IDs")

    # Search helper
    relevance_score: float = Field(0.0, description="Search relevance score (0-1)")

    class Config:
        use_enum_values = True
