"""
Agentic AI Analysis Engine for SafarAI
Uses Emergent LLM (GPT-5.2) for intelligent analysis
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage
from agentic_models import (
    ImpactScenario, DashboardWidget, ActionItem, 
    Approval, TrendForecast, AgenticInsight
)

logger = logging.getLogger(__name__)

# ========================
# AI ANALYSIS FUNCTIONS
# ========================

async def analyze_impact_scenarios(events: List[Dict], run_data: Dict) -> List[ImpactScenario]:
    """Generate impact scenarios from events using AI"""
    try:
        if not events:
            return []
        
        system_prompt = """You are a strategic intelligence analyst for the tourism industry.
Analyze the provided events and generate 3-5 impact scenarios.

Return ONLY valid JSON array with NO markdown, NO code blocks:
[
  {
    "scenario_name": "string",
    "description": "detailed scenario description",
    "probability": 0.0-1.0,
    "impact_level": "low|medium|high|critical",
    "assumptions": ["assumption 1", "assumption 2"],
    "potential_outcomes": ["outcome 1", "outcome 2"],
    "confidence_score": 0.0-1.0
  }
]"""
        
        events_summary = []
        for e in events[:10]:  # Limit to 10 events
            events_summary.append({
                "company": e.get("company"),
                "event_type": e.get("event_type"),
                "title": e.get("title"),
                "summary": e.get("summary")
            })
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"impact-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Events:\n{json.dumps(events_summary, indent=2)}\n\nGenerate impact scenarios."
        )
        
        response = await chat.send_message(user_message)
        
        # Clean response
        response_text = response.strip()
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        # Find JSON array
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        scenarios_data = json.loads(response_text)
        return [ImpactScenario(**s) for s in scenarios_data[:5]]
        
    except Exception as e:
        logger.error(f"Impact analysis error: {e}")
        return []


async def generate_dashboard_recommendations(events: List[Dict]) -> List[DashboardWidget]:
    """Generate dashboard widget recommendations using AI"""
    try:
        if not events:
            return []
        
        system_prompt = """You are a data visualization expert for executive dashboards.
Analyze events and recommend 4-6 dashboard widgets.

Return ONLY valid JSON array:
[
  {
    "widget_type": "chart|metric|table|alert",
    "title": "widget title",
    "description": "what this widget shows",
    "data_source": "data source description",
    "priority": "P0|P1|P2",
    "template": {
      "chart_type": "line|bar|pie|gauge",
      "metrics": ["metric1", "metric2"],
      "filters": ["filter1"]
    }
  }
]"""
        
        event_types = {}
        for e in events:
            et = e.get("event_type", "other")
            event_types[et] = event_types.get(et, 0) + 1
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"dashboard-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Event distribution: {json.dumps(event_types)}\nTotal events: {len(events)}\n\nRecommend dashboard widgets."
        )
        
        response = await chat.send_message(user_message)
        
        # Clean response
        response_text = response.strip()
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        widgets_data = json.loads(response_text)
        return [DashboardWidget(**w) for w in widgets_data[:6]]
        
    except Exception as e:
        logger.error(f"Dashboard recommendation error: {e}")
        return []


async def generate_action_items(events: List[Dict], run_id: str, team_members: List[Dict]) -> List[ActionItem]:
    """Generate prioritized action items with AI-based role assignment"""
    try:
        if not events:
            return []
        
        # Create role mapping
        role_map = {}
        for member in team_members:
            role = member.get("role_type", "analyst")
            if role not in role_map:
                role_map[role] = []
            role_map[role].append(member)
        
        system_prompt = """You are a task management AI for tourism intelligence.
Generate 5-10 prioritized action items based on events.

Assign tasks to roles: analyst, executive, marketing, risk

