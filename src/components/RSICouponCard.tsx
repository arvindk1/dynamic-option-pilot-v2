import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface RSICouponOpportunity {
  id: string;
  symbol: string;
  current_price: number;
  rsi: number;
  sma_50: number;
  signal_strength: number;
  days_below_30: number;
  option_type: string;
  strike: number;
  expiration: string;
  days_to_expiration: number;
  premium: number;
  estimated_delta: number;
  alternative_options: number;
  contracts: number;
  total_cost: number;
  account_risk_pct: number;
  profit_target: number;
  stop_loss: number;
  entry_reason: string;
  selection_reason: string;
  confidence: number;
}

interface RSICouponCardProps {
  opportunity: RSICouponOpportunity;
  onExecute: (opportunity: RSICouponOpportunity) => void;
}

export const RSICouponCard = ({ opportunity, onExecute }: RSICouponCardProps) => {
  const getRSIColor = (rsi: number) => {
    if (rsi < 20) return "bg-red-100 text-red-800 border-red-200";
    if (rsi < 30) return "bg-orange-100 text-orange-800 border-orange-200";
    return "bg-gray-100 text-gray-800 border-gray-200";
  };

  const getDeltaColor = (delta: number) => {
    if (delta >= 0.35) return "text-green-600";
    if (delta >= 0.30) return "text-blue-600";
    return "text-gray-600";
  };

  return (
    <Card className="border-l-4 border-l-green-500 hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            🎫 RSI COUPON STRATEGY
            <Badge className={getRSIColor(opportunity.rsi)}>
              RSI: {opportunity.rsi}
            </Badge>
          </CardTitle>
          <Badge variant="secondary" className="font-semibold">
            {opportunity.confidence}% Confidence
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Stage 1: Equity Analysis */}
        <div className="bg-blue-50 p-3 rounded-lg border">
          <h4 className="font-semibold text-sm text-blue-800 mb-2">📊 Stage 1: Equity Screening</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-600">Symbol:</span>
              <span className="font-semibold ml-2">{opportunity.symbol}</span>
            </div>
            <div>
              <span className="text-gray-600">Current Price:</span>
              <span className="font-semibold ml-2">${opportunity.current_price}</span>
            </div>
            <div>
              <span className="text-gray-600">RSI (14):</span>
              <span className="font-semibold ml-2 text-orange-600">{opportunity.rsi} (Oversold)</span>
            </div>
            <div>
              <span className="text-gray-600">vs 50-day SMA:</span>
              <span className="font-semibold ml-2 text-green-600">
                +{((opportunity.current_price / opportunity.sma_50 - 1) * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">Signal Strength:</span>
              <span className="font-semibold ml-2">{(opportunity.signal_strength * 10).toFixed(1)}/10</span>
            </div>
            <div>
              <span className="text-gray-600">Days Oversold:</span>
              <span className="font-semibold ml-2">{opportunity.days_below_30}</span>
            </div>
          </div>
        </div>

        {/* Stage 2: Options Selection */}
        <div className="bg-purple-50 p-3 rounded-lg border">
          <h4 className="font-semibold text-sm text-purple-800 mb-2">🎯 Stage 2: Options Filtering</h4>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-gray-600">Option:</span>
              <span className="font-semibold ml-2">
                {opportunity.option_type} ${opportunity.strike}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Expiration:</span>
              <span className="font-semibold ml-2">{opportunity.expiration}</span>
            </div>
            <div>
              <span className="text-gray-600">DTE:</span>
              <span className="font-semibold ml-2">{opportunity.days_to_expiration} days</span>
            </div>
            <div>
              <span className="text-gray-600">Est. Delta:</span>
              <span className={`font-semibold ml-2 ${getDeltaColor(opportunity.estimated_delta)}`}>
                {opportunity.estimated_delta}
              </span>
            </div>
            <div>
              <span className="text-gray-600">Premium:</span>
              <span className="font-semibold ml-2">${opportunity.premium}</span>
            </div>
            <div>
              <span className="text-gray-600">Alternatives:</span>
              <span className="font-semibold ml-2">{opportunity.alternative_options} options</span>
            </div>
          </div>
        </div>

        {/* Position Sizing */}
        <div className="bg-yellow-50 p-3 rounded-lg border">
          <h4 className="font-semibold text-sm text-yellow-800 mb-2">💰 Position Sizing (0.5% Risk Rule)</h4>
          <div className="grid grid-cols-3 gap-3 text-sm">
            <div>
              <span className="text-gray-600">Contracts:</span>
              <span className="font-semibold ml-2">{opportunity.contracts}</span>
            </div>
            <div>
              <span className="text-gray-600">Total Cost:</span>
              <span className="font-semibold ml-2">${opportunity.total_cost.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600">Account Risk:</span>
              <span className="font-semibold ml-2">{opportunity.account_risk_pct}%</span>
            </div>
          </div>
        </div>

        {/* Exit Criteria */}
        <div className="bg-red-50 p-3 rounded-lg border-l-4 border-l-red-400">
          <h4 className="font-semibold text-sm text-red-800 mb-2">🚪 EXIT CRITERIA (First to Hit)</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-green-600 font-medium">✅ Profit Target:</span>
              <span className="font-bold">${opportunity.profit_target} (+50%)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-red-600 font-medium">❌ Stop Loss:</span>
              <span className="font-bold">${opportunity.stop_loss} (-30%)</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-600 font-medium">⏰ Time Stop:</span>
              <span className="font-bold">≤ 21 DTE</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-purple-600 font-medium">📈 Signal Exit:</span>
              <span className="font-bold text-xs">RSI ≥ 50 OR Price &lt; ${opportunity.sma_50.toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Entry Reason */}
        <div className="text-sm bg-green-50 p-2 rounded border-l-2 border-l-green-400">
          <strong>Entry Logic:</strong> {opportunity.entry_reason}
        </div>
        <div className="text-sm bg-blue-50 p-2 rounded border-l-2 border-l-blue-400">
          <strong>Selection:</strong> {opportunity.selection_reason}
        </div>

        {/* Execute Button */}
        <Button 
          className="w-full bg-green-600 hover:bg-green-700"
          onClick={() => onExecute(opportunity)}
        >
          Execute RSI Coupon Trade (${opportunity.total_cost.toLocaleString()})
        </Button>
      </CardContent>
    </Card>
  );
};