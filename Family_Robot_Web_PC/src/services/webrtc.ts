import webSocketService, { WebRTCSignalPayload, WebSocketMessage } from './websocket';

export type CallState = 'idle' | 'connecting' | 'connected' | 'failed';

class WebRTCService {
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private remoteAudio: HTMLAudioElement | null = null;
  private isMicEnabled = true;
  private isSignalingBound = false;
  private stateListener: ((state: CallState) => void) | null = null;
  private selectedMicId: string | undefined = undefined;

  private readonly iceServers: RTCIceServer[] = [
    { urls: ['stun:stun.l.google.com:19302'] },
  ];

  private readonly signalingListener = (message: WebSocketMessage) => {
    if (message.type !== 'webrtc_signaling' || !message.data) return;
    this.handleSignalingMessage(message.data as WebRTCSignalPayload);
  };

  async enumerateMics(): Promise<MediaDeviceInfo[]> {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const mics = devices.filter((d) => d.kind === 'audioinput');

    // Deduplicate: group by label substring match, prefer comm variant
    const result: MediaDeviceInfo[] = [];
    const seen = new Set<string>();
    for (const mic of mics) {
      // Extract device name: strip prefixes like "Default - " "Communications - "
      const name = mic.label.replace(/^(默认\s*-\s*|Default\s*-\s*|通讯\s*-\s*|Communications\s*-\s*)/i, '').trim();
      if (seen.has(name)) {
        // Already seen — if this is the comm variant, replace the existing
        const isComm = /通讯|comm/i.test(mic.label);
        if (isComm) {
          const idx = result.findIndex((m) =>
            m.label.replace(/^(默认\s*-\s*|Default\s*-\s*|通讯\s*-\s*|Communications\s*-\s*)/i, '').trim() === name
          );
          if (idx >= 0) result[idx] = mic;
        }
        continue;
      }
      seen.add(name);
      result.push(mic);
    }
    return result;
  }

  setMicrophone(deviceId: string): void {
    this.selectedMicId = deviceId;
    if (this.localStream) {
      // Stop existing tracks so next getUserMedia uses new device
      this.localStream.getTracks().forEach((t) => t.stop());
      this.localStream = null;
    }
  }

  async preAcquireMic(): Promise<void> {
    if (this.localStream) return;
    try {
      const constraints: MediaStreamConstraints = {
        audio: this.selectedMicId
          ? { deviceId: { exact: this.selectedMicId }, echoCancellation: false, noiseSuppression: false }
          : { echoCancellation: false, noiseSuppression: false },
        video: false,
      };
      this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch {
      // Mic not available or permission denied; will retry on call
    }
  }

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
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    if (this.remoteAudio) {
      this.remoteAudio.srcObject = null;
      this.remoteAudio.remove();
      this.remoteAudio = null;
    }
    this.remoteStream = null;
    this.isMicEnabled = true;

    if (this.isSignalingBound) {
      webSocketService.removeMessageListener(this.signalingListener);
      this.isSignalingBound = false;
    }

    this.notifyState('idle');
  }

  onCallStateChange(listener: ((state: CallState) => void) | null): void {
    this.stateListener = listener;
  }

  private async ensurePeerConnection(): Promise<void> {
    if (!this.isSignalingBound) {
      webSocketService.addMessageListener(this.signalingListener);
      this.isSignalingBound = true;
    }

    if (this.peerConnection) return;

    this.peerConnection = new RTCPeerConnection({ iceServers: this.iceServers });
    this.setupEventHandlers();

    if (!this.localStream) {
      const constraints: MediaStreamConstraints = {
        audio: this.selectedMicId
          ? { deviceId: { exact: this.selectedMicId }, echoCancellation: false, noiseSuppression: false }
          : { echoCancellation: false, noiseSuppression: false },
        video: false,
      };
      this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
    }
    this.localStream.getAudioTracks().forEach((track) => {
      track.enabled = this.isMicEnabled;
      this.peerConnection?.addTrack(track, this.localStream!);
    });
  }

  private notifyState(state: CallState): void {
    if (this.stateListener) {
      this.stateListener(state);
    }
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

    this.peerConnection.onconnectionstatechange = () => {
      const state = this.peerConnection?.connectionState;
      if (state === 'connected') {
        this.notifyState('connected');
      } else if (state === 'failed' || state === 'closed' || state === 'disconnected') {
        this.notifyState(state === 'failed' ? 'failed' : 'idle');
      } else if (state === 'connecting') {
        this.notifyState('connecting');
      }
    };

    this.peerConnection.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        this.remoteStream = event.streams[0];
        const audio = new Audio();
        audio.srcObject = event.streams[0];
        audio.autoplay = true;
        audio.play().catch((e) => console.warn('[WebRTC] remote audio play failed:', e));
        this.remoteAudio = audio;
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
