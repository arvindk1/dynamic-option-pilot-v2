import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ConnectionStatus } from '@/services/WebSocketService';
import { Wifi, WifiOff, RefreshCw, AlertCircle } from 'lucide-react';

export const WebSocketStatus: React.FC = () => {
  const { state, connect, disconnect } = useWebSocket();

  const getStatusColor = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return 'bg-green-500';
      case ConnectionStatus.CONNECTING:
      case ConnectionStatus.RECONNECTING:
        return 'bg-yellow-500';
      case ConnectionStatus.DISCONNECTED:
        return 'bg-gray-500';
      case ConnectionStatus.ERROR:
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return <Wifi className="w-4 h-4" />;
      case ConnectionStatus.CONNECTING:
      case ConnectionStatus.RECONNECTING:
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      case ConnectionStatus.ERROR:
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <WifiOff className="w-4 h-4" />;
    }
  };

  const getStatusText = (status: ConnectionStatus) => {
    switch (status) {
      case ConnectionStatus.CONNECTED:
        return 'Connected';
      case ConnectionStatus.CONNECTING:
        return 'Connecting...';
      case ConnectionStatus.RECONNECTING:
        return 'Reconnecting...';
      case ConnectionStatus.DISCONNECTED:
        return 'Disconnected';
      case ConnectionStatus.ERROR:
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  const handleToggleConnection = async () => {
    try {
      if (state.connected) {
        disconnect();
      } else {
        await connect();
      }
    } catch (error) {
      console.error('Failed to toggle connection:', error);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <Badge 
        variant="outline" 
        className={`flex items-center gap-1 ${getStatusColor(state.status)} text-white border-none`}
      >
        {getStatusIcon(state.status)}
        <span className="text-xs">{getStatusText(state.status)}</span>
      </Badge>
      
      {state.error && (
        <Badge variant="destructive" className="text-xs">
          {state.error}
        </Badge>
      )}
      
      <Button
        variant="outline"
        size="sm"
        onClick={handleToggleConnection}
        className="text-xs px-2 py-1"
      >
        {state.connected ? 'Disconnect' : 'Connect'}
      </Button>
      
      {state.connected && state.lastHeartbeat && (
        <span className="text-xs text-slate-400">
          Last: {new Date(state.lastHeartbeat).toLocaleTimeString()}
        </span>
      )}
    </div>
  );
};

export default WebSocketStatus;