import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Pin, Eye, Play, Bookmark, BookmarkX } from 'lucide-react';

interface TradeOpportunity {
  id: string;
  symbol: string;
  strategy_type: string;
  premium?: number;
  probability_profit?: number;
  max_loss?: number;
}

interface TradeCardActionsProps {
  trade: TradeOpportunity;
  onExecute?: (trade: TradeOpportunity) => void;
  onPin?: (trade: TradeOpportunity, pinned: boolean) => void;
  isPinned?: boolean;
  isExecuting?: boolean;
}

const TradeCardActions: React.FC<TradeCardActionsProps> = ({ 
  trade, 
  onExecute, 
  onPin,
  isPinned = false,
  isExecuting = false 
}) => {
  const [showLegs, setShowLegs] = useState(false);

  const handleExecute = () => {
    if (onExecute && !isExecuting) {
      onExecute(trade);
    }
  };

  const handlePin = () => {
    if (onPin) {
      onPin(trade, !isPinned);
    }
  };

  // Quick stats for compact display
  const winRate = ((trade.probability_profit || 0) * 100).toFixed(0);
  const premium = trade.premium?.toFixed(2) || '0.00';

  return (
    <div className="px-4 pb-4">
      {/* Quick Stats Row */}
      <div className="flex items-center justify-between mb-3 py-2 bg-gray-50 rounded px-3">
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <span className="text-gray-500">Win:</span>
            <span className="font-semibold text-green-600">{winRate}%</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-gray-500">Credit:</span>
            <span className="font-semibold text-blue-600">${premium}</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="text-gray-500">Risk:</span>
            <span className="font-semibold text-red-600">
              ${trade.max_loss ? Math.abs(trade.max_loss).toFixed(0) : 'N/A'}
            </span>
          </div>
        </div>
        
        {/* Quality indicator */}
        <Badge 
          variant="outline" 
          className={`text-xs ${
            parseFloat(winRate) >= 70 
              ? 'bg-green-50 text-green-700 border-green-200'
              : parseFloat(winRate) >= 50
              ? 'bg-amber-50 text-amber-700 border-amber-200'
              : 'bg-red-50 text-red-700 border-red-200'
          }`}
        >
          {parseFloat(winRate) >= 70 ? 'High Prob' : parseFloat(winRate) >= 50 ? 'Medium' : 'Speculative'}
        </Badge>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          {/* View Legs Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowLegs(!showLegs)}
            className="text-xs"
          >
            <Eye className="w-3 h-3 mr-1" />
            {showLegs ? 'Hide Legs' : 'View Legs'}
          </Button>

          {/* Simulate Button - placeholder for future */}
          <Button
            variant="outline"
            size="sm"
            className="text-xs"
            disabled
          >
            <Play className="w-3 h-3 mr-1" />
            Simulate
          </Button>
        </div>

        <div className="flex space-x-2">
          {/* Pin Button */}
          <Button
            variant={isPinned ? "default" : "outline"}
            size="sm"
            onClick={handlePin}
            className={`text-xs ${isPinned ? 'bg-blue-100 text-blue-700 border-blue-300' : ''}`}
          >
            {isPinned ? <BookmarkX className="w-3 h-3 mr-1" /> : <Bookmark className="w-3 h-3 mr-1" />}
            {isPinned ? 'Unpin' : 'Pin'}
          </Button>

          {/* Execute Button */}
          <Button
            onClick={handleExecute}
            disabled={isExecuting}
            size="sm"
            className="bg-green-600 hover:bg-green-700 text-white text-xs"
          >
            {isExecuting ? (
              <div className="flex items-center space-x-1">
                <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Executing...</span>
              </div>
            ) : (
              'Execute Trade'
            )}
          </Button>
        </div>
      </div>

      {/* Option Legs Details - Expandable */}
      {showLegs && (
        <div className="mt-3 p-3 bg-gray-50 rounded-lg border">
          <div className="text-xs text-gray-600 mb-2 font-semibold">Option Legs:</div>
          <div className="text-xs space-y-1">
            <div className="flex justify-between">
              <span>Strategy:</span>
              <span className="font-mono">{trade.strategy_type}</span>
            </div>
            <div className="flex justify-between">
              <span>Symbol:</span>
              <span className="font-mono">{trade.symbol}</span>
            </div>
            <div className="text-center py-2 text-gray-500">
              Detailed leg information coming soon...
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default React.memo(TradeCardActions);