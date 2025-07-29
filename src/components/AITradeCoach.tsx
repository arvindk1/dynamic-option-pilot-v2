import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Brain, 
  TrendingUp, 
  Target, 
  Lightbulb, 
  Award, 
  BarChart3, 
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  BookOpen,
  Zap,
  Settings
} from 'lucide-react';

interface TradeGrade {
  id: number;
  trade_id: number;
  overall_grade: string;
  overall_score: number;
  component_scores: {
    entry_timing: number;
    exit_timing: number;
    risk_management: number;
    strategy_selection: number;
    market_conditions: number;
  };
  strengths: string[];
  weaknesses: string[];
  ai_feedback: string;
  improvement_suggestions: string[];
  confidence_level: number;
  analysis_date: string;
  trade_symbol?: string;
  trade_pnl?: number;
}

interface PerformancePattern {
  id: number;
  pattern_name: string;
  pattern_type: string;
  description: string;
  frequency: number;
  confidence: number;
  avg_pnl: number;
  win_rate: number;
  avg_duration: number;
  recommendations: string[];
}

interface TradingInsight {
  id: number;
  insight_type: string;
  title: string;
  description: string;
  priority: string;
  actionable_steps: string[];
  expected_impact: string;
  relevance_score: number;
  created_at: string;
}

interface PortfolioOptimization {
  id: number;
  current_metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    avg_return: number;
  };
  projected_metrics: {
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    avg_return: number;
  };
  suggestions: {
    position_sizing: Record<string, unknown>;
    strategy_allocation: Record<string, unknown>;
    risk_adjustments: Record<string, unknown>;
  };
  implementation: {
    steps: string[];
    timeline: string;
    risk_level: string;
  };
  confidence_score: number;
}

interface DashboardSummary {
  total_trades_graded: number;
  average_score: number;
  grade_distribution: Record<string, number>;
  active_insights: number;
  patterns_identified: number;
  last_analysis: string;
}

