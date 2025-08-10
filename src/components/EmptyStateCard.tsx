import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, TrendingDown, Target, Settings, Lightbulb } from 'lucide-react';

interface EmptyStateCardProps {
  title?: string;
  description?: string;
  suggestions?: string[];
  onReset?: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

const EmptyStateCard: React.FC<EmptyStateCardProps> = ({
  title = "No Trading Opportunities Found",
  description = "No opportunities match your current parameters. Try adjusting your search criteria.",
  suggestions = [
    "Try a smaller universe (fewer symbols)",
    "Adjust DTE range (try 14-45 days)", 
    "Widen strike delta range",
    "Lower minimum probability threshold",
    "Check different strategy types"
  ],
  onReset,
  onRefresh,
  isLoading = false
}) => {
  return (
    <Card className="mx-auto max-w-md text-center p-6 border-dashed border-2 border-gray-200 bg-gray-50/50">
      <CardContent className="space-y-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
            <Target className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        {/* Title & Description */}
        <div className="space-y-2">
          <h3 className="text-lg font-semibold text-gray-900">
            {title}
          </h3>
          <p className="text-sm text-gray-600 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Suggestions */}
        {suggestions && suggestions.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-center space-x-1">
              <Lightbulb className="w-4 h-4 text-amber-500" />
              <span className="text-sm font-medium text-gray-700">Try these adjustments:</span>
            </div>
            
            <div className="space-y-2">
              {suggestions.map((suggestion, index) => (
                <div key={index} className="flex items-center text-left space-x-2 p-2 bg-white rounded-lg border text-sm">
                  <div className="w-1.5 h-1.5 bg-blue-400 rounded-full flex-shrink-0 mt-1" />
                  <span className="text-gray-600">{suggestion}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Quick Stats Hint */}
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-center space-x-4 text-xs text-blue-700">
            <div className="flex items-center space-x-1">
              <TrendingDown className="w-3 h-3" />
              <span>High probability: &gt;70%</span>
            </div>
            <div className="flex items-center space-x-1">
              <Settings className="w-3 h-3" />
              <span>DTE: 14-45 days</span>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-center space-x-3">
          {onReset && (
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onReset}
              className="text-xs"
            >
              <Settings className="w-3 h-3 mr-1" />
              Reset to Defaults
            </Button>
          )}
          
          {onRefresh && (
            <Button 
              variant="default" 
              size="sm" 
              onClick={onRefresh}
              disabled={isLoading}
              className="text-xs bg-blue-600 hover:bg-blue-700"
            >
              {isLoading ? (
                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />
              ) : (
                <RefreshCw className="w-3 h-3 mr-1" />
              )}
              Refresh Scan
            </Button>
          )}
        </div>

        {/* Footer hint */}
        <div className="pt-2 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            💡 Markets change quickly. Try refreshing or adjusting parameters above.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};

export default EmptyStateCard;