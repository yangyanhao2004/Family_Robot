if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface DPadButton_Params {
    symbol?: string;
    btnDirection?: string;
    active?: boolean;
    disabled?: boolean;
    isStop?: boolean;
    onPress?: () => void;
    onRelease?: () => void;
}
interface DPadControl_Params {
    onCommand?: (command: RobotCommand, angle?: number) => void;
    disabled?: boolean;
    activeDirection?: string;
    commandTimer?: number | null;
}
import type { RobotCommand } from '../model/Types';
import { COMMAND_INTERVAL } from "@bundle:com.familyrobot.harmonyos/entry/ets/common/Constants";
export class DPadControl extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.onCommand = undefined;
        this.__disabled = new SynchedPropertySimpleOneWayPU(params.disabled, this, "disabled");
        this.__activeDirection = new ObservedPropertySimplePU('', this, "activeDirection");
        this.commandTimer = null;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: DPadControl_Params) {
        if (params.onCommand !== undefined) {
            this.onCommand = params.onCommand;
        }
        if (params.disabled === undefined) {
            this.__disabled.set(false);
        }
        if (params.activeDirection !== undefined) {
            this.activeDirection = params.activeDirection;
        }
        if (params.commandTimer !== undefined) {
            this.commandTimer = params.commandTimer;
        }
    }
    updateStateVars(params: DPadControl_Params) {
        this.__disabled.reset(params.disabled);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__disabled.purgeDependencyOnElmtId(rmElmtId);
        this.__activeDirection.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__disabled.aboutToBeDeleted();
        this.__activeDirection.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private onCommand?: (command: RobotCommand, angle?: number) => void;
    private __disabled: SynchedPropertySimpleOneWayPU<boolean>;
    get disabled() {
        return this.__disabled.get();
    }
    set disabled(newValue: boolean) {
        this.__disabled.set(newValue);
    }
    private __activeDirection: ObservedPropertySimplePU<string>;
    get activeDirection() {
        return this.__activeDirection.get();
    }
    set activeDirection(newValue: string) {
        this.__activeDirection.set(newValue);
    }
    private commandTimer: number | null;
    aboutToDisappear(): void {
        this.stopContinuousCommand();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 8 });
            Column.debugLine("entry/src/main/ets/components/DPadControl.ets(21:5)", "entry");
            Column.padding(12);
            Column.borderRadius(12);
            Column.backgroundColor('#16213e');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('运动控制');
            Text.debugLine("entry/src/main/ets/components/DPadControl.ets(22:7)", "entry");
            Text.fontSize(14);
            Text.fontColor('#a0a0a0');
            Text.margin({ bottom: 4 });
        }, Text);
        Text.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 上
                    DPadButton(this, {
                        symbol: '▲',
                        btnDirection: 'forward',
                        active: this.activeDirection === 'forward',
                        disabled: this.disabled,
                        onPress: () => this.startCommand('forward'),
                        onRelease: () => this.stopCommand()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/DPadControl.ets", line: 28, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▲',
                            btnDirection: 'forward',
                            active: this.activeDirection === 'forward',
                            disabled: this.disabled,
                            onPress: () => this.startCommand('forward'),
                            onRelease: () => this.stopCommand()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▲',
                        btnDirection: 'forward',
                        active: this.activeDirection === 'forward',
                        disabled: this.disabled
                    });
                }
            }, { name: "DPadButton" });
        }
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 左 中 右
            Row.create({ space: 8 });
            Row.debugLine("entry/src/main/ets/components/DPadControl.ets(38:7)", "entry");
        }, Row);
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new DPadButton(this, {
                        symbol: '◀',
                        btnDirection: 'left',
                        active: this.activeDirection === 'left',
                        disabled: this.disabled,
                        onPress: () => this.startCommand('left'),
                        onRelease: () => this.stopCommand()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/DPadControl.ets", line: 39, col: 9 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '◀',
                            btnDirection: 'left',
                            active: this.activeDirection === 'left',
                            disabled: this.disabled,
                            onPress: () => this.startCommand('left'),
                            onRelease: () => this.stopCommand()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '◀',
                        btnDirection: 'left',
                        active: this.activeDirection === 'left',
                        disabled: this.disabled
                    });
                }
            }, { name: "DPadButton" });
        }
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new DPadButton(this, {
                        symbol: '⏹',
                        btnDirection: 'stop',
                        active: false,
                        disabled: this.disabled,
                        isStop: true,
                        onPress: () => {
                            this.emitCommand('stop');
                        },
                        onRelease: () => { }
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/DPadControl.ets", line: 48, col: 9 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '⏹',
                            btnDirection: 'stop',
                            active: false,
                            disabled: this.disabled,
                            isStop: true,
                            onPress: () => {
                                this.emitCommand('stop');
                            },
                            onRelease: () => { }
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '⏹',
                        btnDirection: 'stop',
                        active: false,
                        disabled: this.disabled,
                        isStop: true
                    });
                }
            }, { name: "DPadButton" });
        }
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new DPadButton(this, {
                        symbol: '▶',
                        btnDirection: 'right',
                        active: this.activeDirection === 'right',
                        disabled: this.disabled,
                        onPress: () => this.startCommand('right'),
                        onRelease: () => this.stopCommand()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/DPadControl.ets", line: 60, col: 9 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▶',
                            btnDirection: 'right',
                            active: this.activeDirection === 'right',
                            disabled: this.disabled,
                            onPress: () => this.startCommand('right'),
                            onRelease: () => this.stopCommand()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▶',
                        btnDirection: 'right',
                        active: this.activeDirection === 'right',
                        disabled: this.disabled
                    });
                }
            }, { name: "DPadButton" });
        }
        // 左 中 右
        Row.pop();
        {
            this.observeComponentCreation2((elmtId, isInitialRender) => {
                if (isInitialRender) {
                    let componentCall = new 
                    // 下
                    DPadButton(this, {
                        symbol: '▼',
                        btnDirection: 'backward',
                        active: this.activeDirection === 'backward',
                        disabled: this.disabled,
                        onPress: () => this.startCommand('backward'),
                        onRelease: () => this.stopCommand()
                    }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/components/DPadControl.ets", line: 71, col: 7 });
                    ViewPU.create(componentCall);
                    let paramsLambda = () => {
                        return {
                            symbol: '▼',
                            btnDirection: 'backward',
                            active: this.activeDirection === 'backward',
                            disabled: this.disabled,
                            onPress: () => this.startCommand('backward'),
                            onRelease: () => this.stopCommand()
                        };
                    };
                    componentCall.paramsGenerator_ = paramsLambda;
                }
                else {
                    this.updateStateVarsOfChildByElmtId(elmtId, {
                        symbol: '▼',
                        btnDirection: 'backward',
                        active: this.activeDirection === 'backward',
                        disabled: this.disabled
                    });
                }
            }, { name: "DPadButton" });
        }
        Column.pop();
    }
    private startCommand(direction: string): void {
        if (this.disabled)
            return;
        this.activeDirection = direction;
        this.emitCommand(direction as RobotCommand);
        // 持续发送
        this.commandTimer = setInterval(() => {
            this.emitCommand(direction as RobotCommand);
        }, COMMAND_INTERVAL);
    }
    private stopCommand(): void {
        this.stopContinuousCommand();
        this.emitCommand('stop');
    }
    private stopContinuousCommand(): void {
        this.activeDirection = '';
        if (this.commandTimer !== null) {
            clearInterval(this.commandTimer);
            this.commandTimer = null;
        }
    }
    private emitCommand(command: RobotCommand): void {
        if (this.onCommand) {
            this.onCommand(command);
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
}
class DPadButton extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__symbol = new SynchedPropertySimpleOneWayPU(params.symbol, this, "symbol");
        this.__btnDirection = new SynchedPropertySimpleOneWayPU(params.btnDirection, this, "btnDirection");
        this.__active = new SynchedPropertySimpleOneWayPU(params.active, this, "active");
        this.__disabled = new SynchedPropertySimpleOneWayPU(params.disabled, this, "disabled");
        this.__isStop = new SynchedPropertySimpleOneWayPU(params.isStop, this, "isStop");
        this.onPress = () => { };
        this.onRelease = () => { };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: DPadButton_Params) {
        if (params.symbol === undefined) {
            this.__symbol.set('');
        }
        if (params.btnDirection === undefined) {
            this.__btnDirection.set('');
        }
        if (params.active === undefined) {
            this.__active.set(false);
        }
        if (params.disabled === undefined) {
            this.__disabled.set(false);
        }
        if (params.isStop === undefined) {
            this.__isStop.set(false);
        }
        if (params.onPress !== undefined) {
            this.onPress = params.onPress;
        }
        if (params.onRelease !== undefined) {
            this.onRelease = params.onRelease;
        }
    }
    updateStateVars(params: DPadButton_Params) {
        this.__symbol.reset(params.symbol);
        this.__btnDirection.reset(params.btnDirection);
        this.__active.reset(params.active);
        this.__disabled.reset(params.disabled);
        this.__isStop.reset(params.isStop);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__symbol.purgeDependencyOnElmtId(rmElmtId);
        this.__btnDirection.purgeDependencyOnElmtId(rmElmtId);
        this.__active.purgeDependencyOnElmtId(rmElmtId);
        this.__disabled.purgeDependencyOnElmtId(rmElmtId);
        this.__isStop.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__symbol.aboutToBeDeleted();
        this.__btnDirection.aboutToBeDeleted();
        this.__active.aboutToBeDeleted();
        this.__disabled.aboutToBeDeleted();
        this.__isStop.aboutToBeDeleted();
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
    private __btnDirection: SynchedPropertySimpleOneWayPU<string>;
    get btnDirection() {
        return this.__btnDirection.get();
    }
    set btnDirection(newValue: string) {
        this.__btnDirection.set(newValue);
    }
    private __active: SynchedPropertySimpleOneWayPU<boolean>;
    get active() {
        return this.__active.get();
    }
    set active(newValue: boolean) {
        this.__active.set(newValue);
    }
    private __disabled: SynchedPropertySimpleOneWayPU<boolean>;
    get disabled() {
        return this.__disabled.get();
    }
    set disabled(newValue: boolean) {
        this.__disabled.set(newValue);
    }
    private __isStop: SynchedPropertySimpleOneWayPU<boolean>;
    get isStop() {
        return this.__isStop.get();
    }
    set isStop(newValue: boolean) {
        this.__isStop.set(newValue);
    }
    private onPress: () => void;
    private onRelease: () => void;
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel(this.symbol);
            Button.debugLine("entry/src/main/ets/components/DPadControl.ets(129:5)", "entry");
            Button.fontSize(this.isStop ? 16 : 24);
            Button.width(56);
            Button.height(56);
            Button.fontColor(this.active ? '#ffffff' : '#a0a0a0');
            Button.backgroundColor(this.isStop
                ? '#2a1a1a'
                : (this.active ? '#0f3460' : '#1a1a2e'));
            Button.borderRadius(12);
            Button.border({ width: 1, color: this.active ? '#3b82f6' : '#333333' });
            Button.enabled(!this.disabled);
            Button.padding(0);
            Button.onTouch((event: TouchEvent) => {
                if (event.type === TouchType.Down) {
                    this.onPress();
                }
                else if (event.type === TouchType.Up || event.type === TouchType.Cancel) {
                    this.onRelease();
                }
            });
        }, Button);
        Button.pop();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
