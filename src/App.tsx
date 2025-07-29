import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./contexts/ThemeContext";
import { StrategyProvider } from "./contexts/StrategyContext";
import { AccessibilityProvider } from "./components/AccessibilityProvider";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => {
  console.log('🚀 App component rendering...');
  
  try {
    return (
      <ThemeProvider>
        <AccessibilityProvider>
          <QueryClientProvider client={queryClient}>
            <StrategyProvider>
              <TooltipProvider>
                <Toaster />
                <Sonner />
                <BrowserRouter>
                  <Routes>
                    <Route path="/" element={<Index />} />
                    {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                    <Route path="*" element={<NotFound />} />
                  </Routes>
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
