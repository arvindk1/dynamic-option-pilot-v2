import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface StrategyMetadata {
  id: string;
  name: string;
  type: string;
  description: string;
  category: string;
  status: 'active' | 'inactive' | 'error';
  config: Record<string, any>;
  last_updated: string;
  performance_stats?: Record<string, any>;
}

export interface OpportunityData {
  strategy_id: string;
  strategy_name: string;
  opportunities: any[];
  count: number;
  generated_at: string;
  market_conditions: Record<string, any>;
}

interface ScanJob {
  jobId: string;
  strategyId: string;
  strategyName: string;
  status: 'running' | 'completed' | 'error' | 'cancelled';
  startedAt: string;
}

interface StrategyContextType {
  // Strategy metadata
  strategies: StrategyMetadata[];
  categories: string[];
  loading: boolean;
  error: string | null;
  
  // Strategy opportunities
  opportunitiesByStrategy: Record<string, OpportunityData>;
  loadingOpportunities: Record<string, boolean>;
  
  // Scan job tracking
  activeScanJobs: ScanJob[];
  
  // Actions
  refreshStrategies: () => Promise<void>;
  refreshAllOpportunities: (useAsyncJobs?: boolean) => Promise<void>;
  refreshStrategyWithProgress: (strategyId: string) => Promise<string>; // Returns jobId
  getStrategyOpportunities: (strategyId: string, symbol?: string) => Promise<void>;
  getStrategiesByCategory: (category: string) => StrategyMetadata[];
  getAllOpportunities: () => any[];
  getOpportunitiesByCategory: (category: string) => any[];
}

const StrategyContext = createContext<StrategyContextType | undefined>(undefined);

export const useStrategies = () => {
  const context = useContext(StrategyContext);
  if (context === undefined) {
    throw new Error('useStrategies must be used within a StrategyProvider');
  }
  return context;
};

interface StrategyProviderProps {
  children: ReactNode;
}

// Enhanced strategy categorization for professional trading interface
const getCategoryFromStrategyType = (strategyId: string): string => {
  // Professional trader-focused categories with clear risk/return profiles
  const categoryMap: Record<string, string> = {
    // Income Generation (Low-Medium Risk)
    'ThetaCropWeekly': 'income_generation',
    'CoveredCall': 'income_generation',
    'CreditSpread': 'income_generation',
    
    // Volatility Trading (Medium-High Risk)
    'IronCondor': 'volatility_trading',
    'Straddle': 'volatility_trading',
    'Strangle': 'volatility_trading',
    'ButterflySpread': 'volatility_trading',
    
    // Directional Strategies (Medium Risk)
    'VerticalSpread': 'directional_strategies',
    'SingleOption': 'directional_strategies',
    
    // Risk Management (Low Risk)
    'ProtectivePut': 'risk_management',
    'Collar': 'risk_management',
    
    // Advanced Strategies (Medium-High Risk)
    'CalendarSpread': 'advanced_strategies',
    'RSICouponStrategy': 'advanced_strategies'
  };
  return categoryMap[strategyId] || 'other_strategies';
};

// Helper function to transform opportunity data for TradeCard compatibility
const transformOpportunityForTradeCard = (opp: any) => ({
  ...opp,
  // Add missing fields that TradeCard expects
  expiration: new Date(Date.now() + (opp.days_to_expiration * 24 * 60 * 60 * 1000)).toISOString().split('T')[0],
  max_profit: Math.max(opp.premium * 100, opp.expected_value * 2), // Estimate max profit
  trade_setup: `${opp.strategy_type} on ${opp.symbol}`,
  risk_level: opp.probability_profit > 0.75 ? 'LOW' : opp.probability_profit > 0.5 ? 'MEDIUM' : 'HIGH'
});