Return ONLY valid JSON array:
[
  {
    "title": "task title",
    "description": "detailed description",
    "priority": "P0|P1|P2",
    "assigned_role": "analyst|executive|marketing|risk",
    "due_date": "YYYY-MM-DD",
    "reasoning": "why this task matters",
    "related_events": ["event_id1", "event_id2"]
  }
]"""
        
        events_for_tasks = []
        for e in events[:15]:
            events_for_tasks.append({
                "id": e.get("id"),
                "company": e.get("company"),
                "event_type": e.get("event_type"),
                "title": e.get("title"),
                "why_it_matters": e.get("why_it_matters")
            })
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"tasks-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Events:\n{json.dumps(events_for_tasks, indent=2)}\n\nAvailable roles: {list(role_map.keys())}\n\nGenerate action items."
        )
        
        response = await chat.send_message(user_message)
        
        # Clean response
        response_text = response.strip()
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        tasks_data = json.loads(response_text)
        
        # Create action items and auto-assign to team members
        action_items = []
        for task in tasks_data[:10]:
            assigned_role = task.get("assigned_role", "analyst")
            assigned_to = None
            
            # Round-robin assignment within role
            if assigned_role in role_map and role_map[assigned_role]:
                assigned_to = role_map[assigned_role][len(action_items) % len(role_map[assigned_role])].get("id")
            
            action_item = ActionItem(
                run_id=run_id,
                title=task.get("title", ""),
                description=task.get("description", ""),
                priority=task.get("priority", "P2"),
                assigned_role=assigned_role,
                assigned_to=assigned_to,
                due_date=task.get("due_date"),
                reasoning=task.get("reasoning", ""),
                related_events=task.get("related_events", [])
            )
            action_items.append(action_item)
        
        return action_items
        
    except Exception as e:
        logger.error(f"Action items generation error: {e}")
        return []


async def generate_approvals(events: List[Dict], run_id: str, run_data: Dict) -> List[Approval]:
    """Generate approval suggestions for executable actions"""
    try:
        if not events:
            return []
        
        system_prompt = """You are an automation advisor for intelligence platforms.
Suggest 3-5 executable actions that require approval.

Action types: send_email, add_source, schedule_monitoring, export_csv, send_alert

Return ONLY valid JSON array:
[
  {
    "action_type": "send_email|add_source|schedule_monitoring|export_csv|send_alert",
    "title": "action title",
    "description": "what this action does",
    "reasoning": "why recommend this",
    "confidence": 0.0-1.0,
    "parameters": {
      "key": "value"
    }
  }
]"""
        
        summary = {
            "events_created": len(events),
            "high_priority": len([e for e in events if e.get("materiality_score", 0) >= 70]),
            "event_types": list(set([e.get("event_type") for e in events]))
        }
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"approvals-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Run summary:\n{json.dumps(summary, indent=2)}\n\nSuggest approval actions."
        )
        
        response = await chat.send_message(user_message)
        
        # Clean response
        response_text = response.strip()
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        approvals_data = json.loads(response_text)
        
        approvals = []
        for approval in approvals_data[:5]:
            approvals.append(Approval(
                run_id=run_id,
                action_type=approval.get("action_type", "send_alert"),
                title=approval.get("title", ""),
                description=approval.get("description", ""),
                reasoning=approval.get("reasoning", ""),
                confidence=approval.get("confidence", 0.5),
                parameters=approval.get("parameters", {})
            ))
        
        return approvals
        
    except Exception as e:
        logger.error(f"Approvals generation error: {e}")
        return []


async def forecast_trends(events: List[Dict], run_id: str) -> List[TrendForecast]:
    """Predict tourism trends using event patterns"""
    try:
        if not events or len(events) < 3:
            return []
        
        system_prompt = """You are a tourism industry trend analyst with predictive capabilities.
Analyze events and forecast 3-5 emerging trends.

Categories: partnerships, funding, pricing, technology, destinations

