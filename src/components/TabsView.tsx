import * as Tabs from "@/components/ui/tabs";
import { Suspense, lazy } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Loader2 } from "lucide-react";

const LoadingFallback = () => (
  <div className="space-y-6">
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-center space-x-2">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">Loading tab content...</span>
        </div>
        <div className="space-y-4 mt-4">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-32 w-full" />
        </div>
      </CardContent>
    </Card>
  </div>
);

// Lazy imports — keep these at module scope
const TradeManager = lazy(() =>
  import("@/components/TradeManager").then(m => ({ default: m.TradeManager }))
);
const EnhancedSignalsTab = lazy(() =>
  import("@/components/EnhancedSignalsTab").then(m => ({ default: m.default }))
);
const EnhancedRiskTab = lazy(() =>
  import("@/components/EnhancedRiskTab").then(m => ({ default: m.default }))
);
const StrategiesTab = lazy(() =>
  import("@/components/StrategiesTab").then(m => ({ default: m.StrategiesTab }))
);

export default function TabsView() {
  return (
    <Tabs.Root defaultValue="execution">
      <Tabs.List className="grid w-full grid-cols-4">
        <Tabs.Trigger value="execution">Execution</Tabs.Trigger>
        <Tabs.Trigger value="positions">Positions</Tabs.Trigger>
        <Tabs.Trigger value="signals">Signals</Tabs.Trigger>
        <Tabs.Trigger value="strategies">Strategies</Tabs.Trigger>
      </Tabs.List>

      <Tabs.Content value="execution" className="space-y-6">
        <div className="p-4">
          <h2>🚀 Trading Execution</h2>
          <p>Live trading opportunities and execution interface.</p>
        </div>
      </Tabs.Content>

      <Tabs.Content value="positions" className="space-y-6">
        <Suspense fallback={<LoadingFallback />}>
          <TradeManager />
        </Suspense>
      </Tabs.Content>

      <Tabs.Content value="signals" className="space-y-6">
        <Suspense fallback={<LoadingFallback />}>
          <EnhancedSignalsTab />
        </Suspense>
      </Tabs.Content>

      <Tabs.Content value="strategies" className="space-y-6">
        <Suspense fallback={<LoadingFallback />}>
          <StrategiesTab />
        </Suspense>
      </Tabs.Content>
    </Tabs.Root>
  );
}