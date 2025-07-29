import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, CheckCircle, Shield } from 'lucide-react';

interface RiskValidationResult {
  valid: boolean;
  warnings: string[];
  margin_required: number;
  buying_power_effect: number;
  max_loss: number;
  max_profit: number;
  break_even: number;
  margin_usage_pct: number;
  position_count_after: number;
  new_delta_exposure: number;
}

interface RiskValidationDialogProps {
  isOpen: boolean;
  isValidating: boolean;
  riskValidation: RiskValidationResult | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export const RiskValidationDialog: React.FC<RiskValidationDialogProps> = React.memo(({
  isOpen,
  isValidating,
  riskValidation,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <AlertDialog open={isOpen}>
      <AlertDialogContent className="max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2 text-blue-600" />
            Risk Assessment
          </AlertDialogTitle>
          <AlertDialogDescription>
            Review the risk analysis before executing this trade.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-4">
          {isValidating ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-muted-foreground">Validating trade risk...</span>
            </div>
          ) : riskValidation ? (
            <>
              <div className="flex items-center mb-4">
                {riskValidation.valid ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mr-2" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-red-600 mr-2" />
                )}
                <Badge variant={riskValidation.valid ? "default" : "destructive"}>
                  {riskValidation.valid ? "Risk Acceptable" : "Risk Warning"}
                </Badge>
              </div>

              {riskValidation.warnings.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-yellow-800 mb-2">Warnings:</h4>
                  <ul className="text-sm text-yellow-700 space-y-1">
                    {riskValidation.warnings.map((warning, index) => (
                      <li key={index} className="flex items-start">
                        <AlertTriangle className="h-4 w-4 mr-2 mt-0.5" />
                        {warning}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-background p-3 rounded border">
                  <div className="text-sm text-muted-foreground mb-1">Margin Required</div>
                  <div className="text-lg font-bold">${riskValidation.margin_required.toFixed(2)}</div>
                </div>
                <div className="bg-background p-3 rounded border">
                  <div className="text-sm text-muted-foreground mb-1">Buying Power Effect</div>
                  <div className="text-lg font-bold">${riskValidation.buying_power_effect.toFixed(2)}</div>
                </div>
                <div className="bg-background p-3 rounded border">
                  <div className="text-sm text-muted-foreground mb-1">Max Loss</div>
                  <div className="text-lg font-bold text-red-600">${riskValidation.max_loss.toFixed(2)}</div>
                </div>
                <div className="bg-background p-3 rounded border">
                  <div className="text-sm text-muted-foreground mb-1">Break Even</div>
                  <div className="text-lg font-bold">${riskValidation.break_even.toFixed(2)}</div>
                </div>
              </div>

              <div className="bg-background p-4 rounded border">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Margin Usage</span>
                  <span className="text-sm font-semibold">{riskValidation.margin_usage_pct.toFixed(1)}%</span>
                </div>
                <Progress value={riskValidation.margin_usage_pct} className="h-2" />
                <div className="text-xs text-muted-foreground mt-1">
                  Position count after: {riskValidation.position_count_after} | 
                  New delta exposure: {riskValidation.new_delta_exposure.toFixed(2)}
                </div>
              </div>
            </>
          ) : null}
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel onClick={onCancel}>Cancel</AlertDialogCancel>
          <AlertDialogAction 
            onClick={onConfirm} 
            disabled={isValidating || !riskValidation?.valid}
            className="bg-blue-600 hover:bg-blue-700"
          >
            Execute Trade
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
});

RiskValidationDialog.displayName = 'RiskValidationDialog';