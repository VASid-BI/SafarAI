"""
Agentic AI Models for SafarAI Intelligence Platform
Additive module - does not modify existing schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid

# ========================
# TEAM MANAGEMENT
# ========================

class TeamMember(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    title: str
    email: str
    role_type: str = "analyst"  # analyst, executive, marketing, risk
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TeamMemberCreate(BaseModel):
    name: str
    title: str
    email: str
    role_type: str = "analyst"

# ========================
# IMPACT ANALYSIS
# ========================

class ImpactScenario(BaseModel):
    scenario_name: str
    description: str
    probability: float  # 0-1
    impact_level: str  # low, medium, high, critical
    assumptions: List[str]
    potential_outcomes: List[str]
    confidence_score: float  # 0-1

class DashboardWidget(BaseModel):
    widget_type: str  # chart, metric, table, alert
    title: str
    description: str
    data_source: str
    priority: str  # P0, P1, P2
    template: Dict[str, Any]

# ========================
# ACTION ITEMS
# ========================

class ActionItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    title: str
    description: str
    priority: str  # P0, P1, P2
    assigned_to: Optional[str] = None  # team member id
    assigned_role: Optional[str] = None  # analyst, executive, marketing, risk
    due_date: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, cancelled
    reasoning: str
    related_events: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class ActionItemUpdate(BaseModel):
    status: Optional[str] = None
    assigned_to: Optional[str] = None

# ========================
# APPROVAL WORKFLOW
# ========================

class Approval(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    action_type: str  # send_email, add_source, schedule_monitoring, export_csv, send_alert
    title: str
    description: str
    reasoning: str
    confidence: float  # 0-1
    parameters: Dict[str, Any]  # action-specific params
    status: str = "pending"  # pending, approved, rejected, executed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    approved_by: Optional[str] = None

# ========================
# TREND FORECASTING
# ========================

class TrendForecast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    trend_category: str  # partnerships, funding, pricing, technology, destinations
    trend_name: str
    description: str
    forecast_horizon: str  # next_quarter, next_6_months, next_year
    confidence: float  # 0-1
    supporting_events: List[str]
    key_indicators: List[str]
    potential_impact: str
    recommended_actions: List[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ========================
# AGENTIC INSIGHTS
# ========================

class AgenticInsight(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    impact_scenarios: List[ImpactScenario]
    dashboard_recommendations: List[DashboardWidget]
    trend_forecasts_summary: str
    key_findings: List[str]
    risk_alerts: List[str]
    opportunities: List[str]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_seconds: float = 0.0
