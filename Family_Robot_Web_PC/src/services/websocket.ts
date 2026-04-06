import { useRobotStore } from '../store/robotStore';

export type RobotCommand =
  | 'forward'
  | 'backward'
  | 'left'
  | 'right'
  | 'stop'
  | 'light_on'
  | 'light_off';

export type WebRTCSignalType = 'offer' | 'answer' | 'candidate';

export interface WebRTCSignalPayload {
  type: WebRTCSignalType;
  offer?: RTCSessionDescriptionInit;
  answer?: RTCSessionDescriptionInit;
  candidate?: RTCIceCandidateInit;
}

export interface WebSocketMessage {
  type: string;
  payload?: any;
  data?: any;
  message?: string;
  role?: string;
}

type MessageListener = (msg: WebSocketMessage) => void;

class WebSocketService {
  private socket: WebSocket | null = null;
  private url: string;

  private reconnectCount = 0;
  private readonly maxReconnect = 5;
  private readonly reconnectDelay = 1500;
  private manualClose = false;

  private isRegistered = false;
  private heartbeatInterval: number | null = null;
  private readonly HEARTBEAT_INTERVAL = 30000;

  private listeners = new Set<MessageListener>();

  constructor(url = 'ws://localhost:8080/ws') {
    this.url = url;
  }

  connect(customUrl?: string): void {
    if (customUrl) this.url = customUrl;
    if (this.socket) return;

    this.manualClose = false;
    const store = useRobotStore();

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = () => {
        this.reconnectCount = 0;
        this.isRegistered = false;
        store.updateConnectionStatus(true, null);
        this.sendRaw({ type: 'register', role: 'web' });
        this.startHeartbeat();
      };

      this.socket.onmessage = (event) => {
        this.handleMessage(event.data);
      };

      this.socket.onerror = () => {
        store.updateConnectionStatus(false, 'WebSocket connection error');
      };

      this.socket.onclose = (event) => {
        store.updateConnectionStatus(false, `Disconnected (${event.code}: ${event.reason})`);
        this.socket = null;
        this.isRegistered = false;
        if (this.heartbeatInterval) {
          clearInterval(this.heartbeatInterval);
          this.heartbeatInterval = null;
        }
        if (!this.manualClose) {
          this.attemptReconnect();
        }
      };
    } catch {
      store.updateConnectionStatus(false, 'WebSocket initialization failed');
    }
  }

  disconnect(): void {
    this.manualClose = true;
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
    this.isRegistered = false;
    useRobotStore().updateConnectionStatus(false, 'Disconnected manually');
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  addMessageListener(listener: MessageListener): void {
    this.listeners.add(listener);
  }

  removeMessageListener(listener: MessageListener): void {
    this.listeners.delete(listener);
  }

  sendCommand(command: RobotCommand): void {
    if (!this.isConnected() || !this.isRegistered) return;
    this.sendRaw({
      type: 'command',
      payload: { command },
    });
  }

  sendWebRTCSignaling(data: WebRTCSignalPayload): void {
    if (!this.isConnected() || !this.isRegistered) return;
    this.sendRaw({
      type: 'webrtc_signaling',
      data,
    });
  }

  private sendRaw(message: WebSocketMessage): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;
    this.socket.send(JSON.stringify(message));
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.isConnected()) {
        this.sendRaw({ type: 'heartbeat' });
      }
    }, this.HEARTBEAT_INTERVAL);
  }

  private handleMessage(raw: string): void {
    const store = useRobotStore();
    let data: WebSocketMessage;
    try {
      data = JSON.parse(raw);
    } catch {
      return;
    }

    if (data.type === 'register_success') {
      this.isRegistered = true;
    } else if (data.type === 'status' && data.payload) {
      store.updateRobotStatus(data.payload);
    } else if (data.type === 'error') {
      store.updateConnectionStatus(false, data.message || 'Backend error');
    }

    this.listeners.forEach((listener) => {
      try {
        listener(data);
      } catch {
        // Listener failures must not break socket processing.
      }
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectCount >= this.maxReconnect) return;
    this.reconnectCount++;
    setTimeout(() => this.connect(), this.reconnectDelay);
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
