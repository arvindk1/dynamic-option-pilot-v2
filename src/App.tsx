import React, { Suspense, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { StrategyProvider } from "./contexts/StrategyContext";
import { AccessibilityProvider } from "./components/AccessibilityProvider";
import { Loader2 } from "lucide-react";
import NotFound from "./pages/NotFound";
import { measurePageLoad, PerformanceMonitor } from "./utils/performance";

// Lazy load heavy components
const Index = React.lazy(() => import("./pages/Index"));
const ButterflyDemo = React.lazy(() => import("./components/ButterflyDemo"));

const AppLoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="flex items-center space-x-2">
      <Loader2 className="h-8 w-8 animate-spin" />
      <span className="text-lg">Loading Trading Platform...</span>
    </div>
  </div>
);

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000, // Cache data for 30 seconds
      gcTime: 300000,   // Keep in cache for 5 minutes
      retry: 1,         // Reduce retry attempts for faster failure
      refetchOnWindowFocus: false, // Prevent unnecessary refetches
    },
  },
});

const App = () => {
  console.log('🚀 App component rendering...');
  
  useEffect(() => {
    measurePageLoad();
    
    // Report performance after 5 seconds
    setTimeout(() => {
      const monitor = PerformanceMonitor.getInstance();
      console.log(monitor.getReport());
    }, 5000);
  }, []);
  
  try {
    return (
      <ThemeProvider>
        <AccessibilityProvider>
          <QueryClientProvider client={queryClient}>
            <StrategyProvider>
              <TooltipProvider>
                <Toaster />
                <Sonner />
                <BrowserRouter
                  future={{
                    v7_startTransition: true,
                    v7_relativeSplatPath: true
                  }}
                >
                  <Suspense fallback={<AppLoadingFallback />}>
                    <Routes>
                      <Route path="/" element={<Index />} />
                      <Route path="/demo" element={<ButterflyDemo />} />
                      {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                      <Route path="*" element={<NotFound />} />
                    </Routes>
                  </Suspense>
                </BrowserRouter>
              </TooltipProvider>
            </StrategyProvider>
          </QueryClientProvider>
        </AccessibilityProvider>
      </ThemeProvider>
    );
  } catch (error) {
    console.error('❌ Error in App component:', error);
    return <div style={{padding: '20px', color: 'red'}}>
      <h1>App Error</h1>
      <p>Error: {error.message}</p>
      <pre>{error.stack}</pre>
    </div>;
  }
};

export default App;