Return ONLY valid JSON array:
[
  {
    "trend_category": "partnerships|funding|pricing|technology|destinations",
    "trend_name": "trend name",
    "description": "detailed trend description",
    "forecast_horizon": "next_quarter|next_6_months|next_year",
    "confidence": 0.0-1.0,
    "supporting_events": ["event_id1"],
    "key_indicators": ["indicator 1", "indicator 2"],
    "potential_impact": "impact description",
    "recommended_actions": ["action 1", "action 2"]
  }
]"""
        
        events_for_forecast = []
        for e in events:
            events_for_forecast.append({
                "id": e.get("id"),
                "company": e.get("company"),
                "event_type": e.get("event_type"),
                "title": e.get("title"),
                "summary": e.get("summary"),
                "key_entities": e.get("key_entities", {})
            })
        
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY', ''),
            session_id=f"trends-{uuid.uuid4()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(
            text=f"Historical events:\n{json.dumps(events_for_forecast, indent=2)}\n\nForecast emerging trends."
        )
        
        response = await chat.send_message(user_message)
        
        # Clean response
        response_text = response.strip()
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        json_start = response_text.find("[")
        json_end = response_text.rfind("]") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        trends_data = json.loads(response_text)
        
        forecasts = []
        for trend in trends_data[:5]:
            forecasts.append(TrendForecast(
                run_id=run_id,
                trend_category=trend.get("trend_category", "partnerships"),
                trend_name=trend.get("trend_name", ""),
                description=trend.get("description", ""),
                forecast_horizon=trend.get("forecast_horizon", "next_quarter"),
                confidence=trend.get("confidence", 0.5),
                supporting_events=trend.get("supporting_events", []),
                key_indicators=trend.get("key_indicators", []),
                potential_impact=trend.get("potential_impact", ""),
                recommended_actions=trend.get("recommended_actions", [])
            ))
        
        return forecasts
        
    except Exception as e:
        logger.error(f"Trend forecasting error: {e}")
        return []


# ========================
# MAIN ORCHESTRATION
# ========================

async def generate_agentic_insights(
    run_id: str, 
    events: List[Dict], 
    run_data: Dict,
    team_members: List[Dict],
    db
) -> Optional[str]:
    """
    Main orchestration function that generates all agentic insights
    Returns insight_id if successful
    """
    try:
        start_time = datetime.now(timezone.utc)
        logger.info(f"Starting agentic analysis for run {run_id}")
        
        # Generate all insights in parallel would be ideal, but for simplicity we'll do sequential
        impact_scenarios = await analyze_impact_scenarios(events, run_data)
        dashboard_widgets = await generate_dashboard_recommendations(events)
        action_items = await generate_action_items(events, run_id, team_members)
        approvals = await generate_approvals(events, run_id, run_data)
        trend_forecasts = await forecast_trends(events, run_id)
        
        # Extract key findings
        key_findings = []
        for scenario in impact_scenarios[:3]:
            key_findings.append(f"{scenario.scenario_name}: {scenario.description[:100]}...")
        
        # Extract risk alerts
        risk_alerts = [s.scenario_name for s in impact_scenarios if s.impact_level in ["high", "critical"]]
        
        # Extract opportunities
        opportunities = [s.scenario_name for s in impact_scenarios if "opportunity" in s.description.lower()]
        
        # Create trend summary
        trend_summary = f"Identified {len(trend_forecasts)} emerging trends across {len(set([t.trend_category for t in trend_forecasts]))} categories"
        
        # Create insight document
        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        insight = AgenticInsight(
            run_id=run_id,
            impact_scenarios=impact_scenarios,
            dashboard_recommendations=dashboard_widgets,
            trend_forecasts_summary=trend_summary,
            key_findings=key_findings,
            risk_alerts=risk_alerts,
            opportunities=opportunities,
            processing_time_seconds=processing_time
        )
        
        # Store in database
        insight_doc = insight.model_dump()
        insight_doc['generated_at'] = insight_doc['generated_at'].isoformat()
        
        # Convert nested models to dicts
        insight_doc['impact_scenarios'] = [s.model_dump() for s in impact_scenarios]
        insight_doc['dashboard_recommendations'] = [w.model_dump() for w in dashboard_widgets]
        
        await db.agentic_insights.insert_one(insight_doc)
        
        # Store action items
        for item in action_items:
            item_doc = item.model_dump()
            item_doc['created_at'] = item_doc['created_at'].isoformat()
            await db.action_items.insert_one(item_doc)
        
        # Store approvals
        for approval in approvals:
            approval_doc = approval.model_dump()
            approval_doc['created_at'] = approval_doc['created_at'].isoformat()
            await db.approvals.insert_one(approval_doc)
        
        # Store trend forecasts
        for forecast in trend_forecasts:
            forecast_doc = forecast.model_dump()
            forecast_doc['created_at'] = forecast_doc['created_at'].isoformat()
            await db.trend_forecasts.insert_one(forecast_doc)
        
        logger.info(f"Agentic analysis complete for run {run_id}: {len(action_items)} tasks, {len(approvals)} approvals, {len(trend_forecasts)} trends")
        
        return insight.id
        
    except Exception as e:
        logger.error(f"Agentic insights generation error: {e}")
        import traceback
        traceback.print_exc()
        return None
