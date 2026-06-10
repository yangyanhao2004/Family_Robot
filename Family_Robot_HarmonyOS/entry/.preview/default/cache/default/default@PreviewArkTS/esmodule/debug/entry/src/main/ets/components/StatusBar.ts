if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface SpeedButton_Params {
    label?: string;
    active?: boolean;
    activeColor?: string;
    isEnabled?: boolean;
    onButtonClick?: () => void;
}
interface StatusBar_Params {
    connectionStatus?: string;
    robotStatus?: RobotStatus;
    speedLevel?: string;
    onSpeedChange?: (command: RobotCommand) => void;
}
import type { RobotStatus, RobotCommand } from '../model/Types';
export class StatusBar extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__connectionStatus = new SynchedPropertySimpleOneWayPU(params.connectionStatus, this, "connectionStatus");
        this.__robotStatus = new SynchedPropertyObjectOneWayPU(params.robotStatus, this, "robotStatus");
        this.__speedLevel = new SynchedPropertySimpleOneWayPU(params.speedLevel, this, "speedLevel");
        this.onSpeedChange = undefined;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: StatusBar_Params) {
        if (params.connectionStatus === undefined) {
            this.__connectionStatus.set('disconnected');
        }
        if (params.robotStatus === undefined) {
            this.__robotStatus.set({
                battery: null,
                isRunning: false,
                temperature: null,
                signalStrength: null
            });
        }
        if (params.speedLevel === undefined) {
            this.__speedLevel.set('medium');
        }
        if (params.onSpeedChange !== undefined) {
            this.onSpeedChange = params.onSpeedChange;
        }
    }
    updateStateVars(params: StatusBar_Params) {
        this.__connectionStatus.reset(params.connectionStatus);
        this.__robotStatus.reset(params.robotStatus);
        this.__speedLevel.reset(params.speedLevel);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__connectionStatus.purgeDependencyOnElmtId(rmElmtId);
        this.__robotStatus.purgeDependencyOnElmtId(rmElmtId);
        this.__speedLevel.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__connectionStatus.aboutToBeDeleted();
        this.__robotStatus.aboutToBeDeleted();
        this.__speedLevel.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __connectionStatus: SynchedPropertySimpleOneWayPU<string>;
    get connectionStatus() {
        return this.__connectionStatus.get();
    }
    set connectionStatus(newValue: string) {
        this.__connectionStatus.set(newValue);
    }
    private __robotStatus: SynchedPropertySimpleOneWayPU<RobotStatus>;
    get robotStatus() {
        return this.__robotStatus.get();
    }
    set robotStatus(newValue: RobotStatus) {
        this.__robotStatus.set(newValue);
    }
    private __speedLevel: SynchedPropertySimpleOneWayPU<string>;
    get speedLevel() {
        return this.__speedLevel.get();
    }
    set speedLevel(newValue: string) {
        this.__speedLevel.set(newValue);
    }
    private onSpeedChange?: (command: RobotCommand) => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/components/StatusBar.ets(20:5)", "entry");
            Row.width('100%');
            Row.height(50);
            Row.padding({ left: 12, right: 12 });
            Row.backgroundColor(this.connectionStatus === 'connected' ? '#1a1a2e' : '#2d2d2d');
            Row.alignItems(VerticalAlign.Center);
        }, Row);
        // 连接状态指示
        this.ConnectionPill.bind(this)();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/components/StatusBar.ets(24:7)", "entry");
        }, Blank);
        Blank.pop();
        // 速度选择器
        this.SpeedButtons.bind(this)();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/components/StatusBar.ets(29:7)", "entry");
        }, Blank);
        Blank.pop();
        // 信号强度
        this.SignalDisplay.bind(this)();
        // 电量
        this.BatteryDisplay.bind(this)();
        Row.pop();
    }
    ConnectionPill(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/components/StatusBar.ets(46:5)", "entry");
            Row.padding({ left: 10, right: 10, top: 4, bottom: 4 });
            Row.borderRadius(12);
            Row.backgroundColor(this.connectionStatus === 'connected' ? '#0f3460' : '#3a3a3a');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Circle.create({ width: 8, height: 8 });
            Circle.debugLine("entry/src/main/ets/components/StatusBar.ets(47:7)", "entry");
            Circle.fill(this.getStatusColor());
            Circle.margin({ right: 6 });
        }, Circle);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.getStatusText());
            Text.debugLine("entry/src/main/ets/components/StatusBar.ets(50:7)", "entry");
            Text.fontSize(13);
            Text.fontColor('#e0e0e0');
        }, Text);
        Text.pop();
        Row.pop();
    }
    SpeedButtons(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create({ space: 4 });
            Row.debugLine("entry/src/main/ets/components/StatusBar.ets(61:5)", "entry");
        }, Row);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new SpeedButton(this, {
                        label: '低',
                        active: this.speedLevel === 'low',
                        activeColor: '#10b981',
                        isEnabled: this.connectionStatus === 'connected',
                        onButtonClick: () => {
                            if (this.onSpeedChange) {
                                this.onSpeedChange('speed_low');
                            }
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/StatusBar.ets", line: 62, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            label: '低',
                            active: this.speedLevel === 'low',
                            activeColor: '#10b981',
                            isEnabled: this.connectionStatus === 'connected',
                            onButtonClick: () => {
                                if (this.onSpeedChange) {
                                    this.onSpeedChange('speed_low');
                                }
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        label: '低',
                        active: this.speedLevel === 'low',
                        activeColor: '#10b981',
                        isEnabled: this.connectionStatus === 'connected'
                    });
                }
            }, { name: "SpeedButton" });
        }
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new SpeedButton(this, {
                        label: '中',
                        active: this.speedLevel === 'medium',
                        activeColor: '#f59e0b',
                        isEnabled: this.connectionStatus === 'connected',
                        onButtonClick: () => {
                            if (this.onSpeedChange) {
                                this.onSpeedChange('speed_medium');
                            }
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/StatusBar.ets", line: 73, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            label: '中',
                            active: this.speedLevel === 'medium',
                            activeColor: '#f59e0b',
                            isEnabled: this.connectionStatus === 'connected',
                            onButtonClick: () => {
                                if (this.onSpeedChange) {
                                    this.onSpeedChange('speed_medium');
                                }
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        label: '中',
                        active: this.speedLevel === 'medium',
                        activeColor: '#f59e0b',
                        isEnabled: this.connectionStatus === 'connected'
                    });
                }
            }, { name: "SpeedButton" });
        }
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new SpeedButton(this, {
                        label: '高',
                        active: this.speedLevel === 'high',
                        activeColor: '#ef4444',
                        isEnabled: this.connectionStatus === 'connected',
                        onButtonClick: () => {
                            if (this.onSpeedChange) {
                                this.onSpeedChange('speed_high');
                            }
                        }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/StatusBar.ets", line: 84, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            label: '高',
                            active: this.speedLevel === 'high',
                            activeColor: '#ef4444',
                            isEnabled: this.connectionStatus === 'connected',
                            onButtonClick: () => {
                                if (this.onSpeedChange) {
                                    this.onSpeedChange('speed_high');
                                }
                            }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        label: '高',
                        active: this.speedLevel === 'high',
                        activeColor: '#ef4444',
                        isEnabled: this.connectionStatus === 'connected'
                    });
                }
            }, { name: "SpeedButton" });
        }
        Row.pop();
    }
    SignalDisplay(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/components/StatusBar.ets(100:5)", "entry");
            Row.margin({ right: 12 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.robotStatus.signalStrength !== null
                ? this.robotStatus.signalStrength!.toString() + '%'
                : '--');
            Text.debugLine("entry/src/main/ets/components/StatusBar.ets(101:7)", "entry");
            Text.fontSize(11);
            Text.fontColor('#a0a0a0');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(' 📶');
            Text.debugLine("entry/src/main/ets/components/StatusBar.ets(106:7)", "entry");
            Text.fontSize(12);
        }, Text);
        Text.pop();
        Row.pop();
    }
    BatteryDisplay(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/components/StatusBar.ets(114:5)", "entry");
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.robotStatus.battery !== null
                ? this.robotStatus.battery!.toString() + '%'
                : '--');
            Text.debugLine("entry/src/main/ets/components/StatusBar.ets(115:7)", "entry");
            Text.fontSize(11);
            Text.fontColor('#a0a0a0');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(' 🔋');
            Text.debugLine("entry/src/main/ets/components/StatusBar.ets(120:7)", "entry");
            Text.fontSize(12);
        }, Text);
        Text.pop();
        Row.pop();
    }
    private getStatusColor(): string {
        if (this.connectionStatus === 'connected')
            return '#10b981';
        if (this.connectionStatus === 'connecting')
            return '#3b82f6';
        return '#6b7280';
    }
    private getStatusText(): string {
        if (this.connectionStatus === 'connected')
            return '已连接';
        if (this.connectionStatus === 'connecting')
            return '连接中…';
        return '未连接';
    }
    rerender() {
        this.updateDirtyElements();
    }
}
class SpeedButton extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__label = new SynchedPropertySimpleOneWayPU(params.label, this, "label");
        this.__active = new SynchedPropertySimpleOneWayPU(params.active, this, "active");
        this.__activeColor = new SynchedPropertySimpleOneWayPU(params.activeColor, this, "activeColor");
        this.__isEnabled = new SynchedPropertySimpleOneWayPU(params.isEnabled, this, "isEnabled");
        this.onButtonClick = undefined;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: SpeedButton_Params) {
        if (params.label === undefined) {
            this.__label.set('');
        }
        if (params.active === undefined) {
            this.__active.set(false);
        }
        if (params.activeColor === undefined) {
            this.__activeColor.set('#10b981');
        }
        if (params.isEnabled === undefined) {
            this.__isEnabled.set(true);
        }
        if (params.onButtonClick !== undefined) {
            this.onButtonClick = params.onButtonClick;
        }
    }
    updateStateVars(params: SpeedButton_Params) {
        this.__label.reset(params.label);
        this.__active.reset(params.active);
        this.__activeColor.reset(params.activeColor);
        this.__isEnabled.reset(params.isEnabled);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__label.purgeDependencyOnElmtId(rmElmtId);
        this.__active.purgeDependencyOnElmtId(rmElmtId);
        this.__activeColor.purgeDependencyOnElmtId(rmElmtId);
        this.__isEnabled.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__label.aboutToBeDeleted();
        this.__active.aboutToBeDeleted();
        this.__activeColor.aboutToBeDeleted();
        this.__isEnabled.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __label: SynchedPropertySimpleOneWayPU<string>;
    get label() {
        return this.__label.get();
    }
    set label(newValue: string) {
        this.__label.set(newValue);
    }
    private __active: SynchedPropertySimpleOneWayPU<boolean>;
    get active() {
        return this.__active.get();
    }
    set active(newValue: boolean) {
        this.__active.set(newValue);
    }
    private __activeColor: SynchedPropertySimpleOneWayPU<string>;
    get activeColor() {
        return this.__activeColor.get();
    }
    set activeColor(newValue: string) {
        this.__activeColor.set(newValue);
    }
    private __isEnabled: SynchedPropertySimpleOneWayPU<boolean>;
    get isEnabled() {
        return this.__isEnabled.get();
    }
    set isEnabled(newValue: boolean) {
        this.__isEnabled.set(newValue);
    }
    private onButtonClick?: () => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.label);
            Button.debugLine("entry/src/main/ets/components/StatusBar.ets(150:5)", "entry");
            Button.fontSize(11);
            Button.fontColor(this.active ? '#ffffff' : '#a0a0a0');
            Button.height(26);
            Button.width(32);
            Button.padding(0);
            Button.backgroundColor(this.active ? this.activeColor : 'transparent');
            Button.borderRadius(6);
            Button.border({ width: 1, color: this.active ? this.activeColor : '#4a4a4a' });
            Button.enabled(this.isEnabled);
            Button.onClick(() => {
                if (this.onButtonClick) {
                    this.onButtonClick();
                }
            });
        }, Button);
        Button.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