export const StrategyProvider: React.FC<StrategyProviderProps> = ({ children }) => {
  const [strategies, setStrategies] = useState<StrategyMetadata[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opportunitiesByStrategy, setOpportunitiesByStrategy] = useState<Record<string, OpportunityData>>({});
  const [loadingOpportunities, setLoadingOpportunities] = useState<Record<string, boolean>>({});
  const [activeScanJobs, setActiveScanJobs] = useState<ScanJob[]>([]);
  
  // Request deduplication with caching
  const [pendingRequests] = useState(new Map<string, Promise<any>>());
  
  // Deduplicate concurrent API requests
  const makeDeduplicatedRequest = async <T,>(key: string, requestFn: () => Promise<T>): Promise<T> => {
    if (pendingRequests.has(key)) {
      return pendingRequests.get(key) as Promise<T>;
    }
    
    const promise = requestFn().finally(() => {
      pendingRequests.delete(key);
    });
    
    pendingRequests.set(key, promise);
    return promise;
  };

  // Refresh opportunities using quick-scan endpoints for all strategies
  const refreshAllOpportunities = async () => {
    try {
      // Set loading state for all strategies
      const loadingState: Record<string, boolean> = {};
      strategies.forEach(strategy => {
        loadingState[strategy.id] = true;
      });
      setLoadingOpportunities(loadingState);

      // Initialize opportunities data structure
      const opportunitiesByStrategy: Record<string, OpportunityData> = {};
      strategies.forEach(strategy => {
        opportunitiesByStrategy[strategy.id] = {
          strategy_id: strategy.id,
          strategy_name: strategy.name,
          opportunities: [],
          count: 0,
          generated_at: new Date().toISOString(),
          market_conditions: {}
        };
      });

      // Trigger quick-scan for active strategies concurrently
      const activeStrategies = strategies.filter(s => s.status === 'active');
      const scanPromises = activeStrategies.map(async (strategy) => {
        try {
          // Try to fetch existing opportunities first (faster)
          const oppResponse = await fetch(`/api/strategies/${strategy.id}/opportunities`);
          if (oppResponse.ok) {
            const oppData = await oppResponse.json();
            // Transform opportunities to match TradeCard interface
            const transformedOpportunities = (oppData.opportunities || []).map(transformOpportunityForTradeCard);
            
            opportunitiesByStrategy[strategy.id] = {
              strategy_id: strategy.id,
              strategy_name: strategy.name,
              opportunities: transformedOpportunities,
              count: oppData.count || 0,
              generated_at: oppData.generated_at || new Date().toISOString(),
              market_conditions: oppData.market_conditions || {}
            };
            console.log(`${strategy.name}: ${oppData.count || 0} opportunities loaded`);
          } else {
            // If no cached opportunities, trigger a quick scan
            console.log(`Triggering scan for ${strategy.name}...`);
            const scanResponse = await fetch(`/api/strategies/${strategy.id}/quick-scan`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' }
            });
            
            if (scanResponse.ok) {
              const scanResult = await scanResponse.json();
              console.log(`${strategy.name}: scan completed with ${scanResult.opportunities_found} opportunities`);
              
              // Fetch opportunities after scan
              const oppResponse2 = await fetch(`/api/strategies/${strategy.id}/opportunities`);
              if (oppResponse2.ok) {
                const oppData2 = await oppResponse2.json();
                // Transform opportunities to match TradeCard interface
                const transformedOpportunities2 = (oppData2.opportunities || []).map(transformOpportunityForTradeCard);
                
                opportunitiesByStrategy[strategy.id] = {
                  strategy_id: strategy.id,
                  strategy_name: strategy.name,
                  opportunities: transformedOpportunities2,
                  count: oppData2.count || 0,
                  generated_at: oppData2.generated_at || new Date().toISOString(),
                  market_conditions: oppData2.market_conditions || {}
                };
              }
            }
          }
        } catch (error) {
          console.error(`Failed to refresh ${strategy.name}:`, error);
        } finally {
          // Clear loading state for this strategy
          setLoadingOpportunities(prev => ({
            ...prev,
            [strategy.id]: false
          }));
        }
      });

      await Promise.all(scanPromises);
      setOpportunitiesByStrategy(opportunitiesByStrategy);
      
    } catch (err) {
      console.error('Error refreshing opportunities:', err);
      // Clear all loading states on error
      setLoadingOpportunities({});
    }
  };

  // New function for async job-based scanning with progress tracking
  const refreshStrategyWithProgress = async (strategyId: string): Promise<string> => {
    try {
      const strategy = strategies.find(s => s.id === strategyId);
      if (!strategy) {
        throw new Error(`Strategy ${strategyId} not found`);
      }

      // Start async scan job
      const response = await fetch(`/api/strategies/${strategyId}/quick-scan?async_job=true`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Failed to start scan job: ${response.statusText}`);
      }

      const jobData = await response.json();
      const jobId = jobData.job_id;

      // Add to active jobs
      const newJob: ScanJob = {
        jobId,
        strategyId,
        strategyName: strategy.name,
        status: 'running',
        startedAt: new Date().toISOString()
      };

      setActiveScanJobs(prev => [...prev.filter(job => job.jobId !== jobId), newJob]);
      
      // Set loading state
      setLoadingOpportunities(prev => ({ ...prev, [strategyId]: true }));

      return jobId;
    } catch (error) {
      console.error(`Error starting scan job for ${strategyId}:`, error);
      throw error;
    }
  };

  // Update existing refreshAllOpportunities to support async mode
  const refreshAllOpportunitiesWithJobs = async (useAsyncJobs: boolean = false) => {
    if (!useAsyncJobs) {
      // Use original synchronous implementation
      return refreshAllOpportunities();
    }

    try {
      // Set loading state for all strategies
      const loadingState: Record<string, boolean> = {};
      strategies.forEach(strategy => {
        loadingState[strategy.id] = true;
      });
      setLoadingOpportunities(loadingState);

      // Start async jobs for all active strategies
      const activeStrategies = strategies.filter(s => s.status === 'active');
      const jobPromises = activeStrategies.map(strategy => refreshStrategyWithProgress(strategy.id));
      
      await Promise.all(jobPromises);
    } catch (error) {
      console.error('Error starting async scan jobs:', error);
      setLoadingOpportunities({});
    }
  };

  // Legacy load function for backward compatibility  
  const loadAllOpportunities = async () => {
    try {
      const response = await fetch('/api/trading/opportunities');
      if (!response.ok) {
        throw new Error(`Failed to fetch opportunities: ${response.statusText}`);
      }
      
      const data = await response.json();
      const allOpportunities = data.opportunities || [];
      
      // Group opportunities by strategy_type and map to strategy IDs
      const opportunitiesByStrategy: Record<string, OpportunityData> = {};
      
      // Initialize all strategies with empty opportunities
      const currentStrategies = strategies.length > 0 ? strategies : [];
      
      currentStrategies.forEach(strategy => {
        opportunitiesByStrategy[strategy.id] = {
          strategy_id: strategy.id,
          strategy_name: strategy.name,
          opportunities: [],
          count: 0,
          generated_at: new Date().toISOString(),
          market_conditions: {}
        };
      });
      
      // Distribute opportunities to strategies based on strategy_type
      allOpportunities.forEach((opp: any) => {
        // CRITICAL FIX: Map backend strategy_type (SCREAMING_SNAKE_CASE) to frontend strategy IDs (PascalCase)
        const strategyMapping: Record<string, string> = {
          // Exact mapping from backend strategy_type to frontend strategy ID
          'PROTECTIVE_PUT': 'ProtectivePut',
          'STRANGLE': 'Strangle', 
          'STRADDLE': 'Straddle',
          'RSI_COUPON': 'RSICouponStrategy',
          'THETA_HARVESTING': 'ThetaCropWeekly',
          'BUTTERFLY': 'Butterfly',
          'NAKED_OPTION': 'SingleOption',
          'COLLAR': 'Collar',
          'COVERED_CALL': 'CoveredCall',
          'VERTICAL_SPREAD': 'VerticalSpread',
          'CALENDAR_SPREAD': 'CalendarSpread',
          'IRON_CONDOR': 'IronCondor',
          'CREDIT_SPREAD': 'CreditSpread',
          
          // Legacy mappings for backward compatibility
          'high_probability': 'RSICouponStrategy',
          'quick_scalp': 'SingleOption', 
          'swing_trade': 'CoveredCall',
          'volatility_play': 'IronCondor',
          'iron_condor': 'IronCondor',
          'put_spread': 'CreditSpread',
          'covered_call': 'CoveredCall',
          'theta_decay': 'ThetaCropWeekly',
          'momentum': 'VerticalSpread',
          'protective': 'ProtectivePut',
          'neutral': 'Butterfly'
        };
        
        let targetStrategyId = strategyMapping[opp.strategy_type] || 
                              strategyMapping[opp.strategy_type?.toLowerCase()] ||
                              opp.strategy_type; // fallback to exact match
        
        // If still no match found, try to find any active strategy
        if (!opportunitiesByStrategy[targetStrategyId]) {
          targetStrategyId = currentStrategies.find(s => s.status === 'active')?.id || 'IronCondor';
          console.warn(`No strategy mapping found for '${opp.strategy_type}', using fallback: ${targetStrategyId}`);
        }
        
        if (opportunitiesByStrategy[targetStrategyId]) {
          opportunitiesByStrategy[targetStrategyId].opportunities.push(opp);
          opportunitiesByStrategy[targetStrategyId].count += 1;
        }
      });
      
      setOpportunitiesByStrategy(opportunitiesByStrategy);
      
    } catch (err) {
      console.error('Error loading all opportunities:', err);
    }
  };

  const refreshStrategies = async () => {
    return makeDeduplicatedRequest('refresh-strategies', async () => {
      try {
        setLoading(true);
        setError(null);
        
        // First get basic strategy metadata
        const strategiesResponse = await fetch('/api/strategies/');
        if (!strategiesResponse.ok) {
          throw new Error(`Failed to fetch strategies: ${strategiesResponse.statusText}`);
        }
        
        const strategiesData = await strategiesResponse.json();
      
      // Enhanced strategy metadata with proper category mapping
      const enhancedStrategies = strategiesData.strategies.map((strategy: any) => ({
        ...strategy,
        // Use backend category if available, otherwise map from strategy ID
        category: strategy.category || getCategoryFromStrategyType(strategy.id),
        status: (strategy.enabled === true) ? 'active' as const : 'inactive' as const,
        last_updated: new Date().toISOString(),
        performance_stats: {},
        config: {
          min_dte: strategy.min_dte,
          max_dte: strategy.max_dte,
          risk_level: strategy.risk_level,
          enabled: strategy.enabled
        }
      }));
      
      // Extract unique categories from strategies  
      const uniqueCategories = [...new Set(enhancedStrategies.map(s => s.category))];
      
      setStrategies(enhancedStrategies);
      setCategories(uniqueCategories);
      
      // Now load all opportunities and distribute them to strategies
      await loadAllOpportunities();
      
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load strategies';
        setError(errorMessage);
        console.error('Error fetching strategies:', err);
      } finally {
        setLoading(false);
      }
    });
  };

  const getStrategyOpportunities = async (strategyId: string, symbol: string = 'SPY') => {
    // For now, just reload all opportunities since we're using the general endpoint
    await loadAllOpportunities();
  };

  const getStrategiesByCategory = (category: string): StrategyMetadata[] => {
    return strategies.filter(strategy => strategy.category === category);
  };

  const getAllOpportunities = (): any[] => {
    const allOpportunities: any[] = [];
    
    Object.values(opportunitiesByStrategy).forEach(strategyData => {
      allOpportunities.push(...strategyData.opportunities);
    });
    
    // Sort by score descending
    return allOpportunities.sort((a, b) => (b.score || 0) - (a.score || 0));
  };

  const getOpportunitiesByCategory = (category: string): any[] => {
    const categoryStrategies = getStrategiesByCategory(category);
    const categoryOpportunities: any[] = [];
    
    categoryStrategies.forEach(strategy => {
      const strategyData = opportunitiesByStrategy[strategy.id];
      if (strategyData) {
        categoryOpportunities.push(...strategyData.opportunities);
      }
    });
    
    // Sort by score descending
    return categoryOpportunities.sort((a, b) => (b.score || 0) - (a.score || 0));
  };

  // Load strategies on mount with immediate parallel data loading
  useEffect(() => {
    const initializeApp = async () => {
      try {
        setLoading(true);
        
        // Load strategies and opportunities in parallel
        const [strategiesResponse, opportunitiesResponse] = await Promise.allSettled([
          fetch('/api/strategies/'),
          fetch('/api/trading/opportunities')
        ]);
        
        // Process strategies
        let strategiesData: any = null;
        if (strategiesResponse.status === 'fulfilled' && strategiesResponse.value.ok) {
          strategiesData = await strategiesResponse.value.json();
          const enhancedStrategies = strategiesData.strategies.map((strategy: any) => ({
            ...strategy,
            category: strategy.category || getCategoryFromStrategyType(strategy.id),
            status: (strategy.enabled === true) ? 'active' as const : 'inactive' as const,
            last_updated: new Date().toISOString(),
            performance_stats: {},
            config: {
              min_dte: strategy.min_dte,
              max_dte: strategy.max_dte,
              risk_level: strategy.risk_level,
              enabled: strategy.enabled
            }
          }));
          
          const uniqueCategories = [...new Set(enhancedStrategies.map(s => s.category))];
          setStrategies(enhancedStrategies);
          setCategories(uniqueCategories);
        }
        
        // Process opportunities in parallel
        if (opportunitiesResponse.status === 'fulfilled' && opportunitiesResponse.value.ok) {
          const oppData = await opportunitiesResponse.value.json();
          const allOpportunities = oppData.opportunities || [];
          
          // Distribute opportunities to strategies
          const opportunitiesByStrategy: Record<string, OpportunityData> = {};
          const currentStrategies = strategiesData ? strategiesData.strategies : [];
          
          currentStrategies.forEach((strategy: any) => {
            opportunitiesByStrategy[strategy.id] = {
              strategy_id: strategy.id,
              strategy_name: strategy.name,
              opportunities: [],
              count: 0,
              generated_at: new Date().toISOString(),
              market_conditions: {}
            };
          });
          
          allOpportunities.forEach((opp: any) => {
            const targetStrategyId = opp.strategy_type || 'IronCondor';
            if (opportunitiesByStrategy[targetStrategyId]) {
              opportunitiesByStrategy[targetStrategyId].opportunities.push(opp);
              opportunitiesByStrategy[targetStrategyId].count += 1;
            }
          });
          
          setOpportunitiesByStrategy(opportunitiesByStrategy);
        }
        
      } catch (err) {
        console.error('Error initializing app:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize');
      } finally {
        setLoading(false);
      }
    };
    
    initializeApp();
  }, []);

  const value: StrategyContextType = {
    strategies,
    categories,
    loading,
    error,
    opportunitiesByStrategy,
    loadingOpportunities,
    activeScanJobs,
    refreshStrategies,
    refreshAllOpportunities: refreshAllOpportunitiesWithJobs,
    refreshStrategyWithProgress,
    getStrategyOpportunities,
    getStrategiesByCategory,
    getAllOpportunities,
    getOpportunitiesByCategory,
  };

  return (
    <StrategyContext.Provider value={value}>
      {children}
    </StrategyContext.Provider>
  );
};