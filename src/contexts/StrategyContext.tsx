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

interface StrategyContextType {
  // Strategy metadata
  strategies: StrategyMetadata[];
  categories: string[];
  loading: boolean;
  error: string | null;
  
  // Strategy opportunities
  opportunitiesByStrategy: Record<string, OpportunityData>;
  loadingOpportunities: Record<string, boolean>;
  
  // Actions
  refreshStrategies: () => Promise<void>;
  refreshAllOpportunities: () => Promise<void>;
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

export const StrategyProvider: React.FC<StrategyProviderProps> = ({ children }) => {
  const [strategies, setStrategies] = useState<StrategyMetadata[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [opportunitiesByStrategy, setOpportunitiesByStrategy] = useState<Record<string, OpportunityData>>({});
  const [loadingOpportunities, setLoadingOpportunities] = useState<Record<string, boolean>>({});

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

      // Trigger quick-scan for all strategies concurrently
      const scanPromises = strategies.map(async (strategy) => {
        try {
          const response = await fetch(`/api/strategies/${strategy.id}/quick-scan`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          });
          
          if (response.ok) {
            const scanResult = await response.json();
            console.log(`${strategy.name}: ${scanResult.opportunities_found} opportunities`);
            
            // Now fetch the opportunities from the strategy's opportunities endpoint
            const oppResponse = await fetch(`/api/strategies/${strategy.id}/opportunities`);
            if (oppResponse.ok) {
              const oppData = await oppResponse.json();
              opportunitiesByStrategy[strategy.id] = {
                strategy_id: strategy.id,
                strategy_name: strategy.name,
                opportunities: oppData.opportunities || [],
                count: oppData.count || 0,
                generated_at: oppData.generated_at || new Date().toISOString(),
                market_conditions: oppData.market_conditions || {}
              };
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
      const currentStrategies = strategies.length > 0 ? strategies : [
        { id: 'iron_condor', name: 'Iron Condor' },
        { id: 'put_spread', name: 'Put Credit Spread' },  
        { id: 'covered_call', name: 'Covered Call' }
      ];
      
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
      
      // Distribute opportunities to strategies based on strategy_type or characteristics
      allOpportunities.forEach((opp: any) => {
        // Map opportunity strategy_type to strategy IDs
        let targetStrategyId = 'IronCondor'; // default
        
        if (opp.strategy_type === 'high_probability' || opp.probability_profit > 0.75) {
          targetStrategyId = 'RSICouponStrategy'; // high probability strategy
        } else if (opp.days_to_expiration > 30) {
          targetStrategyId = 'CoveredCall'; // longer-term strategy
        } else if (opp.strategy_type === 'volatility_play' || opp.liquidity_score > 8) {
          targetStrategyId = 'IronCondor'; // volatility strategy
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
    try {
      setLoading(true);
      setError(null);
      
      // First get basic strategy metadata
      const strategiesResponse = await fetch('/api/strategies/');
      if (!strategiesResponse.ok) {
        throw new Error(`Failed to fetch strategies: ${strategiesResponse.statusText}`);
      }
      
      const strategiesData = await strategiesResponse.json();
      
      // Enhanced strategy metadata with categories
      const enhancedStrategies = strategiesData.strategies.map((strategy: any) => ({
        ...strategy,
        category: strategy.id === 'iron_condor' ? 'volatility_plays' :
                 strategy.id === 'put_spread' ? 'high_probability' :
                 strategy.id === 'covered_call' ? 'swing_trades' : 'other',
        status: strategy.enabled ? 'active' : 'inactive',
        last_updated: new Date().toISOString(),
        performance_stats: {}
      }));
      
      setStrategies(enhancedStrategies);
      setCategories(['high_probability', 'swing_trades', 'volatility_plays']);
      
      // Now load all opportunities and distribute them to strategies
      await loadAllOpportunities();
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load strategies';
      setError(errorMessage);
      console.error('Error fetching strategies:', err);
    } finally {
      setLoading(false);
    }
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

  // Load strategies on mount
  useEffect(() => {
    refreshStrategies();
  }, []);

  // Auto-load opportunities for active strategies
  useEffect(() => {
    if (strategies.length > 0) {
      // Load all opportunities once when strategies are loaded
      loadAllOpportunities();
    }
  }, [strategies]);

  const value: StrategyContextType = {
    strategies,
    categories,
    loading,
    error,
    opportunitiesByStrategy,
    loadingOpportunities,
    refreshStrategies,
    refreshAllOpportunities,
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