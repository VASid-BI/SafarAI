import { useState, useEffect } from "react";
import axios from "axios";
import { 
  Brain, CheckCircle2, Clock, AlertTriangle, TrendingUp, 
  Users, Target, Zap, ArrowRight, ChevronRight, Sparkles,
  ThumbsUp, ThumbsDown, Loader2, User, Calendar, Flag,
  BarChart3, Activity, Send, Plus, FileText, Shield
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// ========================
// INSIGHTS PAGE
// ========================
export const InsightsPage = () => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const response = await axios.get(`${API}/agentic/insights/latest`);
      setInsights(response.data);
    } catch (e) {
      console.error("Failed to fetch insights:", e);
    } finally {
      setLoading(false);
    }
  };

  const generateInsights = async () => {
    try {
      setGenerating(true);
      toast.info("Generating AI insights...", { description: "This may take 30-60 seconds" });
      const response = await axios.post(`${API}/agentic/generate`);
      toast.success("Insights generated successfully!", { 
        description: `Analyzed ${response.data.events_analyzed} events` 
      });
      setTimeout(() => fetchInsights(), 2000);
    } catch (e) {
      toast.error("Failed to generate insights", { 
        description: e.response?.data?.detail || "Unknown error" 
      });
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  if (!insights || insights.message) {
    return (
      <div className="space-y-8 noise-bg" data-testid="insights-page">
        <div className="flex flex-col items-center justify-center h-[60vh] text-center">
          <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mb-6">
            <Brain className="text-white/60" size={40} />
          </div>
          <h2 className="text-3xl font-bold mb-3">No Insights Yet</h2>
          <p className="text-white/40 mb-8 max-w-md">
            Generate AI-powered insights to get impact analysis, trend forecasts, and recommendations
          </p>
          <button 
            onClick={generateInsights}
            disabled={generating}
            className="btn-premium-bw flex items-center gap-2"
          >
            {generating ? (
              <>
                <Loader2 className="animate-spin" size={16} />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={16} />
                Generate Insights
              </>
            )}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="insights-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="badge-bw badge-outline mb-4 inline-block">
            <Brain size={12} /> AI Insights
          </span>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            Agentic Intelligence
          </h1>
          <p className="text-white/40 mt-2">
            Generated: {insights.generated_at ? new Date(insights.generated_at).toLocaleString() : "N/A"}
          </p>
        </div>
        <button 
          onClick={generateInsights}
          disabled={generating}
          className="btn-outline-bw flex items-center gap-2"
        >
          {generating ? <Loader2 className="animate-spin" size={14} /> : <Sparkles size={14} />}
          Regenerate
        </button>
      </div>

      {/* Key Findings */}
      {insights.key_findings && insights.key_findings.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <Target size={20} className="text-white/60" />
            </div>
            <h2 className="text-xl md:text-2xl font-bold">Key Findings</h2>
          </div>
          <div className="space-y-3">
            {insights.key_findings.map((finding, i) => (
              <div key={i} className="flex items-start gap-3 p-4 rounded-xl bg-white/[0.02] border border-white/5">
                <ChevronRight size={20} className="text-white/40 mt-0.5 shrink-0" />
                <p className="text-white/70 text-sm leading-relaxed">{finding}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Alerts & Opportunities */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        {/* Risk Alerts */}
        {insights.risk_alerts && insights.risk_alerts.length > 0 && (
          <div className="spotlight-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle size={18} className="text-red-400" />
              <h3 className="text-lg font-semibold">Risk Alerts</h3>
            </div>
            <div className="space-y-2">
              {insights.risk_alerts.map((alert, i) => (
                <div key={i} className="p-3 rounded-lg bg-red-500/5 border border-red-500/10">
                  <p className="text-sm text-red-300">{alert}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Opportunities */}
        {insights.opportunities && insights.opportunities.length > 0 && (
          <div className="spotlight-card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Zap size={18} className="text-green-400" />
              <h3 className="text-lg font-semibold">Opportunities</h3>
            </div>
            <div className="space-y-2">
              {insights.opportunities.map((opp, i) => (
                <div key={i} className="p-3 rounded-lg bg-green-500/5 border border-green-500/10">
                  <p className="text-sm text-green-300">{opp}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Impact Scenarios */}
      {insights.impact_scenarios && insights.impact_scenarios.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <BarChart3 size={20} className="text-white/60" />
            </div>
            <h2 className="text-xl md:text-2xl font-bold">Impact Scenarios</h2>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {insights.impact_scenarios.map((scenario, i) => (
              <div key={i} className="p-5 rounded-xl bg-white/[0.02] border border-white/5 space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <h3 className="text-lg font-semibold text-white">{scenario.scenario_name}</h3>
                  <span className={`badge-bw text-xs ${
                    scenario.impact_level === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                    scenario.impact_level === 'high' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                    scenario.impact_level === 'medium' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                    'bg-blue-500/10 text-blue-400 border-blue-500/20'
                  }`}>
                    {scenario.impact_level}
                  </span>
                </div>
                <p className="text-sm text-white/60 leading-relaxed">{scenario.description}</p>
                
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <Activity size={14} className="text-white/40" />
                    <span className="text-white/50">Probability: {Math.round(scenario.probability * 100)}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield size={14} className="text-white/40" />
                    <span className="text-white/50">Confidence: {Math.round(scenario.confidence_score * 100)}%</span>
                  </div>
                </div>

                {scenario.assumptions && scenario.assumptions.length > 0 && (
                  <div className="pt-3 border-t border-white/5">
                    <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Assumptions</p>
                    <ul className="space-y-1">
                      {scenario.assumptions.slice(0, 2).map((assumption, j) => (
                        <li key={j} className="text-xs text-white/50 flex items-start gap-2">
                          <span className="text-white/30">•</span>
                          <span>{assumption}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dashboard Recommendations */}
      {insights.dashboard_recommendations && insights.dashboard_recommendations.length > 0 && (
        <div className="spotlight-card p-6 md:p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center">
              <Activity size={20} className="text-white/60" />
            </div>
            <h2 className="text-xl md:text-2xl font-bold">Dashboard Recommendations</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {insights.dashboard_recommendations.map((widget, i) => (
              <div key={i} className="p-5 rounded-xl bg-white/[0.02] border border-white/5">
                <div className="flex items-start justify-between mb-3">
                  <span className={`badge-bw text-xs ${
                    widget.priority === 'P0' ? 'bg-red-500/10 text-red-400' :
                    widget.priority === 'P1' ? 'bg-orange-500/10 text-orange-400' :
                    'bg-blue-500/10 text-blue-400'
                  }`}>
                    {widget.priority}
                  </span>
                  <span className="text-xs text-white/30 uppercase">{widget.widget_type}</span>
                </div>
                <h4 className="font-semibold text-white mb-2">{widget.title}</h4>
                <p className="text-xs text-white/50 leading-relaxed">{widget.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Info */}
      <div className="flex items-center justify-center gap-6 text-xs text-white/30 py-4">
        <span>Processing time: {insights.processing_time_seconds?.toFixed(1)}s</span>
        <span>•</span>
        <span>Powered by GPT-5.2</span>
      </div>
    </div>
  );
};

// ========================
// ACTION ITEMS PAGE
// ========================
export const ActionItemsPage = () => {
  const [actionItems, setActionItems] = useState([]);
  const [team, setTeam] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all"); // all, pending, in_progress, completed

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [itemsRes, teamRes] = await Promise.all([
        axios.get(`${API}/action-items`),
        axios.get(`${API}/team`)
      ]);
      setActionItems(itemsRes.data.action_items || []);
      setTeam(teamRes.data.team_members || []);
    } catch (e) {
      console.error("Failed to fetch action items:", e);
      toast.error("Failed to load action items");
    } finally {
      setLoading(false);
    }
  };

  const updateStatus = async (itemId, newStatus) => {
    try {
      await axios.post(`${API}/action-items/${itemId}/complete`, {
        status: newStatus
      });
      setActionItems(actionItems.map(item => 
        item.id === itemId ? { ...item, status: newStatus } : item
      ));
      toast.success("Task status updated");
    } catch (e) {
      toast.error("Failed to update status");
    }
  };

  const getTeamMember = (memberId) => {
    return team.find(m => m.id === memberId);
  };

  const filteredItems = filter === "all" 
    ? actionItems 
    : actionItems.filter(item => item.status === filter);

  const priorityOrder = { P0: 0, P1: 1, P2: 2 };
  const sortedItems = [...filteredItems].sort((a, b) => 
    priorityOrder[a.priority] - priorityOrder[b.priority]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  const stats = {
    total: actionItems.length,
    pending: actionItems.filter(i => i.status === 'pending').length,
    in_progress: actionItems.filter(i => i.status === 'in_progress').length,
    completed: actionItems.filter(i => i.status === 'completed').length
  };

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="action-items-page">
      {/* Header */}
      <div>
        <span className="badge-bw badge-outline mb-4 inline-block">
          <CheckCircle2 size={12} /> Task Management
        </span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Action Items
        </h1>
        <p className="text-white/40 mt-2">
          AI-assigned tasks for your team
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4">
        {[
          { label: "Total Tasks", value: stats.total, color: "blue" },
          { label: "Pending", value: stats.pending, color: "yellow" },
          { label: "In Progress", value: stats.in_progress, color: "orange" },
          { label: "Completed", value: stats.completed, color: "green" },
        ].map((stat, i) => (
          <div key={i} className="spotlight-card p-4 md:p-6">
            <p className="stat-number text-3xl md:text-4xl">{stat.value}</p>
            <p className="text-xs text-white/40 uppercase tracking-wider mt-2">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {[
          { label: "All", value: "all" },
          { label: "Pending", value: "pending" },
          { label: "In Progress", value: "in_progress" },
          { label: "Completed", value: "completed" }
        ].map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-4 py-2 rounded-lg text-xs font-medium uppercase tracking-wider transition-all ${
              filter === f.value
                ? 'bg-white text-black'
                : 'bg-white/5 text-white/50 hover:bg-white/10'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Action Items */}
      {sortedItems.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <CheckCircle2 className="mb-4 text-white/20" size={48} />
          <p className="text-white/40">No action items found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedItems.map((item) => {
            const assignee = getTeamMember(item.assigned_to);
            return (
              <div key={item.id} className="spotlight-card p-5 md:p-6">
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <span className={`badge-bw text-xs ${
                        item.priority === 'P0' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                        item.priority === 'P1' ? 'bg-orange-500/10 text-orange-400 border-orange-500/20' :
                        'bg-blue-500/10 text-blue-400 border-blue-500/20'
                      }`}>
                        {item.priority}
                      </span>
                      <span className={`badge-bw text-xs ${
                        item.status === 'completed' ? 'badge-success-bw' :
                        item.status === 'in_progress' ? 'bg-orange-500/10 text-orange-400' :
                        'badge-outline'
                      }`}>
                        {item.status.replace('_', ' ')}
                      </span>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                    <p className="text-sm text-white/60 leading-relaxed mb-4">{item.description}</p>
                    
                    {item.reasoning && (
                      <div className="p-3 rounded-lg bg-white/[0.02] border border-white/5 mb-4">
                        <p className="text-xs text-white/40 uppercase tracking-wider mb-1">Reasoning</p>
                        <p className="text-sm text-white/50">{item.reasoning}</p>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-xs text-white/40">
                      {assignee && (
                        <div className="flex items-center gap-2">
                          <User size={14} />
                          <span>{assignee.name} ({assignee.title})</span>
                        </div>
                      )}
                      {item.due_date && (
                        <div className="flex items-center gap-2">
                          <Calendar size={14} />
                          <span>Due: {new Date(item.due_date).toLocaleDateString()}</span>
                        </div>
                      )}
                      {item.assigned_role && (
                        <div className="flex items-center gap-2">
                          <Flag size={14} />
                          <span className="capitalize">{item.assigned_role}</span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex md:flex-col gap-2">
                    {item.status === 'pending' && (
                      <button
                        onClick={() => updateStatus(item.id, 'in_progress')}
                        className="btn-outline-bw text-xs px-4 py-2 flex items-center gap-2 whitespace-nowrap"
                      >
                        <Activity size={14} />
                        Start
                      </button>
                    )}
                    {item.status === 'in_progress' && (
                      <button
                        onClick={() => updateStatus(item.id, 'completed')}
                        className="btn-premium-bw text-xs px-4 py-2 flex items-center gap-2 whitespace-nowrap"
                      >
                        <CheckCircle2 size={14} />
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ========================
// APPROVALS PAGE
// ========================
export const ApprovalsPage = () => {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);

  useEffect(() => {
    fetchApprovals();
  }, []);

  const fetchApprovals = async () => {
    try {
      const response = await axios.get(`${API}/approvals?status=pending`);
      setApprovals(response.data.approvals || []);
    } catch (e) {
      console.error("Failed to fetch approvals:", e);
      toast.error("Failed to load approvals");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId) => {
    try {
      setProcessing(approvalId);
      await axios.post(`${API}/approvals/${approvalId}/approve`);
      toast.success("Action approved and executed");
      setApprovals(approvals.filter(a => a.id !== approvalId));
    } catch (e) {
      toast.error("Failed to approve action", {
        description: e.response?.data?.detail || "Unknown error"
      });
    } finally {
      setProcessing(null);
    }
  };

  const handleReject = async (approvalId) => {
    try {
      setProcessing(approvalId);
      await axios.post(`${API}/approvals/${approvalId}/reject`);
      toast.success("Action rejected");
      setApprovals(approvals.filter(a => a.id !== approvalId));
    } catch (e) {
      toast.error("Failed to reject action");
    } finally {
      setProcessing(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="approvals-page">
      {/* Header */}
      <div>
        <span className="badge-bw badge-outline mb-4 inline-block">
          <Shield size={12} /> Approval Workflow
        </span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Pending Approvals
        </h1>
        <p className="text-white/40 mt-2">
          Review and execute AI-recommended actions
        </p>
      </div>

      {/* Approvals */}
      {approvals.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center spotlight-card p-12">
          <CheckCircle2 className="mb-4 text-green-400" size={64} />
          <h2 className="text-2xl font-bold mb-2">All Clear!</h2>
          <p className="text-white/40">No pending approvals at this time</p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((approval) => (
            <div key={approval.id} className="spotlight-card p-6 md:p-8">
              <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-4">
                    <span className="badge-bw badge-white text-xs">
                      {approval.action_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-white/30">
                      Confidence: {Math.round(approval.confidence * 100)}%
                    </span>
                  </div>

                  <h3 className="text-xl font-semibold text-white mb-3">{approval.title}</h3>
                  <p className="text-sm text-white/60 leading-relaxed mb-4">{approval.description}</p>

                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 mb-4">
                    <p className="text-xs text-white/40 uppercase tracking-wider mb-2">AI Reasoning</p>
                    <p className="text-sm text-white/50">{approval.reasoning}</p>
                  </div>

                  {approval.parameters && Object.keys(approval.parameters).length > 0 && (
                    <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                      <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Parameters</p>
                      <pre className="text-xs text-white/50 overflow-x-auto">
                        {JSON.stringify(approval.parameters, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>

                <div className="flex lg:flex-col gap-3">
                  <button
                    onClick={() => handleApprove(approval.id)}
                    disabled={processing === approval.id}
                    className="btn-premium-bw flex items-center gap-2 whitespace-nowrap"
                  >
                    {processing === approval.id ? (
                      <>
                        <Loader2 className="animate-spin" size={16} />
                        Processing...
                      </>
                    ) : (
                      <>
                        <ThumbsUp size={16} />
                        Approve & Execute
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleReject(approval.id)}
                    disabled={processing === approval.id}
                    className="btn-outline-bw flex items-center gap-2 whitespace-nowrap text-red-400 border-red-500/20 hover:bg-red-500/10"
                  >
                    <ThumbsDown size={16} />
                    Reject
                  </button>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-white/5 text-xs text-white/30">
                Created: {new Date(approval.created_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ========================
// TRENDS PAGE
// ========================
export const TrendsPage = () => {
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrends();
  }, []);

  const fetchTrends = async () => {
    try {
      const response = await axios.get(`${API}/trends`);
      setTrends(response.data.trends || []);
    } catch (e) {
      console.error("Failed to fetch trends:", e);
      toast.error("Failed to load trends");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="animate-spin text-white" size={32} />
      </div>
    );
  }

  const categoryColors = {
    partnerships: 'blue',
    funding: 'green',
    pricing: 'yellow',
    technology: 'purple',
    destinations: 'pink'
  };

  return (
    <div className="space-y-6 md:space-y-8 noise-bg w-full" data-testid="trends-page">
      {/* Header */}
      <div>
        <span className="badge-bw badge-outline mb-4 inline-block">
          <TrendingUp size={12} /> Predictive Analytics
        </span>
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          Trend Forecasts
        </h1>
        <p className="text-white/40 mt-2">
          AI-predicted tourism industry trends
        </p>
      </div>

      {/* Trends */}
      {trends.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <TrendingUp className="mb-4 text-white/20" size={48} />
          <p className="text-white/40">No trend forecasts available yet</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
          {trends.map((trend) => (
            <div key={trend.id} className="spotlight-card p-6 md:p-8">
              <div className="flex items-start justify-between gap-3 mb-4">
                <span className={`badge-bw text-xs capitalize ${
                  trend.trend_category === 'partnerships' ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' :
                  trend.trend_category === 'funding' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                  trend.trend_category === 'pricing' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                  trend.trend_category === 'technology' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20' :
                  'bg-pink-500/10 text-pink-400 border-pink-500/20'
                }`}>
                  {trend.trend_category}
                </span>
                <span className="text-xs text-white/30 uppercase">{trend.forecast_horizon.replace('_', ' ')}</span>
              </div>

              <h3 className="text-xl font-semibold text-white mb-3">{trend.trend_name}</h3>
              <p className="text-sm text-white/60 leading-relaxed mb-4">{trend.description}</p>

              <div className="flex items-center gap-2 mb-4">
                <div className="flex-1 h-2 bg-white/5 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    style={{ width: `${trend.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-white/50 font-mono">{Math.round(trend.confidence * 100)}%</span>
              </div>

              {trend.potential_impact && (
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 mb-4">
                  <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Potential Impact</p>
                  <p className="text-sm text-white/50">{trend.potential_impact}</p>
                </div>
              )}

              {trend.key_indicators && trend.key_indicators.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Key Indicators</p>
                  <div className="flex flex-wrap gap-2">
                    {trend.key_indicators.map((indicator, i) => (
                      <span key={i} className="badge-bw badge-outline text-xs">
                        {indicator}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {trend.recommended_actions && trend.recommended_actions.length > 0 && (
                <div>
                  <p className="text-xs text-white/40 uppercase tracking-wider mb-2">Recommended Actions</p>
                  <ul className="space-y-2">
                    {trend.recommended_actions.map((action, i) => (
                      <li key={i} className="text-sm text-white/50 flex items-start gap-2">
                        <ArrowRight size={16} className="text-white/30 mt-0.5 shrink-0" />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
