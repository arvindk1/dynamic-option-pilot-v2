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

  const refreshStrategies = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/strategies/');
      if (!response.ok) {
        throw new Error(`Failed to fetch strategies: ${response.statusText}`);
      }
      
      const data = await response.json();
      setStrategies(data.strategies || []);
      setCategories(data.categories || []);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load strategies';
      setError(errorMessage);
      console.error('Error fetching strategies:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStrategyOpportunities = async (strategyId: string, symbol: string = 'SPY') => {
    try {
      setLoadingOpportunities(prev => ({ ...prev, [strategyId]: true }));
      
      const response = await fetch(`/api/strategies/${strategyId}/opportunities?symbol=${symbol}&max_opportunities=10`);
      if (!response.ok) {
        throw new Error(`Failed to fetch opportunities for ${strategyId}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setOpportunitiesByStrategy(prev => ({
        ...prev,
        [strategyId]: data
      }));
      
    } catch (err) {
      console.error(`Error fetching opportunities for ${strategyId}:`, err);
      // Set empty data on error
      setOpportunitiesByStrategy(prev => ({
        ...prev,
        [strategyId]: {
          strategy_id: strategyId,
          strategy_name: strategies.find(s => s.id === strategyId)?.name || strategyId,
          opportunities: [],
          count: 0,
          generated_at: new Date().toISOString(),
          market_conditions: {}
        }
      }));
    } finally {
      setLoadingOpportunities(prev => ({ ...prev, [strategyId]: false }));
    }
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
    const activeStrategies = strategies.filter(s => s.status === 'active');
    
    // Load opportunities for each active strategy
    activeStrategies.forEach(strategy => {
      if (!opportunitiesByStrategy[strategy.id] && !loadingOpportunities[strategy.id]) {
        getStrategyOpportunities(strategy.id);
      }
    });
  }, [strategies]);

  const value: StrategyContextType = {
    strategies,
    categories,
    loading,
    error,
    opportunitiesByStrategy,
    loadingOpportunities,
    refreshStrategies,
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