from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class DomainScore(BaseModel):
    domain: str
    video_ads_score: int = Field(..., description='Score for active video ads (0-30)')
    traffic_score: int = Field(..., description='Score for web traffic (0-25)')
    onsite_video_score: int = Field(..., description='Score for on-site video quality/presence (0-25)')
    cart_score: int = Field(..., description='Score for e-commerce cart detection (0-20)')
    total_score: int = Field(..., description='Combined match score (0-100)')
    details: Dict[str, str] = Field(default_factory=dict, description='Additional analysis findings')

class Contact(BaseModel):
    name: str
    title: str
    email: str
    linkedin: Optional[str] = None
    selected: bool = True
    source: Optional[str] = "unknown"  # apollo_verified, gemini_unverified, verified_vault, placeholder

class CaseStudy(BaseModel):
    title: str
    metric: str
    focus: str
    description: str

class OutreachDraft(BaseModel):
    persona: str
    subject: str
    body: str
    linkedin_note: Optional[str] = ""
