if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface PTZButton_Params {
    symbol?: string;
    label?: string;
    disabled?: boolean;
    active?: boolean;
    onPress?: () => void;
    onRelease?: () => void;
}
interface PTZControl_Params {
    onCommand?: (command: RobotCommand, angle: number) => void;
    disabled?: boolean;
    servo1Angle?: number;
    servo2Angle?: number;
    activeServo?: string;
    commandTimer?: number | null;
}
import type { RobotCommand } from '../model/Types';
import { SERVO_STEP, COMMAND_INTERVAL } from "@bundle:com.familyrobot.harmonyos/entry/ets/common/Constants";
export class PTZControl extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.onCommand = undefined;
        this.__disabled = new SynchedPropertySimpleOneWayPU(params.disabled, this, "disabled");
        this.__servo1Angle = new ObservedPropertySimplePU(90 // 水平 0-180
        , this, "servo1Angle");
        this.__servo2Angle = new ObservedPropertySimplePU(90 // 垂直 0-180
        , this, "servo2Angle");
        this.__activeServo = new ObservedPropertySimplePU('', this, "activeServo");
        this.commandTimer = null;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: PTZControl_Params) {
        if (params.onCommand !== undefined) {
            this.onCommand = params.onCommand;
        }
        if (params.disabled === undefined) {
            this.__disabled.set(false);
        }
        if (params.servo1Angle !== undefined) {
            this.servo1Angle = params.servo1Angle;
        }
        if (params.servo2Angle !== undefined) {
            this.servo2Angle = params.servo2Angle;
        }
        if (params.activeServo !== undefined) {
            this.activeServo = params.activeServo;
        }
        if (params.commandTimer !== undefined) {
            this.commandTimer = params.commandTimer;
        }
    }
    updateStateVars(params: PTZControl_Params) {
        this.__disabled.reset(params.disabled);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__disabled.purgeDependencyOnElmtId(rmElmtId);
        this.__servo1Angle.purgeDependencyOnElmtId(rmElmtId);
        this.__servo2Angle.purgeDependencyOnElmtId(rmElmtId);
        this.__activeServo.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__disabled.aboutToBeDeleted();
        this.__servo1Angle.aboutToBeDeleted();
        this.__servo2Angle.aboutToBeDeleted();
        this.__activeServo.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private onCommand?: (command: RobotCommand, angle: number) => void;
    private __disabled: SynchedPropertySimpleOneWayPU<boolean>;
    get disabled() {
        return this.__disabled.get();
    }
    set disabled(newValue: boolean) {
        this.__disabled.set(newValue);
    }
    private __servo1Angle: ObservedPropertySimplePU<number>; // 水平 0-180
    get servo1Angle() {
        return this.__servo1Angle.get();
    }
    set servo1Angle(newValue: number) {
        this.__servo1Angle.set(newValue);
    }
    private __servo2Angle: ObservedPropertySimplePU<number>; // 垂直 0-180
    get servo2Angle() {
        return this.__servo2Angle.get();
    }
    set servo2Angle(newValue: number) {
        this.__servo2Angle.set(newValue);
    }
    private __activeServo: ObservedPropertySimplePU<string>;
    get activeServo() {
        return this.__activeServo.get();
    }
    set activeServo(newValue: string) {
        this.__activeServo.set(newValue);
    }
    private commandTimer: number | null;
    aboutToDisappear(): void {
        this.stopContinuous();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 8 });
            Column.debugLine("entry/src/main/ets/components/PTZControl.ets(23:5)", "entry");
            Column.padding(12);
            Column.borderRadius(12);
            Column.backgroundColor('#16213e');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('云台控制');
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(24:7)", "entry");
            Text.fontSize(14);
            Text.fontColor('#a0a0a0');
            Text.margin({ bottom: 4 });
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // Servo1 当前角度
            Text.create('水平: ' + this.servo1Angle.toFixed(0) + '°');
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(30:7)", "entry");
            // Servo1 当前角度
            Text.fontSize(12);
            // Servo1 当前角度
            Text.fontColor('#808080');
        }, Text);
        // Servo1 当前角度
        Text.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // Servo2 上下
                    PTZButton(this, {
                        symbol: '▲',
                        label: 'S2+',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo2_up',
                        onPress: () => this.startAdjust('servo2', 1),
                        onRelease: () => this.stopContinuous()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/PTZControl.ets", line: 35, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▲',
                            label: 'S2+',
                            disabled: this.disabled,
                            active: this.activeServo === 'servo2_up',
                            onPress: () => this.startAdjust('servo2', 1),
                            onRelease: () => this.stopContinuous()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▲',
                        label: 'S2+',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo2_up'
                    });
                }
            }, { name: "PTZButton" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // Servo1 左右 + Servo2 下
            Row.create({ space: 8 });
            Row.debugLine("entry/src/main/ets/components/PTZControl.ets(45:7)", "entry");
        }, Row);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new PTZButton(this, {
                        symbol: '◀',
                        label: 'S1-',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo1_left',
                        onPress: () => this.startAdjust('servo1', -1),
                        onRelease: () => this.stopContinuous()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/PTZControl.ets", line: 46, col: 9 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '◀',
                            label: 'S1-',
                            disabled: this.disabled,
                            active: this.activeServo === 'servo1_left',
                            onPress: () => this.startAdjust('servo1', -1),
                            onRelease: () => this.stopContinuous()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '◀',
                        label: 'S1-',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo1_left'
                    });
                }
            }, { name: "PTZButton" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/components/PTZControl.ets(55:9)", "entry");
            Column.width(40);
            Column.height(44);
            Column.justifyContent(FlexAlign.Center);
            Column.borderRadius(8);
            Column.backgroundColor('#1a1a2e');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('云台');
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(56:11)", "entry");
            Text.fontSize(10);
            Text.fontColor('#606060');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.servo2Angle.toFixed(0) + '°');
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(59:11)", "entry");
            Text.fontSize(11);
            Text.fontColor('#808080');
        }, Text);
        Text.pop();
        Column.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new PTZButton(this, {
                        symbol: '▶',
                        label: 'S1+',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo1_right',
                        onPress: () => this.startAdjust('servo1', 1),
                        onRelease: () => this.stopContinuous()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/PTZControl.ets", line: 69, col: 9 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▶',
                            label: 'S1+',
                            disabled: this.disabled,
                            active: this.activeServo === 'servo1_right',
                            onPress: () => this.startAdjust('servo1', 1),
                            onRelease: () => this.stopContinuous()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▶',
                        label: 'S1+',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo1_right'
                    });
                }
            }, { name: "PTZButton" });
        }
        // Servo1 左右 + Servo2 下
        Row.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new PTZButton(this, {
                        symbol: '▼',
                        label: 'S2-',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo2_down',
                        onPress: () => this.startAdjust('servo2', -1),
                        onRelease: () => this.stopContinuous()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/PTZControl.ets", line: 79, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▼',
                            label: 'S2-',
                            disabled: this.disabled,
                            active: this.activeServo === 'servo2_down',
                            onPress: () => this.startAdjust('servo2', -1),
                            onRelease: () => this.stopContinuous()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▼',
                        label: 'S2-',
                        disabled: this.disabled,
                        active: this.activeServo === 'servo2_down'
                    });
                }
            }, { name: "PTZButton" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // Servo2 当前角度
            Text.create('垂直: ' + this.servo2Angle.toFixed(0) + '°');
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(89:7)", "entry");
            // Servo2 当前角度
            Text.fontSize(12);
            // Servo2 当前角度
            Text.fontColor('#808080');
        }, Text);
        // Servo2 当前角度
        Text.pop();
        Column.pop();
    }
    private startAdjust(servo: string, direction: number): void {
        if (this.disabled)
            return;
        this.activeServo = servo + (direction > 0 ? '_right' : '_left');
        if (servo === 'servo2') {
            this.activeServo = servo + (direction > 0 ? '_up' : '_down');
        }
        let step: number = SERVO_STEP * direction;
        this.adjustAndSend(servo, step);
        this.commandTimer = setInterval(() => {
            this.adjustAndSend(servo, step);
        }, COMMAND_INTERVAL);
    }
    private stopContinuous(): void {
        this.activeServo = '';
        if (this.commandTimer !== null) {
            clearInterval(this.commandTimer);
            this.commandTimer = null;
        }
    }
    private adjustAndSend(servo: string, step: number): void {
        let command: RobotCommand = servo === 'servo1' ? 'servo1' : 'servo2';
        if (servo === 'servo1') {
            this.servo1Angle = Math.max(0, Math.min(180, this.servo1Angle + step));
            if (this.onCommand) {
                this.onCommand(command, this.servo1Angle);
            }
        }
        else {
            this.servo2Angle = Math.max(0, Math.min(180, this.servo2Angle + step));
            if (this.onCommand) {
                this.onCommand(command, this.servo2Angle);
            }
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
}
class PTZButton extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__symbol = new SynchedPropertySimpleOneWayPU(params.symbol, this, "symbol");
        this.__label = new SynchedPropertySimpleOneWayPU(params.label, this, "label");
        this.__disabled = new SynchedPropertySimpleOneWayPU(params.disabled, this, "disabled");
        this.__active = new SynchedPropertySimpleOneWayPU(params.active, this, "active");
        this.onPress = () => { };
        this.onRelease = () => { };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: PTZButton_Params) {
        if (params.symbol === undefined) {
            this.__symbol.set('');
        }
        if (params.label === undefined) {
            this.__label.set('');
        }
        if (params.disabled === undefined) {
            this.__disabled.set(false);
        }
        if (params.active === undefined) {
            this.__active.set(false);
        }
        if (params.onPress !== undefined) {
            this.onPress = params.onPress;
        }
        if (params.onRelease !== undefined) {
            this.onRelease = params.onRelease;
        }
    }
    updateStateVars(params: PTZButton_Params) {
        this.__symbol.reset(params.symbol);
        this.__label.reset(params.label);
        this.__disabled.reset(params.disabled);
        this.__active.reset(params.active);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__symbol.purgeDependencyOnElmtId(rmElmtId);
        this.__label.purgeDependencyOnElmtId(rmElmtId);
        this.__disabled.purgeDependencyOnElmtId(rmElmtId);
        this.__active.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__symbol.aboutToBeDeleted();
        this.__label.aboutToBeDeleted();
        this.__disabled.aboutToBeDeleted();
        this.__active.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __symbol: SynchedPropertySimpleOneWayPU<string>;
    get symbol() {
        return this.__symbol.get();
    }
    set symbol(newValue: string) {
        this.__symbol.set(newValue);
    }
    private __label: SynchedPropertySimpleOneWayPU<string>;
    get label() {
        return this.__label.get();
    }
    set label(newValue: string) {
        this.__label.set(newValue);
    }
    private __disabled: SynchedPropertySimpleOneWayPU<boolean>;
    get disabled() {
        return this.__disabled.get();
    }
    set disabled(newValue: boolean) {
        this.__disabled.set(newValue);
    }
    private __active: SynchedPropertySimpleOneWayPU<boolean>;
    get active() {
        return this.__active.get();
    }
    set active(newValue: boolean) {
        this.__active.set(newValue);
    }
    private onPress: () => void;
    private onRelease: () => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithChild();
            Button.debugLine("entry/src/main/ets/components/PTZControl.ets(150:5)", "entry");
            Button.width(44);
            Button.height(44);
            Button.padding(0);
            Button.fontColor(this.active ? '#ffffff' : '#a0a0a0');
            Button.backgroundColor(this.active ? '#0f3460' : '#1a1a2e');
            Button.borderRadius(10);
            Button.border({ width: 1, color: this.active ? '#3b82f6' : '#333333' });
            Button.enabled(!this.disabled);
            Button.onTouch((event: TouchEvent) => {
                if (event.type === TouchType.Down) {
                    this.onPress();
                }
                else if (event.type === TouchType.Up || event.type === TouchType.Cancel) {
                    this.onRelease();
                }
            });
        }, Button);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 1 });
            Column.debugLine("entry/src/main/ets/components/PTZControl.ets(151:7)", "entry");
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.symbol);
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(152:9)", "entry");
            Text.fontSize(18);
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.label);
            Text.debugLine("entry/src/main/ets/components/PTZControl.ets(154:9)", "entry");
            Text.fontSize(9);
        }, Text);
        Text.pop();
        Column.pop();
        Button.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
