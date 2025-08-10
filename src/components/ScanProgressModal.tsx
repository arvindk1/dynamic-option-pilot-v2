import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Loader2, X, CheckCircle, AlertCircle, Activity } from 'lucide-react';

interface ScanJob {
  strategy_id: string;
  status: 'running' | 'completed' | 'error' | 'cancelled';
  progress: number;
  current_symbol: string | null;
  total_symbols: number;
  opportunities_found: number;
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

interface ScanProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobId: string | null;
  strategyName: string;
  onComplete?: (opportunitiesFound: number) => void;
}

const ScanProgressModal: React.FC<ScanProgressModalProps> = ({
  isOpen,
  onClose,
  jobId,
  strategyName,
  onComplete
}) => {
  const [job, setJob] = useState<ScanJob | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Poll for job status
  useEffect(() => {
    if (!jobId || !isOpen) {
      setIsPolling(false);
      return;
    }

    const pollJobStatus = async () => {
      try {
        const response = await fetch(`/api/scan/${jobId}/status`);
        if (response.ok) {
          const jobData = await response.json();
          setJob(jobData);

          // Stop polling when job is done
          if (jobData.status === 'completed' || jobData.status === 'error' || jobData.status === 'cancelled') {
            setIsPolling(false);
            if (jobData.status === 'completed' && onComplete) {
              onComplete(jobData.opportunities_found);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll job status:', error);
      }
    };

    setIsPolling(true);
    pollJobStatus(); // Initial poll

    const interval = setInterval(pollJobStatus, 1000); // Poll every second
    return () => clearInterval(interval);
  }, [jobId, isOpen, onComplete]);

  const handleCancel = async () => {
    if (jobId && job?.status === 'running') {
      try {
        await fetch(`/api/scan/${jobId}`, { method: 'DELETE' });
      } catch (error) {
        console.error('Failed to cancel job:', error);
      }
    }
    onClose();
  };

  const getStatusIcon = () => {
    if (!job) return <Loader2 className="w-5 h-5 animate-spin" />;
    
    switch (job.status) {
      case 'running':
        return <Activity className="w-5 h-5 animate-pulse text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'cancelled':
        return <X className="w-5 h-5 text-gray-500" />;
      default:
        return <Loader2 className="w-5 h-5 animate-spin" />;
    }
  };

  const getStatusText = () => {
    if (!job) return 'Initializing scan...';
    
    switch (job.status) {
      case 'running':
        return job.current_symbol 
          ? `Scanning ${job.current_symbol}...`
          : 'Starting scan...';
      case 'completed':
        return `Scan completed! Found ${job.opportunities_found} opportunities.`;
      case 'error':
        return `Scan failed: ${job.error}`;
      case 'cancelled':
        return 'Scan cancelled.';
      default:
        return 'Processing...';
    }
  };

  const getStatusColor = () => {
    if (!job) return 'bg-blue-100 text-blue-800';
    
    switch (job.status) {
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {getStatusIcon()}
            Scanning {strategyName}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Status Badge */}
          <div className="flex justify-center">
            <Badge variant="outline" className={`${getStatusColor()} px-3 py-1`}>
              {job?.status?.toUpperCase() || 'STARTING'}
            </Badge>
          </div>

          {/* Progress Bar */}
          {job && job.status === 'running' && (
            <div className="space-y-2">
              <Progress value={job.progress} className="w-full" />
              <div className="flex justify-between text-sm text-gray-600">
                <span>{job.progress}% complete</span>
                <span>{job.total_symbols > 0 ? `${Math.floor(job.progress / 100 * job.total_symbols)}/${job.total_symbols} symbols` : ''}</span>
              </div>
            </div>
          )}

          {/* Current Status */}
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-700">{getStatusText()}</p>
          </div>

          {/* Results Preview */}
          {job && job.opportunities_found > 0 && (
            <div className="text-center p-3 bg-green-50 rounded-lg border border-green-200">
              <div className="text-lg font-semibold text-green-800">
                {job.opportunities_found} opportunities found
              </div>
              <div className="text-sm text-green-600">
                Ready to analyze and execute
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 justify-end">
            {job?.status === 'running' && (
              <Button variant="outline" onClick={handleCancel}>
                Cancel Scan
              </Button>
            )}
            
            {(job?.status === 'completed' || job?.status === 'error' || job?.status === 'cancelled') && (
              <Button onClick={onClose}>
                {job.status === 'completed' ? 'View Results' : 'Close'}
              </Button>
            )}
          </div>

          {/* Technical Details (Collapsible) */}
          {job && (
            <details className="text-xs text-gray-500">
              <summary className="cursor-pointer hover:text-gray-700">Technical Details</summary>
              <div className="mt-2 p-2 bg-gray-100 rounded text-xs font-mono">
                <div>Job ID: {jobId}</div>
                <div>Started: {new Date(job.started_at).toLocaleTimeString()}</div>
                {job.completed_at && (
                  <div>Completed: {new Date(job.completed_at).toLocaleTimeString()}</div>
                )}
                <div>Strategy: {job.strategy_id}</div>
              </div>
            </details>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ScanProgressModal;