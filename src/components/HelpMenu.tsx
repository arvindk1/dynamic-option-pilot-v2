import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { HelpCircle, Keyboard, Play, X } from 'lucide-react';

interface HelpMenuProps {
  onStartTour: () => void;
}

const keyboardShortcuts = [
  { key: 'Ctrl+1', action: 'Switch to Overview tab' },
  { key: 'Ctrl+2', action: 'Switch to Commentary tab' },
  { key: 'Ctrl+3', action: 'Switch to Sentiment tab' },
  { key: 'Ctrl+4', action: 'Switch to Economic tab' },
  { key: 'Ctrl+5', action: 'Switch to AI Coach tab' },
  { key: 'Ctrl+6', action: 'Switch to Signals tab' },
  { key: 'Ctrl+7', action: 'Switch to Trades tab' },
  { key: 'Ctrl+8', action: 'Switch to Positions tab' },
  { key: 'Ctrl+9', action: 'Switch to Risk tab' },
  { key: 'Ctrl+0', action: 'Switch to Config tab' },
  { key: 'F1', action: 'Open help overlay' },
  { key: 'Esc', action: 'Close current overlay' },
];

export const HelpMenu: React.FC<HelpMenuProps> = ({ onStartTour }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleStartTour = () => {
    setIsOpen(false);
    onStartTour();
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" title="Help & Shortcuts">
          <HelpCircle className="h-[1.2rem] w-[1.2rem]" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <HelpCircle className="h-5 w-5" />
            <span>Help & Shortcuts</span>
          </DialogTitle>
          <DialogDescription>
            Keyboard shortcuts and platform guidance
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Tour Section */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center space-x-2">
                <Play className="h-4 w-4" />
                <span>Platform Tour</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-3">
                Take a guided tour of the trading platform features.
              </p>
              <Button onClick={handleStartTour} size="sm" className="w-full">
                <Play className="h-4 w-4 mr-2" />
                Start Tour
              </Button>
            </CardContent>
          </Card>

          {/* Keyboard Shortcuts */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center space-x-2">
                <Keyboard className="h-4 w-4" />
                <span>Keyboard Shortcuts</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {keyboardShortcuts.map((shortcut, index) => (
                  <div key={index} className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">{shortcut.action}</span>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {shortcut.key}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Tips */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Quick Tips</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm text-muted-foreground">
                <div>• Two-tier navigation: main tabs + sub-tabs for organization</div>
                <div>• Executed trades automatically switch to Positions tab</div>
                <div>• Risk dashboard sections can be collapsed for focus</div>
                <div>• Account summary stays visible during navigation</div>
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
};