if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface DashboardPage_Params {
    connectionStatus?: string;
    connectionError?: string;
    autoConnect?: boolean;
    robotStatus?: RobotStatus;
    speedLevel?: string;
    videoUrl?: string;
    photoFilename?: string;
    wsMsgListener?: (msg: WebSocketMessage) => void;
}
import router from "@ohos:router";
import { webSocketService } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/WebSocketService";
import type { ConnectionCallback } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/WebSocketService";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import { StatusBar } from "@bundle:com.familyrobot.harmonyos/entry/ets/components/StatusBar";
import { VideoStream } from "@bundle:com.familyrobot.harmonyos/entry/ets/components/VideoStream";
import { DPadControl } from "@bundle:com.familyrobot.harmonyos/entry/ets/components/DPadControl";
import { PTZControl } from "@bundle:com.familyrobot.harmonyos/entry/ets/components/PTZControl";
import type { RobotCommand, RobotStatus, WebSocketMessage } from '../model/Types';
import { getVideoStreamUrl } from "@bundle:com.familyrobot.harmonyos/entry/ets/common/Constants";
class DashboardPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__connectionStatus = new ObservedPropertySimplePU('disconnected', this, "connectionStatus");
        this.__connectionError = new ObservedPropertySimplePU('', this, "connectionError");
        this.__autoConnect = new ObservedPropertySimplePU(true
        // 机器人状态
        , this, "autoConnect");
        this.__robotStatus = new ObservedPropertyObjectPU({
            battery: null,
            isRunning: false,
            temperature: null,
            signalStrength: null
        }
        // 速度
        , this, "robotStatus");
        this.__speedLevel = new ObservedPropertySimplePU('medium'
        // 视频
        , this, "speedLevel");
        this.__videoUrl = new ObservedPropertySimplePU(getVideoStreamUrl()
        // 照片捕获状态
        , this, "videoUrl");
        this.__photoFilename = new ObservedPropertySimplePU('', this, "photoFilename");
        this.wsMsgListener = (_msg: WebSocketMessage) => { };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: DashboardPage_Params) {
        if (params.connectionStatus !== undefined) {
            this.connectionStatus = params.connectionStatus;
        }
        if (params.connectionError !== undefined) {
            this.connectionError = params.connectionError;
        }
        if (params.autoConnect !== undefined) {
            this.autoConnect = params.autoConnect;
        }
        if (params.robotStatus !== undefined) {
            this.robotStatus = params.robotStatus;
        }
        if (params.speedLevel !== undefined) {
            this.speedLevel = params.speedLevel;
        }
        if (params.videoUrl !== undefined) {
            this.videoUrl = params.videoUrl;
        }
        if (params.photoFilename !== undefined) {
            this.photoFilename = params.photoFilename;
        }
        if (params.wsMsgListener !== undefined) {
            this.wsMsgListener = params.wsMsgListener;
        }
    }
    updateStateVars(params: DashboardPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__connectionStatus.purgeDependencyOnElmtId(rmElmtId);
        this.__connectionError.purgeDependencyOnElmtId(rmElmtId);
        this.__autoConnect.purgeDependencyOnElmtId(rmElmtId);
        this.__robotStatus.purgeDependencyOnElmtId(rmElmtId);
        this.__speedLevel.purgeDependencyOnElmtId(rmElmtId);
        this.__videoUrl.purgeDependencyOnElmtId(rmElmtId);
        this.__photoFilename.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__connectionStatus.aboutToBeDeleted();
        this.__connectionError.aboutToBeDeleted();
        this.__autoConnect.aboutToBeDeleted();
        this.__robotStatus.aboutToBeDeleted();
        this.__speedLevel.aboutToBeDeleted();
        this.__videoUrl.aboutToBeDeleted();
        this.__photoFilename.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    // 连接状态
    private __connectionStatus: ObservedPropertySimplePU<string>;
    get connectionStatus() {
        return this.__connectionStatus.get();
    }
    set connectionStatus(newValue: string) {
        this.__connectionStatus.set(newValue);
    }
    private __connectionError: ObservedPropertySimplePU<string>;
    get connectionError() {
        return this.__connectionError.get();
    }
    set connectionError(newValue: string) {
        this.__connectionError.set(newValue);
    }
    private __autoConnect: ObservedPropertySimplePU<boolean>;
    get autoConnect() {
        return this.__autoConnect.get();
    }
    set autoConnect(newValue: boolean) {
        this.__autoConnect.set(newValue);
    }
    // 机器人状态
    private __robotStatus: ObservedPropertyObjectPU<RobotStatus>;
    get robotStatus() {
        return this.__robotStatus.get();
    }
    set robotStatus(newValue: RobotStatus) {
        this.__robotStatus.set(newValue);
    }
    // 速度
    private __speedLevel: ObservedPropertySimplePU<string>;
    get speedLevel() {
        return this.__speedLevel.get();
    }
    set speedLevel(newValue: string) {
        this.__speedLevel.set(newValue);
    }
    // 视频
    private __videoUrl: ObservedPropertySimplePU<string>;
    get videoUrl() {
        return this.__videoUrl.get();
    }
    set videoUrl(newValue: string) {
        this.__videoUrl.set(newValue);
    }
    // 照片捕获状态
    private __photoFilename: ObservedPropertySimplePU<string>;
    get photoFilename() {
        return this.__photoFilename.get();
    }
    set photoFilename(newValue: string) {
        this.__photoFilename.set(newValue);
    }
    private wsMsgListener: (msg: WebSocketMessage) => void;
    aboutToAppear(): void {
        // 注册回调
        let cb: ConnectionCallback = {
            onStatusChanged: (status: string, error?: string) => {
                this.connectionStatus = status;
                if (error)
                    this.connectionError = error;
            },
            onRobotStatusUpdated: (status: RobotStatus) => {
                this.robotStatus = status;
            },
            onError: (message: string) => {
                // 错误通知
            }
        };
        webSocketService.setCallback(cb);
        // 监听 photo_captured 消息
        this.wsMsgListener = (msg: WebSocketMessage) => {
            if (msg.type === 'photo_captured' && msg.payload) {
                let payload: Record<string, Object> = msg.payload;
                let filename: string = (payload['filename'] as string) || '';
                let url: string = (payload['url'] as string) || '';
                this.onPhotoCaptured(url, filename);
            }
        };
        webSocketService.addMessageListener(this.wsMsgListener);
        // 自动连接
        if (this.autoConnect) {
            webSocketService.connect();
        }
    }
    aboutToDisappear(): void {
        webSocketService.removeMessageListener(this.wsMsgListener);
        webSocketService.disconnect();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/DashboardPage.ets(82:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 顶部状态栏
                    StatusBar(this, {
                        connectionStatus: this.connectionStatus,
                        robotStatus: this.robotStatus,
                        speedLevel: this.speedLevel,
                        onSpeedChange: (cmd: RobotCommand) => {
                            this.speedLevel = cmd === 'speed_low' ? 'low'
                                : cmd === 'speed_medium' ? 'medium' : 'high';
                            webSocketService.sendCommand(cmd);
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/DashboardPage.ets", line: 84, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            connectionStatus: this.connectionStatus,
                            robotStatus: this.robotStatus,
                            speedLevel: this.speedLevel,
                            onSpeedChange: (cmd: RobotCommand) => {
                                this.speedLevel = cmd === 'speed_low' ? 'low'
                                    : cmd === 'speed_medium' ? 'medium' : 'high';
                                webSocketService.sendCommand(cmd);
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        connectionStatus: this.connectionStatus,
                        robotStatus: this.robotStatus,
                        speedLevel: this.speedLevel
                    });
                }
            }, { name: "StatusBar" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 主区域
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/DashboardPage.ets(96:7)", "entry");
            // 主区域
            Row.layoutWeight(1);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 左侧: 视频区域 + 拍照按钮
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/DashboardPage.ets(98:9)", "entry");
            // 左侧: 视频区域 + 拍照按钮
            Column.layoutWeight(1);
            // 左侧: 视频区域 + 拍照按钮
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Stack.create();
            Stack.debugLine("entry/src/main/ets/pages/DashboardPage.ets(99:11)", "entry");
            Stack.layoutWeight(1);
        }, Stack);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            __Common__.create();
            __Common__.width('100%');
            __Common__.height('100%');
        }, __Common__);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 视频
                    VideoStream(this, { streamUrl: this.videoUrl }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/DashboardPage.ets", line: 101, col: 13 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            streamUrl: this.videoUrl
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        streamUrl: this.videoUrl
                    });
                }
            }, { name: "VideoStream" });
        }
        __Common__.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 拍照按钮 (悬浮)
            Button.createWithChild();
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(106:13)", "entry");
            // 拍照按钮 (悬浮)
            Button.width(48);
            // 拍照按钮 (悬浮)
            Button.height(48);
            // 拍照按钮 (悬浮)
            Button.backgroundColor('#0f3460');
            // 拍照按钮 (悬浮)
            Button.borderRadius(24);
            // 拍照按钮 (悬浮)
            Button.position({ right: 16, bottom: 16 });
            // 拍照按钮 (悬浮)
            Button.onClick(() => { this.takePhoto(); });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('📷');
            Text.debugLine("entry/src/main/ets/pages/DashboardPage.ets(107:15)", "entry");
            Text.fontSize(20);
        }, Text);
        Text.pop();
        // 拍照按钮 (悬浮)
        Button.pop();
        Stack.pop();
        // 左侧: 视频区域 + 拍照按钮
        Column.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 右侧: 控制面板
            Column.create({ space: 16 });
            Column.debugLine("entry/src/main/ets/pages/DashboardPage.ets(121:9)", "entry");
            // 右侧: 控制面板
            Column.width(320);
            // 右侧: 控制面板
            Column.padding(12);
            // 右侧: 控制面板
            Column.backgroundColor('#12122a');
        }, Column);
        // 连接按钮
        this.BuildConnectionButton.bind(this)();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 运动方向键
                    DPadControl(this, {
                        disabled: this.connectionStatus !== 'connected',
                        onCommand: (cmd: RobotCommand, angle?: number) => {
                            webSocketService.sendCommand(cmd, angle);
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/DashboardPage.ets", line: 126, col: 11 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            disabled: this.connectionStatus !== 'connected',
                            onCommand: (cmd: RobotCommand, angle?: number) => {
                                webSocketService.sendCommand(cmd, angle);
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        disabled: this.connectionStatus !== 'connected'
                    });
                }
            }, { name: "DPadControl" });
        }
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 云台控制
                    PTZControl(this, {
                        disabled: this.connectionStatus !== 'connected',
                        onCommand: (cmd: RobotCommand, angle: number) => {
                            webSocketService.sendCommand(cmd, angle);
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/DashboardPage.ets", line: 134, col: 11 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            disabled: this.connectionStatus !== 'connected',
                            onCommand: (cmd: RobotCommand, angle: number) => {
                                webSocketService.sendCommand(cmd, angle);
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        disabled: this.connectionStatus !== 'connected'
                    });
                }
            }, { name: "PTZControl" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // AI 对话 + 相册 入口
            Row.create({ space: 10 });
            Row.debugLine("entry/src/main/ets/pages/DashboardPage.ets(142:11)", "entry");
            // AI 对话 + 相册 入口
            Row.width('100%');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('💬 AI对话');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(143:13)", "entry");
            Button.fontSize(13);
            Button.fontColor('#ffffff');
            Button.layoutWeight(1);
            Button.height(40);
            Button.backgroundColor('#0f3460');
            Button.borderRadius(8);
            Button.onClick(() => {
                router.pushUrl({ url: 'pages/AIChatPage' });
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('🖼 相册');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(150:13)", "entry");
            Button.fontSize(13);
            Button.fontColor('#ffffff');
            Button.layoutWeight(1);
            Button.height(40);
            Button.backgroundColor('#0f3460');
            Button.borderRadius(8);
            Button.onClick(() => {
                router.pushUrl({ url: 'pages/AlbumPage' });
            });
        }, Button);
        Button.pop();
        // AI 对话 + 相册 入口
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 提醒 + 设置 + 个人中心
            Row.create({ space: 10 });
            Row.debugLine("entry/src/main/ets/pages/DashboardPage.ets(161:11)", "entry");
            // 提醒 + 设置 + 个人中心
            Row.width('100%');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('⏰');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(162:13)", "entry");
            Button.fontSize(16);
            Button.layoutWeight(1);
            Button.height(36);
            Button.backgroundColor('#1a1a2e');
            Button.borderRadius(8);
            Button.onClick(() => router.pushUrl({ url: 'pages/ReminderPage' }));
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('⚙️');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(167:13)", "entry");
            Button.fontSize(16);
            Button.layoutWeight(1);
            Button.height(36);
            Button.backgroundColor('#1a1a2e');
            Button.borderRadius(8);
            Button.onClick(() => router.pushUrl({ url: 'pages/SettingsPage' }));
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('👤');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(172:13)", "entry");
            Button.fontSize(16);
            Button.layoutWeight(1);
            Button.height(36);
            Button.backgroundColor('#1a1a2e');
            Button.borderRadius(8);
            Button.onClick(() => router.pushUrl({ url: 'pages/ProfilePage' }));
        }, Button);
        Button.pop();
        // 提醒 + 设置 + 个人中心
        Row.pop();
        // 右侧: 控制面板
        Column.pop();
        // 主区域
        Row.pop();
        Column.pop();
    }
    BuildConnectionButton(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/DashboardPage.ets(193:5)", "entry");
            Row.width('100%');
            Row.height(40);
            Row.padding({ left: 10, right: 10 });
            Row.borderRadius(8);
            Row.backgroundColor('#1a1a2e');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Circle.create({ width: 8, height: 8 });
            Circle.debugLine("entry/src/main/ets/pages/DashboardPage.ets(194:7)", "entry");
            Circle.fill(this.connectionStatus === 'connected' ? '#10b981'
                : this.connectionStatus === 'connecting' ? '#3b82f6' : '#6b7280');
            Circle.margin({ right: 6 });
        }, Circle);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.connectionStatus === 'connected' ? '已连接'
                : this.connectionStatus === 'connecting' ? '连接中...' : '未连接');
            Text.debugLine("entry/src/main/ets/pages/DashboardPage.ets(199:7)", "entry");
            Text.fontSize(13);
            Text.fontColor('#c0c0c0');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/DashboardPage.ets(204:7)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.connectionStatus === 'connected' ? '断开' : '连接');
            Button.debugLine("entry/src/main/ets/pages/DashboardPage.ets(206:7)", "entry");
            Button.fontSize(12);
            Button.height(30);
            Button.padding({ left: 12, right: 12 });
            Button.fontColor('#ffffff');
            Button.backgroundColor(this.connectionStatus === 'connected' ? '#7f1d1d' : '#0f3460');
            Button.borderRadius(6);
            Button.enabled(this.connectionStatus !== 'connecting');
            Button.onClick(() => {
                if (this.connectionStatus === 'connected') {
                    webSocketService.disconnect();
                }
                else {
                    webSocketService.connect();
                }
            });
        }, Button);
        Button.pop();
        Row.pop();
    }
    private takePhoto(): void {
        if (!webSocketService.isConnected())
            return;
        webSocketService.sendCommand('take_photo');
    }
    private async onPhotoCaptured(url: string, filename: string): Promise<void> {
        try {
            await api.addPhoto(url, filename);
        }
        catch (_err) {
            // 保存到相册失败不阻塞
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "DashboardPage";
    }
}
registerNamedRoute(() => new DashboardPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/DashboardPage", pageFullPath: "entry/src/main/ets/pages/DashboardPage", integratedHsp: "false", moduleType: "followWithHap" });
