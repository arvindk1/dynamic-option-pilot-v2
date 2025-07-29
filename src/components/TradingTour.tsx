/**
 * TradingTour Component
 * Provides guided tour for new users using react-joyride
 */

import React, { useCallback, useState } from 'react';
import Joyride, { 
  CallBackProps, 
  STATUS, 
  Step,
  Styles,
  TooltipRenderProps 
} from 'react-joyride';
import { Button } from '@/components/ui/button';
import { 
  ChevronLeft, 
  ChevronRight, 
  X, 
  Play,
  RotateCcw
} from 'lucide-react';

interface TradingTourProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

// Custom tooltip component for better styling
const CustomTooltip: React.FC<TooltipRenderProps> = ({
  continuous,
  index,
  step,
  backProps,
  closeProps,
  primaryProps,
  tooltipProps,
  skipProps,
  size,
  isLastStep,
}) => (
  <div
    {...tooltipProps}
    className="bg-white rounded-lg shadow-xl border border-gray-200 p-6 max-w-sm"
  >
    <div className="flex justify-between items-start mb-4">
      <h3 className="text-lg font-semibold text-gray-900">{step.title}</h3>
      <Button
        {...closeProps}
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
    
    <div className="text-gray-600 mb-4">
      {step.content}
    </div>
    
    <div className="flex justify-between items-center">
      <div className="text-xs text-gray-400">
        Step {index + 1} of {size}
      </div>
      
      <div className="flex gap-2">
        {index > 0 && (
          <Button
            {...backProps}
            variant="outline"
            size="sm"
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back
          </Button>
        )}
        
        {continuous && (
          <Button
            {...primaryProps}
            size="sm"
            className={isLastStep ? 'bg-green-600 hover:bg-green-700' : ''}
          >
            {isLastStep ? 'Finish' : 'Next'}
            {!isLastStep && <ChevronRight className="h-4 w-4 ml-1" />}
          </Button>
        )}
        
        {!continuous && (
          <Button
            {...skipProps}
            variant="ghost"
            size="sm"
          >
            Skip Tour
          </Button>
        )}
      </div>
    </div>
  </div>
);

