if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface RegisterPage_Params {
    step?: number;
    email?: string;
    password?: string;
    serialNumber?: string;
    code?: string;
    error?: string;
    isLoading?: boolean;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
class RegisterPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__step = new ObservedPropertySimplePU(1 // 1=填信息, 2=验码
        , this, "step");
        this.__email = new ObservedPropertySimplePU('', this, "email");
        this.__password = new ObservedPropertySimplePU('', this, "password");
        this.__serialNumber = new ObservedPropertySimplePU('', this, "serialNumber");
        this.__code = new ObservedPropertySimplePU('', this, "code");
        this.__error = new ObservedPropertySimplePU('', this, "error");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: RegisterPage_Params) {
        if (params.step !== undefined) {
            this.step = params.step;
        }
        if (params.email !== undefined) {
            this.email = params.email;
        }
        if (params.password !== undefined) {
            this.password = params.password;
        }
        if (params.serialNumber !== undefined) {
            this.serialNumber = params.serialNumber;
        }
        if (params.code !== undefined) {
            this.code = params.code;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
    }
    updateStateVars(params: RegisterPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__step.purgeDependencyOnElmtId(rmElmtId);
        this.__email.purgeDependencyOnElmtId(rmElmtId);
        this.__password.purgeDependencyOnElmtId(rmElmtId);
        this.__serialNumber.purgeDependencyOnElmtId(rmElmtId);
        this.__code.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__step.aboutToBeDeleted();
        this.__email.aboutToBeDeleted();
        this.__password.aboutToBeDeleted();
        this.__serialNumber.aboutToBeDeleted();
        this.__code.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __step: ObservedPropertySimplePU<number>; // 1=填信息, 2=验码
    get step() {
        return this.__step.get();
    }
    set step(newValue: number) {
        this.__step.set(newValue);
    }
    private __email: ObservedPropertySimplePU<string>;
    get email() {
        return this.__email.get();
    }
    set email(newValue: string) {
        this.__email.set(newValue);
    }
    private __password: ObservedPropertySimplePU<string>;
    get password() {
        return this.__password.get();
    }
    set password(newValue: string) {
        this.__password.set(newValue);
    }
    private __serialNumber: ObservedPropertySimplePU<string>;
    get serialNumber() {
        return this.__serialNumber.get();
    }
    set serialNumber(newValue: string) {
        this.__serialNumber.set(newValue);
    }
    private __code: ObservedPropertySimplePU<string>;
    get code() {
        return this.__code.get();
    }
    set code(newValue: string) {
        this.__code.set(newValue);
    }
    private __error: ObservedPropertySimplePU<string>;
    get error() {
        return this.__error.get();
    }
    set error(newValue: string) {
        this.__error.set(newValue);
    }
    private __isLoading: ObservedPropertySimplePU<boolean>;
    get isLoading() {
        return this.__isLoading.get();
    }
    set isLoading(newValue: boolean) {
        this.__isLoading.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/RegisterPage.ets(20:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/RegisterPage.ets(22:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
            // 标题栏
            Row.margin({ top: 40 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/RegisterPage.ets(23:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => {
                if (this.step === 1) {
                    router.back();
                }
                else {
                    this.step = 1;
                }
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/RegisterPage.ets(34:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('注册账号');
            Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(35:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/RegisterPage.ets(38:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 占位保持居中
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/RegisterPage.ets(40:9)", "entry");
            // 占位保持居中
            Row.width(60);
        }, Row);
        // 占位保持居中
        Row.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 步骤进度
            Row.create({ space: 8 });
            Row.debugLine("entry/src/main/ets/pages/RegisterPage.ets(47:7)", "entry");
            // 步骤进度
            Row.width('100%');
            // 步骤进度
            Row.justifyContent(FlexAlign.Center);
            // 步骤进度
            Row.margin({ top: 20, bottom: 30 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/RegisterPage.ets(48:9)", "entry");
            Row.width(24);
            Row.height(24);
            Row.borderRadius(12);
            Row.backgroundColor(this.step >= 1 ? '#3b82f6' : '#333333');
            Row.justifyContent(FlexAlign.Center);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('1');
            Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(49:11)", "entry");
            Text.fontSize(12);
            Text.fontColor(this.step >= 1 ? '#ffffff' : '#808080');
        }, Text);
        Text.pop();
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Divider.create();
            Divider.debugLine("entry/src/main/ets/pages/RegisterPage.ets(58:9)", "entry");
            Divider.width(40);
            Divider.height(1);
            Divider.color(this.step >= 2 ? '#3b82f6' : '#333333');
        }, Divider);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/RegisterPage.ets(60:9)", "entry");
            Row.width(24);
            Row.height(24);
            Row.borderRadius(12);
            Row.backgroundColor(this.step >= 2 ? '#3b82f6' : '#333333');
            Row.justifyContent(FlexAlign.Center);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('2');
            Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(61:11)", "entry");
            Text.fontSize(12);
            Text.fontColor(this.step >= 2 ? '#ffffff' : '#808080');
        }, Text);
        Text.pop();
        Row.pop();
        // 步骤进度
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.step === 1) {
                this.ifElseBranchUpdateFunction(0, () => {
                    // Step 1: 填写信息
                    this.BuildStep1.bind(this)();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    // Step 2: 验证码
                    this.BuildStep2.bind(this)();
                });
            }
        }, If);
        If.pop();
        Column.pop();
    }
    BuildStep1(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 16 });
            Column.debugLine("entry/src/main/ets/pages/RegisterPage.ets(89:5)", "entry");
            Column.padding({ left: 40, right: 40 });
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextInput.create({ placeholder: '请输入邮箱', text: this.email });
            TextInput.debugLine("entry/src/main/ets/pages/RegisterPage.ets(90:7)", "entry");
            TextInput.width('100%');
            TextInput.height(48);
            TextInput.backgroundColor('#1a1a2e');
            TextInput.borderRadius(8);
            TextInput.border({ width: 1, color: '#333333' });
            TextInput.fontColor('#e0e0e0');
            TextInput.placeholderColor('#606060');
            TextInput.type(InputType.Email);
            TextInput.onChange((v: string) => { this.email = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextInput.create({ placeholder: '请输入密码', text: this.password });
            TextInput.debugLine("entry/src/main/ets/pages/RegisterPage.ets(98:7)", "entry");
            TextInput.width('100%');
            TextInput.height(48);
            TextInput.backgroundColor('#1a1a2e');
            TextInput.borderRadius(8);
            TextInput.border({ width: 1, color: '#333333' });
            TextInput.fontColor('#e0e0e0');
            TextInput.placeholderColor('#606060');
            TextInput.type(InputType.Password);
            TextInput.onChange((v: string) => { this.password = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextInput.create({ placeholder: '请输入机器人序列号', text: this.serialNumber });
            TextInput.debugLine("entry/src/main/ets/pages/RegisterPage.ets(106:7)", "entry");
            TextInput.width('100%');
            TextInput.height(48);
            TextInput.backgroundColor('#1a1a2e');
            TextInput.borderRadius(8);
            TextInput.border({ width: 1, color: '#333333' });
            TextInput.fontColor('#e0e0e0');
            TextInput.placeholderColor('#606060');
            TextInput.onChange((v: string) => { this.serialNumber = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.error.length > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.error);
                        Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(114:9)", "entry");
                        Text.fontSize(13);
                        Text.fontColor('#ef4444');
                        Text.width('100%');
                        Text.textAlign(TextAlign.Center);
                        Text.padding(10);
                        Text.backgroundColor('#2a1a1a');
                        Text.borderRadius(6);
                    }, Text);
                    Text.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('发送验证码');
            Button.debugLine("entry/src/main/ets/pages/RegisterPage.ets(120:7)", "entry");
            Button.width('100%');
            Button.height(48);
            Button.fontSize(16);
            Button.fontColor('#ffffff');
            Button.backgroundColor('#3b82f6');
            Button.borderRadius(8);
            Button.enabled(!this.isLoading && this.email.length > 0
                && this.password.length > 0 && this.serialNumber.length > 0);
            Button.onClick(() => { this.sendRegisterCode(); });
        }, Button);
        Button.pop();
        Column.pop();
    }
    BuildStep2(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 16 });
            Column.debugLine("entry/src/main/ets/pages/RegisterPage.ets(133:5)", "entry");
            Column.padding({ left: 40, right: 40 });
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('验证码已发送至 ' + this.email);
            Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(134:7)", "entry");
            Text.fontSize(14);
            Text.fontColor('#a0a0a0');
            Text.margin({ bottom: 10 });
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextInput.create({ placeholder: '请输入6位验证码', text: this.code });
            TextInput.debugLine("entry/src/main/ets/pages/RegisterPage.ets(138:7)", "entry");
            TextInput.width('100%');
            TextInput.height(48);
            TextInput.backgroundColor('#1a1a2e');
            TextInput.borderRadius(8);
            TextInput.border({ width: 1, color: '#333333' });
            TextInput.fontColor('#e0e0e0');
            TextInput.placeholderColor('#606060');
            TextInput.maxLength(6);
            TextInput.type(InputType.Number);
            TextInput.fontSize(20);
            TextInput.letterSpacing(8);
            TextInput.textAlign(TextAlign.Center);
            TextInput.onChange((v: string) => { this.code = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.error.length > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.error);
                        Text.debugLine("entry/src/main/ets/pages/RegisterPage.ets(149:9)", "entry");
                        Text.fontSize(13);
                        Text.fontColor('#ef4444');
                        Text.width('100%');
                        Text.textAlign(TextAlign.Center);
                        Text.padding(10);
                        Text.backgroundColor('#2a1a1a');
                        Text.borderRadius(6);
                    }, Text);
                    Text.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('完成注册');
            Button.debugLine("entry/src/main/ets/pages/RegisterPage.ets(155:7)", "entry");
            Button.width('100%');
            Button.height(48);
            Button.fontSize(16);
            Button.fontColor('#ffffff');
            Button.backgroundColor('#10b981');
            Button.borderRadius(8);
            Button.enabled(!this.isLoading && this.code.length === 6);
            Button.onClick(() => { this.verifyCode(); });
        }, Button);
        Button.pop();
        Column.pop();
    }
    private async sendRegisterCode(): Promise<void> {
        this.error = '';
        this.isLoading = true;
        try {
            await api.register(this.email.trim(), this.password, this.serialNumber.trim());
            this.step = 2;
        }
        catch (err) {
            this.error = (err as Error).message;
        }
        finally {
            this.isLoading = false;
        }
    }
    private async verifyCode(): Promise<void> {
        this.error = '';
        this.isLoading = true;
        try {
            await api.verify(this.email.trim(), this.code);
            router.replaceUrl({ url: 'pages/LoginPage' });
        }
        catch (err) {
            this.error = (err as Error).message;
        }
        finally {
            this.isLoading = false;
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "RegisterPage";
    }
}
registerNamedRoute(() => new RegisterPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/RegisterPage", pageFullPath: "entry/src/main/ets/pages/RegisterPage", integratedHsp: "false", moduleType: "followWithHap" });
