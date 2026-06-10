if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface ResetPwdPage_Params {
    step?: number;
    email?: string;
    code?: string;
    newPassword?: string;
    error?: string;
    isLoading?: boolean;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
class ResetPwdPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__step = new ObservedPropertySimplePU(1, this, "step");
        this.__email = new ObservedPropertySimplePU('', this, "email");
        this.__code = new ObservedPropertySimplePU('', this, "code");
        this.__newPassword = new ObservedPropertySimplePU('', this, "newPassword");
        this.__error = new ObservedPropertySimplePU('', this, "error");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: ResetPwdPage_Params) {
        if (params.step !== undefined) {
            this.step = params.step;
        }
        if (params.email !== undefined) {
            this.email = params.email;
        }
        if (params.code !== undefined) {
            this.code = params.code;
        }
        if (params.newPassword !== undefined) {
            this.newPassword = params.newPassword;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
    }
    updateStateVars(params: ResetPwdPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__step.purgeDependencyOnElmtId(rmElmtId);
        this.__email.purgeDependencyOnElmtId(rmElmtId);
        this.__code.purgeDependencyOnElmtId(rmElmtId);
        this.__newPassword.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__step.aboutToBeDeleted();
        this.__email.aboutToBeDeleted();
        this.__code.aboutToBeDeleted();
        this.__newPassword.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __step: ObservedPropertySimplePU<number>;
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
    private __code: ObservedPropertySimplePU<string>;
    get code() {
        return this.__code.get();
    }
    set code(newValue: string) {
        this.__code.set(newValue);
    }
    private __newPassword: ObservedPropertySimplePU<string>;
    get newPassword() {
        return this.__newPassword.get();
    }
    set newPassword(newValue: string) {
        this.__newPassword.set(newValue);
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
            Column.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(20:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(22:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
            // 标题栏
            Row.margin({ top: 40 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(23:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => {
                if (this.step === 1) {
                    if (authManager.isAuthenticated()) {
                        router.back();
                    }
                    else {
                        router.replaceUrl({ url: 'pages/LoginPage' });
                    }
                }
                else {
                    this.step = 1;
                }
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(37:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('重置密码');
            Text.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(38:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(40:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(41:9)", "entry");
            Row.width(60);
        }, Row);
        Row.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 16 });
            Column.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(45:7)", "entry");
            Column.padding({ left: 40, right: 40 });
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.step === 1) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('请输入注册邮箱，我们将发送验证码');
                        Text.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(47:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#a0a0a0');
                        Text.margin({ bottom: 10 });
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        TextInput.create({ placeholder: '请输入邮箱', text: this.email });
                        TextInput.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(50:11)", "entry");
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
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        TextInput.create({ placeholder: '请输入6位验证码', text: this.code });
                        TextInput.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(58:11)", "entry");
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
                        TextInput.create({ placeholder: '请输入新密码', text: this.newPassword });
                        TextInput.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(67:11)", "entry");
                        TextInput.width('100%');
                        TextInput.height(48);
                        TextInput.backgroundColor('#1a1a2e');
                        TextInput.borderRadius(8);
                        TextInput.border({ width: 1, color: '#333333' });
                        TextInput.fontColor('#e0e0e0');
                        TextInput.placeholderColor('#606060');
                        TextInput.type(InputType.Password);
                        TextInput.onChange((v: string) => { this.newPassword = v; });
                    }, TextInput);
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.error.length > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.error);
                        Text.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(77:11)", "entry");
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
            Button.createWithLabel(this.step === 1 ? '发送验证码' : '重置密码');
            Button.debugLine("entry/src/main/ets/pages/ResetPwdPage.ets(83:9)", "entry");
            Button.width('100%');
            Button.height(48);
            Button.fontSize(16);
            Button.fontColor('#ffffff');
            Button.backgroundColor('#3b82f6');
            Button.borderRadius(8);
            Button.enabled(!this.isLoading);
            Button.onClick(() => {
                if (this.step === 1)
                    this.sendCode();
                else
                    this.resetPassword();
            });
        }, Button);
        Button.pop();
        Column.pop();
        Column.pop();
    }
    private async sendCode(): Promise<void> {
        this.error = '';
        this.isLoading = true;
        try {
            await api.sendResetPasswordCode(this.email.trim());
            this.step = 2;
        }
        catch (err) {
            this.error = (err as Error).message;
        }
        finally {
            this.isLoading = false;
        }
    }
    private async resetPassword(): Promise<void> {
        this.error = '';
        this.isLoading = true;
        try {
            await api.resetPassword(this.email.trim(), this.code, this.newPassword);
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
        return "ResetPwdPage";
    }
}
registerNamedRoute(() => new ResetPwdPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/ResetPwdPage", pageFullPath: "entry/src/main/ets/pages/ResetPwdPage", integratedHsp: "false", moduleType: "followWithHap" });