export const TradingTour: React.FC<TradingTourProps> = ({
  isOpen,
  onClose,
  onComplete,
}) => {
  const [stepIndex, setStepIndex] = useState(0);

  // Tour steps targeting key elements of the trading dashboard
  const steps: Step[] = [
    {
      target: '.dashboard-overview',
      content: (
        <div>
          <p className="mb-3">
            Welcome to Dynamic Option Pilot! This is your <strong>account overview</strong> 
            showing your current balance, buying power, and performance metrics.
          </p>
          <p className="text-sm text-blue-600">
            💡 In demo mode, you'll see sample data to explore the platform safely.
          </p>
        </div>
      ),
      title: 'Account Overview',
      placement: 'bottom',
      disableBeacon: true,
    },
    {
      target: '.market-data-section',
      content: (
        <div>
          <p className="mb-3">
            This section shows <strong>live market data</strong> for SPY including price, 
            volume, and technical indicators like RSI and MACD.
          </p>
          <p className="text-sm text-green-600">
            📊 Technical indicators help identify trading opportunities.
          </p>
        </div>
      ),
      title: 'Market Data',
      placement: 'right',
    },
    {
      target: '.trades-tab',
      content: (
        <div>
          <p className="mb-3">
            The <strong>Trades tab</strong> is where you'll find trading opportunities. 
            Our system analyzes the market and suggests credit spreads, single options, 
            and specialized strategies.
          </p>
          <p className="text-sm text-purple-600">
            🎯 Opportunities are categorized by probability and timeframe.
          </p>
        </div>
      ),
      title: 'Trading Opportunities',
      placement: 'bottom',
    },
    {
      target: '.opportunity-categories',
      content: (
        <div>
          <p className="mb-3">
            Use these <strong>category filters</strong> to find trades that match your style:
          </p>
          <ul className="text-sm space-y-1 mb-3">
            <li>• <strong>High Probability:</strong> Conservative trades with high win rates</li>
            <li>• <strong>Quick Scalps:</strong> Short-term opportunities</li>
            <li>• <strong>RSI Coupon:</strong> Our signature oversold strategy</li>
          </ul>
        </div>
      ),
      title: 'Trade Categories',
      placement: 'top',
    },
    {
      target: '.trade-execution-btn',
      content: (
        <div>
          <p className="mb-3">
            When you find a trade you like, click the <strong>Execute button</strong>. 
            Our risk management system will validate the trade before execution.
          </p>
          <p className="text-sm text-yellow-600">
            ⚠️ All trades go through risk validation to protect your account.
          </p>
        </div>
      ),
      title: 'Trade Execution & Risk Management',
      placement: 'top',
    },
    {
      target: '.positions-tab',
      content: (
        <div>
          <p className="mb-3">
            The <strong>Positions tab</strong> shows your open trades with real-time P&L, 
            Greeks, and position management tools.
          </p>
          <p className="text-sm text-blue-600">
            📈 Track your trades and close them manually when needed.
          </p>
        </div>
      ),
      title: 'Position Management',
      placement: 'bottom',
    },
    {
      target: '.analytics-tab',
      content: (
        <div>
          <p className="mb-3">
            <strong>Analytics</strong> provides insights into your trading performance 
            with metrics like win rate, Sharpe ratio, and risk analysis.
          </p>
          <p className="text-sm text-green-600">
            📊 Use these metrics to improve your trading strategy.
          </p>
        </div>
      ),
      title: 'Performance Analytics',
      placement: 'bottom',
    },
    {
      target: '.demo-mode-toggle',
      content: (
        <div>
          <p className="mb-3">
            Toggle <strong>Demo Mode</strong> to practice with simulated data, 
            or switch to live mode when you're ready to trade with real money.
          </p>
          <p className="text-sm text-red-600">
            🛡️ Start with demo mode to familiarize yourself with the platform.
          </p>
        </div>
      ),
      title: 'Demo vs Live Mode',
      placement: 'left',
    },
  ];

  // Custom styles for the tour
  const joyrideStyles: Styles = {
    options: {
      primaryColor: '#3b82f6',
      zIndex: 10000,
    },
    overlay: {
      backgroundColor: 'rgba(0, 0, 0, 0.4)',
    },
    spotlight: {
      borderRadius: '8px',
    },
  };

  const handleJoyrideCallback = useCallback((data: CallBackProps) => {
    const { status, type, index, action } = data;
    
    if ([STATUS.FINISHED, STATUS.SKIPPED].includes(status)) {
      onComplete();
      onClose();
    } else if (type === 'step:after') {
      setStepIndex(index + (action === 'next' ? 1 : -1));
    }
  }, [onComplete, onClose]);

  if (!isOpen) return null;

  return (
    <Joyride
      steps={steps}
      run={isOpen}
      continuous
      showProgress
      showSkipButton
      stepIndex={stepIndex}
      callback={handleJoyrideCallback}
      styles={joyrideStyles}
      tooltipComponent={CustomTooltip}
      locale={{
        back: 'Back',
        close: 'Close',
        last: 'Finish Tour',
        next: 'Next',
        skip: 'Skip Tour',
      }}
    />
  );
};

// Tour trigger button component
interface TourTriggerProps {
  onStartTour: () => void;
  variant?: 'button' | 'link';
  className?: string;
}

export const TourTrigger: React.FC<TourTriggerProps> = ({ 
  onStartTour, 
  variant = 'button',
  className = ''
}) => {
  if (variant === 'link') {
    return (
      <button
        onClick={onStartTour}
        className={`text-sm text-blue-600 hover:text-blue-800 underline flex items-center gap-1 ${className}`}
      >
        <Play className="h-3 w-3" />
        Take Tour
      </button>
    );
  }

  return (
    <Button
      onClick={onStartTour}
      variant="outline"
      size="sm"
      className={className}
    >
      <RotateCcw className="h-4 w-4 mr-2" />
      Restart Tour
    </Button>
  );
};