"""Pydantic models for request/response schemas."""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class BudgetLevel(str, Enum):
    budget = "budget"
    mid_range = "mid-range"
    luxury = "luxury"


class GroupType(str, Enum):
    solo = "solo"
    couple = "couple"
    friends = "friends"
    family = "family"


class TravelPreferences(BaseModel):
    destination: Optional[str] = None
    travel_dates: Optional[str] = Field(
        default=None,
        description="Planned travel dates, e.g. 'March 2025' or '2025-03-15 to 2025-03-22'",
    )
    trip_length: Optional[str] = Field(
        default=None,
        description="Duration of the trip, e.g. '7 days', '2 weeks'",
    )
    budget_level: Optional[BudgetLevel] = Field(
        default=None,
        description="Budget level: budget, mid-range, or luxury",
    )
    travel_style: Optional[list[str]] = Field(
        default=None,
        description="Travel styles, e.g. ['adventure', 'cultural', 'relaxation']",
    )
    food_interests: Optional[list[str]] = Field(
        default=None,
        description="Food interests, e.g. ['street food', 'fine dining', 'vegetarian']",
    )
    group_type: Optional[GroupType] = Field(
        default=None,
        description="Type of travel group: solo, couple, friends, or family",
    )


class ResearchRequest(BaseModel):
    destination: str = Field(
        ...,
        description="The travel destination to research",
        min_length=1,
    )
    preferences: Optional[TravelPreferences] = Field(
        default=None,
        description="Optional travel preferences to tailor the research",
    )


class ResearchResponse(BaseModel):
    success: bool
    destination: str
    box_file_id: Optional[str] = None
    box_file_name: Optional[str] = None
    box_file_url: Optional[str] = None
    brief_preview: str = Field(
        description="First 500 characters of the generated travel brief"
    )
    message: str
