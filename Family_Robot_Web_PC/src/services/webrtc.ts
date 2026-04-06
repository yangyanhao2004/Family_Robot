import webSocketService, { WebRTCSignalPayload, WebSocketMessage } from './websocket';

class WebRTCService {
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private isMicEnabled = true;
  private isSignalingBound = false;

  private readonly iceServers: RTCIceServer[] = [
    { urls: ['stun:stun.l.google.com:19302'] },
  ];

  private readonly signalingListener = (message: WebSocketMessage) => {
    if (message.type !== 'webrtc_signaling' || !message.data) return;
    this.handleSignalingMessage(message.data as WebRTCSignalPayload);
  };

  async startCall(): Promise<void> {
    if (!webSocketService.isConnected()) {
      throw new Error('WebSocket is not connected');
    }

    await this.ensurePeerConnection();

    if (this.peerConnection) {
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);
      this.sendSignalingMessage({
        type: 'offer',
        offer: offer,
      });
    }
  }

  close(): void {
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    this.remoteStream = null;
    this.isMicEnabled = true;

    if (this.isSignalingBound) {
      webSocketService.removeMessageListener(this.signalingListener);
      this.isSignalingBound = false;
    }
  }

  getRemoteStream(): MediaStream | null {
    return this.remoteStream;
  }

  getMicStatus(): boolean {
    return this.isMicEnabled;
  }

  getConnectionState(): string {
    return this.peerConnection?.connectionState || 'disconnected';
  }

  toggleMicrophone(): boolean {
    if (!this.localStream) return this.isMicEnabled;
    this.isMicEnabled = !this.isMicEnabled;
    this.localStream.getAudioTracks().forEach((track) => {
      track.enabled = this.isMicEnabled;
    });
    return this.isMicEnabled;
  }

  private async ensurePeerConnection(): Promise<void> {
    if (!this.isSignalingBound) {
      webSocketService.addMessageListener(this.signalingListener);
      this.isSignalingBound = true;
    }

    if (this.peerConnection) return;

    this.peerConnection = new RTCPeerConnection({ iceServers: this.iceServers });
    this.setupEventHandlers();

    this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    this.localStream.getAudioTracks().forEach((track) => {
      this.peerConnection?.addTrack(track, this.localStream!);
    });
  }

  private setupEventHandlers(): void {
    if (!this.peerConnection) return;

    this.peerConnection.onicecandidate = (event) => {
      if (!event.candidate) return;
      this.sendSignalingMessage({
        type: 'candidate',
        candidate: event.candidate.toJSON(),
      });
    };

    this.peerConnection.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        this.remoteStream = event.streams[0];
      }
    };
  }

  private async handleSignalingMessage(message: WebRTCSignalPayload): Promise<void> {
    if (!message?.type) return;
    await this.ensurePeerConnection();
    if (!this.peerConnection) return;

    try {
      if (message.type === 'answer' && message.answer) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(message.answer));
        return;
      }

      if (message.type === 'offer' && message.offer) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(message.offer));
        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);
        this.sendSignalingMessage({
          type: 'answer',
          answer: answer,
        });
        return;
      }

      if (message.type === 'candidate' && message.candidate) {
        await this.peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
      }
    } catch (error) {
      console.error('[WebRTC] signaling handling failed:', error);
    }
  }

  private sendSignalingMessage(payload: WebRTCSignalPayload): void {
    webSocketService.sendWebRTCSignaling(payload);
  }
}

const webRTCService = new WebRTCService();
export default webRTCService;
