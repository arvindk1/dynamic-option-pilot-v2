import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Info } from 'lucide-react';
import { DataState, DataStateIndicator, isDemoData, getDataStateLabel, getDataStateColor } from '@/types/dataState';

interface DemoModeAlertProps {
  data?: any;
  className?: string;
  variant?: 'banner' | 'inline' | 'badge';
  showDetails?: boolean;
}

export const DemoModeAlert: React.FC<DemoModeAlertProps> = ({ 
  data, 
  className = '', 
  variant = 'inline',
  showDetails = true 
}) => {
  // Don't show anything if there's no data or it's not demo data
  if (!data || !isDemoData(data)) {
    return null;
  }

  const dataState = data.data_state || DataState.DEMO;
  const warning = data.warning || "This is simulated data for development purposes";
  const demoNotice = data.demo_notice;

  // Badge variant - minimal warning
  if (variant === 'badge') {
    return (
      <Badge className={`${getDataStateColor(dataState)} ${className}`}>
        {getDataStateLabel(dataState)}
      </Badge>
    );
  }

  // Banner variant - prominent warning
  if (variant === 'banner') {
    return (
      <Alert variant="destructive" className={`border-2 border-yellow-400 bg-yellow-50 ${className}`}>
        <AlertTriangle className="h-5 w-5 text-yellow-600" />
        <AlertTitle className="text-yellow-800 font-bold text-lg">
          🚨 {getDataStateLabel(dataState)}
        </AlertTitle>
        <AlertDescription className="text-yellow-700">
          <div className="font-medium">{warning}</div>
          {showDetails && demoNotice && (
            <div className="text-sm mt-1 opacity-90">{demoNotice}</div>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  // Inline variant - standard alert
  return (
    <Alert variant="default" className={`border-yellow-300 bg-yellow-50 ${className}`}>
      <Info className="h-4 w-4 text-yellow-600" />
      <AlertTitle className="text-yellow-800 font-semibold">
        {getDataStateLabel(dataState)}
      </AlertTitle>
      {showDetails && (
        <AlertDescription className="text-yellow-700">
          <div className="text-sm">{warning}</div>
          {demoNotice && (
            <div className="text-xs mt-1 opacity-90">{demoNotice}</div>
          )}
        </AlertDescription>
      )}
    </Alert>
  );
};

/**
 * Hook to detect demo mode from any data object
 */
export const useDemoModeDetection = (data: any) => {
  const isDemo = isDemoData(data);
  const dataState = data?.data_state || DataState.UNAVAILABLE;
  const warning = data?.warning;
  const demoNotice = data?.demo_notice;

  return {
    isDemo,
    dataState,
    warning,
    demoNotice,
    label: getDataStateLabel(dataState),
    colorClass: getDataStateColor(dataState)
  };
};

export default DemoModeAlert;