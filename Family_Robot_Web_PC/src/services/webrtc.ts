// services/webrtc.ts - WebRTC 连接管理模块
// 设计意图：实现与机器人的实时通信，支持单向视频和双向音频

import { useRobotStore } from '../store/robotStore';

class WebRTCService {
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private isMicEnabled: boolean = true;
  private iceServers: RTCIceServer[] = [
    {
      urls: ['stun:stun.l.google.com:19302']
    }
  ];

  // 延迟获取 robotStore 实例
  private get robotStore() {
    return useRobotStore();
  }

  /**
   * 初始化 WebRTC 连接
   */
  async init(): Promise<void> {
    try {
      // 创建 RTCPeerConnection
      this.peerConnection = new RTCPeerConnection({ iceServers: this.iceServers });

      // 配置事件处理
      this.setupEventHandlers();

      // 获取本地音频流
      await this.getLocalAudioStream();

      console.log('[WebRTC] 初始化成功');
    } catch (error) {
      console.error('[WebRTC] 初始化失败:', error);
      this.robotStore.updateConnectionStatus(false, 'WebRTC 初始化失败');
    }
  }

  /**
   * 设置事件处理器
   */
  private setupEventHandlers(): void {
    if (!this.peerConnection) return;

    // 当有 ICE 候选时发送给远端
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        this.sendSignalingMessage({
          type: 'candidate',
          candidate: event.candidate
        });
      }
    };

    // 当有远端流时处理
    this.peerConnection.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        this.remoteStream = event.streams[0];
        console.log('[WebRTC] 收到远端流');
      }
    };

    // 连接状态变化
    this.peerConnection.onconnectionstatechange = () => {
      if (this.peerConnection) {
        console.log('[WebRTC] 连接状态:', this.peerConnection.connectionState);
        this.updateCallStatus();
      }
    };
  }

  /**
   * 获取本地音频流
   */
  private async getLocalAudioStream(): Promise<void> {
    try {
      this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      
      // 将本地音频轨道添加到 PeerConnection
      if (this.localStream && this.peerConnection) {
        this.localStream.getAudioTracks().forEach(track => {
          this.peerConnection?.addTrack(track, this.localStream!);
        });
      }

      console.log('[WebRTC] 本地音频流获取成功');
    } catch (error) {
      console.error('[WebRTC] 获取本地音频流失败:', error);
      this.robotStore.updateConnectionStatus(false, '麦克风访问失败');
    }
  }

  /**
   * 创建并发送 Offer
   */
  async createOffer(): Promise<void> {
    try {
      if (!this.peerConnection) {
        await this.init();
      }

      if (this.peerConnection) {
        const offer = await this.peerConnection.createOffer();
        await this.peerConnection.setLocalDescription(offer);
        
        this.sendSignalingMessage({
          type: 'offer',
          offer: offer
        });

        console.log('[WebRTC] 发送 Offer 成功');
      }
    } catch (error) {
      console.error('[WebRTC] 创建 Offer 失败:', error);
      this.robotStore.updateConnectionStatus(false, '创建 Offer 失败');
    }
  }

  /**
   * 处理收到的 Offer
   */
  async handleOffer(offer: RTCSessionDescriptionInit): Promise<void> {
    try {
      if (!this.peerConnection) {
        await this.init();
      }

      if (this.peerConnection) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        
        const answer = await this.peerConnection.createAnswer();
        await this.peerConnection.setLocalDescription(answer);
        
        this.sendSignalingMessage({
          type: 'answer',
          answer: answer
        });

        console.log('[WebRTC] 处理 Offer 并发送 Answer 成功');
      }
    } catch (error) {
      console.error('[WebRTC] 处理 Offer 失败:', error);
      this.robotStore.updateConnectionStatus(false, '处理 Offer 失败');
    }
  }

  /**
   * 处理收到的 Answer
   */
  async handleAnswer(answer: RTCSessionDescriptionInit): Promise<void> {
    try {
      if (this.peerConnection) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
        console.log('[WebRTC] 处理 Answer 成功');
      }
    } catch (error) {
      console.error('[WebRTC] 处理 Answer 失败:', error);
      this.robotStore.updateConnectionStatus(false, '处理 Answer 失败');
    }
  }

  /**
   * 处理收到的 ICE Candidate
   */
  async handleCandidate(candidate: RTCIceCandidateInit): Promise<void> {
    try {
      if (this.peerConnection) {
        await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        console.log('[WebRTC] 添加 ICE Candidate 成功');
      }
    } catch (error) {
      console.error('[WebRTC] 添加 ICE Candidate 失败:', error);
    }
  }

  /**
   * 发送信令消息
   */
  private sendSignalingMessage(message: any): void {
    // 这里需要与后端协商具体的消息格式
    // 暂时通过控制台打印，实际项目中应该通过 WebSocket 发送
    console.log('[WebRTC] 发送信令消息:', message);
    // 注意：实际项目中应该通过 WebSocket 发送信令消息
    // 例如：webSocketService.send(JSON.stringify({ type: 'webrtc_signaling', data: message }));
  }

  /**
   * 切换麦克风状态
   */
  toggleMicrophone(): boolean {
    if (this.localStream) {
      this.isMicEnabled = !this.isMicEnabled;
      this.localStream.getAudioTracks().forEach(track => {
        track.enabled = this.isMicEnabled;
      });
      console.log('[WebRTC] 麦克风状态:', this.isMicEnabled ? '开启' : '关闭');
    }
    return this.isMicEnabled;
  }

  /**
   * 关闭 WebRTC 连接
   */
  close(): void {
    // 停止本地流
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }

    // 关闭 PeerConnection
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // 清理远端流
    this.remoteStream = null;
    this.isMicEnabled = true;

    console.log('[WebRTC] 连接已关闭');
  }

  /**
   * 获取远端视频流
   */
  getRemoteStream(): MediaStream | null {
    return this.remoteStream;
  }

  /**
   * 获取麦克风状态
   */
  getMicStatus(): boolean {
    return this.isMicEnabled;
  }

  /**
   * 获取连接状态
   */
  getConnectionState(): string {
    if (!this.peerConnection) return 'disconnected';
    return this.peerConnection.connectionState;
  }

  /**
   * 更新通话状态到 Pinia Store
   */
  private updateCallStatus(): void {
    const state = this.getConnectionState();
    const isConnected = state === 'connected';
    
    if (isConnected) {
      this.robotStore.updateConnectionStatus(true, '通话已连接');
    } else {
      this.robotStore.updateConnectionStatus(false, `通话状态: ${state}`);
    }
  }
}

// 导出单例实例
const webRTCService = new WebRTCService();
export default webRTCService;