const AITradeCoach: React.FC = React.memo(() => {
  const [dashboardData, setDashboardData] = useState<{
    summary: DashboardSummary;
    recent_grades: TradeGrade[];
    active_insights: TradingInsight[];
    performance_patterns: PerformancePattern[];
    portfolio_optimization: PortfolioOptimization | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/ai-coach/dashboard');
      if (!response.ok) throw new Error('Failed to fetch AI coach dashboard');
      
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const analyzePatterns = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ai-coach/analyze-patterns', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to analyze patterns');
      
      await fetchDashboardData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pattern analysis failed');
    }
  };

  const generateInsights = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ai-coach/generate-insights', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to generate insights');
      
      await fetchDashboardData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Insight generation failed');
    }
  };

  const optimizePortfolio = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/ai-coach/optimize-portfolio', { method: 'POST' });
      if (!response.ok) throw new Error('Failed to optimize portfolio');
      
      await fetchDashboardData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Portfolio optimization failed');
    }
  };

  const dismissInsight = async (insightId: number) => {
    try {
      const response = await fetch(`/api/ai-coach/insights/${insightId}/dismiss`, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to dismiss insight');
      
      await fetchDashboardData(); // Refresh data
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to dismiss insight');
    }
  };

  useEffect(() => {
    fetchDashboardData();
    
    // Auto-refresh every 10 minutes (reduced from 5 minutes to minimize API calls)
    const interval = setInterval(fetchDashboardData, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getGradeColor = (grade: string) => {
    const colors: Record<string, string> = {
      'A+': 'text-green-600 bg-green-50',
      'A': 'text-green-600 bg-green-50',
      'A-': 'text-green-600 bg-green-50',
      'B+': 'text-blue-600 bg-blue-50',
      'B': 'text-blue-600 bg-blue-50',
      'B-': 'text-blue-600 bg-blue-50',
      'C+': 'text-yellow-600 bg-yellow-50',
      'C': 'text-yellow-600 bg-yellow-50',
      'C-': 'text-yellow-600 bg-yellow-50',
      'D+': 'text-orange-600 bg-orange-50',
      'D': 'text-orange-600 bg-orange-50',
      'F': 'text-red-600 bg-red-50'
    };
    return colors[grade] || 'text-gray-600 bg-gray-50';
  };

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      'high': 'bg-red-100 text-red-800',
      'medium': 'bg-yellow-100 text-yellow-800',
      'low': 'bg-green-100 text-green-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-800';
  };

  const getPatternTypeIcon = (type: string) => {
    switch (type) {
      case 'strength': return '💪';
      case 'weakness': return '⚠️';
      default: return '📊';
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading AI Trade Coach...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            AI Trade Grading Coach
          </h2>
          <p className="text-muted-foreground">
            Machine learning-powered trade analysis and personalized coaching
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={analyzePatterns} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Analyze Patterns
          </Button>
          <Button 
            onClick={generateInsights} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <Lightbulb className="h-4 w-4 mr-2" />
            Generate Insights
          </Button>
          <Button 
            onClick={fetchDashboardData} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {dashboardData && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="grades">Trade Grades</TabsTrigger>
            <TabsTrigger value="patterns">Patterns</TabsTrigger>
            <TabsTrigger value="insights">Insights</TabsTrigger>
            <TabsTrigger value="optimization">Optimization</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Trades Graded</p>
                      <p className="text-2xl font-bold">{dashboardData.summary.total_trades_graded}</p>
                    </div>
                    <Award className="h-8 w-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Average Score</p>
                      <p className="text-2xl font-bold">{dashboardData.summary.average_score.toFixed(1)}</p>
                    </div>
                    <Target className="h-8 w-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Active Insights</p>
                      <p className="text-2xl font-bold">{dashboardData.summary.active_insights}</p>
                    </div>
                    <Lightbulb className="h-8 w-8 text-yellow-600" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">Patterns Found</p>
                      <p className="text-2xl font-bold">{dashboardData.summary.patterns_identified}</p>
                    </div>
                    <BarChart3 className="h-8 w-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Grades */}
            <Card>
              <CardHeader>
                <CardTitle>Recent Trade Grades</CardTitle>
                <CardDescription>Latest AI-graded trades with performance scores</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.recent_grades.slice(0, 5).map((grade) => (
                    <div key={grade.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Badge className={getGradeColor(grade.overall_grade)}>
                          {grade.overall_grade}
                        </Badge>
                        <div>
                          <p className="font-semibold">{grade.trade_symbol} Trade #{grade.trade_id}</p>
                          <p className="text-sm text-muted-foreground">
                            Score: {grade.overall_score.toFixed(1)}/100 • 
                            P&L: {grade.trade_pnl ? `$${grade.trade_pnl.toFixed(2)}` : 'Open'}
                          </p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Progress value={grade.overall_score} className="w-20 mb-1" />
                        <p className="text-xs text-muted-foreground">
                          {new Date(grade.analysis_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Active Insights Preview */}
            <Card>
              <CardHeader>
                <CardTitle>Key Insights</CardTitle>
                <CardDescription>Personalized recommendations for improvement</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboardData.active_insights.slice(0, 3).map((insight) => (
                    <div key={insight.id} className="flex items-start justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge className={getPriorityColor(insight.priority)}>
                            {insight.priority}
                          </Badge>
                          <h4 className="font-semibold">{insight.title}</h4>
                        </div>
                        <p className="text-sm text-muted-foreground">{insight.description}</p>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => dismissInsight(insight.id)}
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="grades" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Trade Grade Analysis</CardTitle>
                <CardDescription>Detailed breakdown of trade performance scores</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {dashboardData.recent_grades.map((grade) => (
                    <div key={grade.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-3">
                          <Badge className={getGradeColor(grade.overall_grade)} variant="outline">
                            {grade.overall_grade}
                          </Badge>
                          <h3 className="font-semibold">{grade.trade_symbol} Trade #{grade.trade_id}</h3>
                        </div>
                        <div className="text-right">
                          <p className="text-lg font-bold">{grade.overall_score.toFixed(1)}/100</p>
                          <p className="text-sm text-muted-foreground">Overall Score</p>
                        </div>
                      </div>

                      {/* Component Scores */}
                      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-4">
                        {Object.entries(grade.component_scores).map(([component, score]) => (
                          <div key={component} className="text-center">
                            <p className="text-sm font-medium capitalize">{component.replace('_', ' ')}</p>
                            <Progress value={score} className="mt-1 mb-1" />
                            <p className="text-xs text-muted-foreground">{score.toFixed(0)}/100</p>
                          </div>
                        ))}
                      </div>

                      {/* AI Feedback */}
                      <div className="bg-muted p-3 rounded-lg">
                        <h4 className="font-semibold mb-2">AI Analysis</h4>
                        <p className="text-sm whitespace-pre-line">{grade.ai_feedback}</p>
                      </div>

                      {/* Strengths and Weaknesses */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        {grade.strengths.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-green-600 mb-2">Strengths</h4>
                            <ul className="space-y-1">
                              {grade.strengths.map((strength, idx) => (
                                <li key={idx} className="text-sm flex items-start gap-2">
                                  <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                                  {strength}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {grade.weaknesses.length > 0 && (
                          <div>
                            <h4 className="font-semibold text-orange-600 mb-2">Areas for Improvement</h4>
                            <ul className="space-y-1">
                              {grade.weaknesses.map((weakness, idx) => (
                                <li key={idx} className="text-sm flex items-start gap-2">
                                  <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                                  {weakness}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      {/* Improvement Suggestions */}
                      {grade.improvement_suggestions.length > 0 && (
                        <div className="mt-4">
                          <h4 className="font-semibold mb-2">Improvement Suggestions</h4>
                          <ul className="space-y-1">
                            {grade.improvement_suggestions.map((suggestion, idx) => (
                              <li key={idx} className="text-sm flex items-start gap-2">
                                <BookOpen className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                                {suggestion}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="patterns" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Patterns</CardTitle>
                <CardDescription>AI-identified patterns in your trading behavior</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {dashboardData.performance_patterns.map((pattern) => (
                    <div key={pattern.id} className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-lg">{getPatternTypeIcon(pattern.pattern_type)}</span>
                        <h3 className="font-semibold">{pattern.pattern_name}</h3>
                        <Badge variant="outline">{pattern.pattern_type}</Badge>
                      </div>
                      
                      <p className="text-sm text-muted-foreground mb-3">{pattern.description}</p>
                      
                      <div className="grid grid-cols-3 gap-2 text-center mb-3">
                        <div>
                          <p className="text-lg font-bold">{pattern.frequency}</p>
                          <p className="text-xs text-muted-foreground">Frequency</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold">{(pattern.win_rate * 100).toFixed(0)}%</p>
                          <p className="text-xs text-muted-foreground">Win Rate</p>
                        </div>
                        <div>
                          <p className="text-lg font-bold">${pattern.avg_pnl.toFixed(0)}</p>
                          <p className="text-xs text-muted-foreground">Avg P&L</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3">
                        <Progress value={pattern.confidence * 100} className="flex-1" />
                        <span className="text-sm text-muted-foreground">
                          {(pattern.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>

                      {pattern.recommendations.length > 0 && (
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Recommendations</h4>
                          <ul className="space-y-1">
                            {pattern.recommendations.slice(0, 2).map((rec, idx) => (
                              <li key={idx} className="text-xs flex items-start gap-2">
                                <Zap className="h-3 w-3 text-yellow-600 mt-0.5 flex-shrink-0" />
                                {rec}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="insights" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Trading Insights</CardTitle>
                <CardDescription>Personalized recommendations and action items</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dashboardData.active_insights.map((insight) => (
                    <div key={insight.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge className={getPriorityColor(insight.priority)}>
                            {insight.priority}
                          </Badge>
                          <Badge variant="outline">{insight.insight_type}</Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => dismissInsight(insight.id)}
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      </div>
                      
                      <h3 className="font-semibold mb-2">{insight.title}</h3>
                      <p className="text-sm text-muted-foreground mb-3">{insight.description}</p>
                      
                      {insight.actionable_steps.length > 0 && (
                        <div className="mb-3">
                          <h4 className="font-semibold text-sm mb-2">Action Steps</h4>
                          <ol className="space-y-1">
                            {insight.actionable_steps.map((step, idx) => (
                              <li key={idx} className="text-sm flex items-start gap-2">
                                <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                                  {idx + 1}
                                </span>
                                {step}
                              </li>
                            ))}
                          </ol>
                        </div>
                      )}
                      
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Expected Impact: {insight.expected_impact}</span>
                        <span className="text-muted-foreground">
                          Relevance: {(insight.relevance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="optimization" className="space-y-4">
            {dashboardData.portfolio_optimization ? (
              <Card>
                <CardHeader>
                  <CardTitle>Portfolio Optimization</CardTitle>
                  <CardDescription>AI-recommended improvements to your trading approach</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* Current vs Projected Metrics */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <h3 className="font-semibold mb-3">Current Performance</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Sharpe Ratio:</span>
                            <span className="font-mono">{dashboardData.portfolio_optimization.current_metrics.sharpe_ratio.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Max Drawdown:</span>
                            <span className="font-mono">{(dashboardData.portfolio_optimization.current_metrics.max_drawdown * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Win Rate:</span>
                            <span className="font-mono">{(dashboardData.portfolio_optimization.current_metrics.win_rate * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Avg Return:</span>
                            <span className="font-mono">{(dashboardData.portfolio_optimization.current_metrics.avg_return * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="font-semibold mb-3">Projected Performance</h3>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Sharpe Ratio:</span>
                            <span className="font-mono text-green-600">{dashboardData.portfolio_optimization.projected_metrics.sharpe_ratio.toFixed(2)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Max Drawdown:</span>
                            <span className="font-mono text-green-600">{(dashboardData.portfolio_optimization.projected_metrics.max_drawdown * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Win Rate:</span>
                            <span className="font-mono text-green-600">{(dashboardData.portfolio_optimization.projected_metrics.win_rate * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Avg Return:</span>
                            <span className="font-mono text-green-600">{(dashboardData.portfolio_optimization.projected_metrics.avg_return * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Implementation Plan */}
                    <div>
                      <h3 className="font-semibold mb-3">Implementation Plan</h3>
                      <div className="bg-muted p-4 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline">{dashboardData.portfolio_optimization.implementation.risk_level}</Badge>
                          <span className="text-sm text-muted-foreground">
                            Timeline: {dashboardData.portfolio_optimization.implementation.timeline}
                          </span>
                        </div>
                        <ol className="space-y-2">
                          {dashboardData.portfolio_optimization.implementation.steps.map((step, idx) => (
                            <li key={idx} className="text-sm flex items-start gap-2">
                              <span className="bg-blue-100 text-blue-600 rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                                {idx + 1}
                              </span>
                              {step}
                            </li>
                          ))}
                        </ol>
                      </div>
                    </div>

                    {/* Confidence Score */}
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">Confidence Level:</span>
                      <Progress value={dashboardData.portfolio_optimization.confidence_score * 100} className="flex-1" />
                      <span className="text-sm text-muted-foreground">
                        {(dashboardData.portfolio_optimization.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-64">
                  <Settings className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground text-center mb-4">
                    No portfolio optimization available yet
                  </p>
                  <Button onClick={optimizePortfolio} disabled={loading}>
                    <Zap className="h-4 w-4 mr-2" />
                    Run Portfolio Optimization
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
});

export default AITradeCoach;