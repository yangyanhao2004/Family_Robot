if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface LoginPage_Params {
    email?: string;
    password?: string;
    code?: string;
    loginMode?: string;
    error?: string;
    isLoading?: boolean;
}
import router from "@ohos:router";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
class LoginPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__email = new ObservedPropertySimplePU('', this, "email");
        this.__password = new ObservedPropertySimplePU('', this, "password");
        this.__code = new ObservedPropertySimplePU('', this, "code");
        this.__loginMode = new ObservedPropertySimplePU('password' // 'password' | 'code'
        , this, "loginMode");
        this.__error = new ObservedPropertySimplePU('', this, "error");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: LoginPage_Params) {
        if (params.email !== undefined) {
            this.email = params.email;
        }
        if (params.password !== undefined) {
            this.password = params.password;
        }
        if (params.code !== undefined) {
            this.code = params.code;
        }
        if (params.loginMode !== undefined) {
            this.loginMode = params.loginMode;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
    }
    updateStateVars(params: LoginPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__email.purgeDependencyOnElmtId(rmElmtId);
        this.__password.purgeDependencyOnElmtId(rmElmtId);
        this.__code.purgeDependencyOnElmtId(rmElmtId);
        this.__loginMode.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__email.aboutToBeDeleted();
        this.__password.aboutToBeDeleted();
        this.__code.aboutToBeDeleted();
        this.__loginMode.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
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
    private __code: ObservedPropertySimplePU<string>;
    get code() {
        return this.__code.get();
    }
    set code(newValue: string) {
        this.__code.set(newValue);
    }
    private __loginMode: ObservedPropertySimplePU<string>; // 'password' | 'code'
    get loginMode() {
        return this.__loginMode.get();
    }
    set loginMode(newValue: string) {
        this.__loginMode.set(newValue);
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
    aboutToAppear(): void {
        // 已登录则直接跳转
        if (authManager.isAuthenticated()) {
            this.navigateToMain();
        }
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/LoginPage.ets(28:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题区域
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/LoginPage.ets(30:7)", "entry");
            // 标题区域
            Column.width('100%');
            // 标题区域
            Column.padding({ top: 80, bottom: 40 });
            // 标题区域
            Column.alignItems(HorizontalAlign.Center);
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('家庭机器人');
            Text.debugLine("entry/src/main/ets/pages/LoginPage.ets(31:9)", "entry");
            Text.fontSize(32);
            Text.fontWeight(FontWeight.Bold);
            Text.fontColor('#ffffff');
            Text.margin({ bottom: 8 });
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('Family Robot Control');
            Text.debugLine("entry/src/main/ets/pages/LoginPage.ets(37:9)", "entry");
            Text.fontSize(15);
            Text.fontColor('#808080');
            Text.margin({ bottom: 40 });
        }, Text);
        Text.pop();
        // 标题区域
        Column.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 登录模式切换
            Row.create({ space: 24 });
            Row.debugLine("entry/src/main/ets/pages/LoginPage.ets(47:7)", "entry");
            // 登录模式切换
            Row.width('100%');
            // 登录模式切换
            Row.justifyContent(FlexAlign.Center);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('密码登录');
            Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(48:9)", "entry");
            Button.fontSize(14);
            Button.fontColor(this.loginMode === 'password' ? '#3b82f6' : '#808080');
            Button.backgroundColor('transparent');
            Button.border({ width: 0, color: this.loginMode === 'password' ? '#3b82f6' : 'transparent', style: BorderStyle.Solid });
            Button.borderWidth({ bottom: 2 });
            Button.borderRadius(0);
            Button.onClick(() => { this.loginMode = 'password'; });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('验证码登录');
            Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(56:9)", "entry");
            Button.fontSize(14);
            Button.fontColor(this.loginMode === 'code' ? '#3b82f6' : '#808080');
            Button.backgroundColor('transparent');
            Button.border({ width: 0, color: this.loginMode === 'code' ? '#3b82f6' : 'transparent', style: BorderStyle.Solid });
            Button.borderWidth({ bottom: 2 });
            Button.borderRadius(0);
            Button.onClick(() => { this.loginMode = 'code'; });
        }, Button);
        Button.pop();
        // 登录模式切换
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 表单
            Column.create({ space: 16 });
            Column.debugLine("entry/src/main/ets/pages/LoginPage.ets(69:7)", "entry");
            // 表单
            Column.padding({ left: 40, right: 40 });
            // 表单
            Column.width('100%');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 邮箱输入
            TextInput.create({ placeholder: '请输入邮箱', text: this.email });
            TextInput.debugLine("entry/src/main/ets/pages/LoginPage.ets(71:9)", "entry");
            // 邮箱输入
            TextInput.width('100%');
            // 邮箱输入
            TextInput.height(48);
            // 邮箱输入
            TextInput.backgroundColor('#1a1a2e');
            // 邮箱输入
            TextInput.borderRadius(8);
            // 邮箱输入
            TextInput.border({ width: 1, color: '#333333' });
            // 邮箱输入
            TextInput.fontColor('#e0e0e0');
            // 邮箱输入
            TextInput.placeholderColor('#606060');
            // 邮箱输入
            TextInput.type(InputType.Email);
            // 邮箱输入
            TextInput.onChange((value: string) => { this.email = value; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.loginMode === 'password') {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 密码输入
                        TextInput.create({ placeholder: '请输入密码', text: this.password });
                        TextInput.debugLine("entry/src/main/ets/pages/LoginPage.ets(84:11)", "entry");
                        // 密码输入
                        TextInput.width('100%');
                        // 密码输入
                        TextInput.height(48);
                        // 密码输入
                        TextInput.backgroundColor('#1a1a2e');
                        // 密码输入
                        TextInput.borderRadius(8);
                        // 密码输入
                        TextInput.border({ width: 1, color: '#333333' });
                        // 密码输入
                        TextInput.fontColor('#e0e0e0');
                        // 密码输入
                        TextInput.placeholderColor('#606060');
                        // 密码输入
                        TextInput.type(InputType.Password);
                        // 密码输入
                        TextInput.onChange((value: string) => { this.password = value; });
                    }, TextInput);
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 验证码输入
                        Row.create();
                        Row.debugLine("entry/src/main/ets/pages/LoginPage.ets(96:11)", "entry");
                        // 验证码输入
                        Row.width('100%');
                    }, Row);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        TextInput.create({ placeholder: '请输入验证码', text: this.code });
                        TextInput.debugLine("entry/src/main/ets/pages/LoginPage.ets(97:13)", "entry");
                        TextInput.layoutWeight(1);
                        TextInput.height(48);
                        TextInput.backgroundColor('#1a1a2e');
                        TextInput.borderRadius(8);
                        TextInput.border({ width: 1, color: '#333333' });
                        TextInput.fontColor('#e0e0e0');
                        TextInput.placeholderColor('#606060');
                        TextInput.maxLength(6);
                        TextInput.type(InputType.Number);
                        TextInput.onChange((value: string) => { this.code = value; });
                    }, TextInput);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('发送验证码');
                        Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(109:13)", "entry");
                        Button.fontSize(12);
                        Button.height(48);
                        Button.padding({ left: 12, right: 12 });
                        Button.backgroundColor('#0f3460');
                        Button.borderRadius(8);
                        Button.fontColor('#ffffff');
                        Button.margin({ left: 10 });
                        Button.onClick(() => { this.sendCode(); });
                    }, Button);
                    Button.pop();
                    // 验证码输入
                    Row.pop();
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 错误提示
            if (this.error.length > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.error);
                        Text.debugLine("entry/src/main/ets/pages/LoginPage.ets(124:11)", "entry");
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
            // 登录按钮
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 登录按钮
            Button.createWithLabel(this.isLoading ? '登录中...' : '登 录');
            Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(135:9)", "entry");
            // 登录按钮
            Button.width('100%');
            // 登录按钮
            Button.height(48);
            // 登录按钮
            Button.fontSize(16);
            // 登录按钮
            Button.fontColor('#ffffff');
            // 登录按钮
            Button.backgroundColor('#3b82f6');
            // 登录按钮
            Button.borderRadius(8);
            // 登录按钮
            Button.enabled(!this.isLoading);
            // 登录按钮
            Button.onClick(() => { this.handleLogin(); });
        }, Button);
        // 登录按钮
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 注册 / 忘记密码
            Row.create({ space: 20 });
            Row.debugLine("entry/src/main/ets/pages/LoginPage.ets(146:9)", "entry");
            // 注册 / 忘记密码
            Row.width('100%');
            // 注册 / 忘记密码
            Row.justifyContent(FlexAlign.Center);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('注册账号');
            Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(147:11)", "entry");
            Button.fontSize(13);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => { router.pushUrl({ url: 'pages/RegisterPage' }); });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('忘记密码');
            Button.debugLine("entry/src/main/ets/pages/LoginPage.ets(152:11)", "entry");
            Button.fontSize(13);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => { router.pushUrl({ url: 'pages/ResetPwdPage' }); });
        }, Button);
        Button.pop();
        // 注册 / 忘记密码
        Row.pop();
        // 表单
        Column.pop();
        Column.pop();
    }
    private async handleLogin(): Promise<void> {
        this.error = '';
        if (this.email.trim().length === 0) {
            this.error = '请输入邮箱';
            return;
        }
        this.isLoading = true;
        try {
            if (this.loginMode === 'password') {
                if (this.password.length === 0) {
                    this.error = '请输入密码';
                    this.isLoading = false;
                    return;
                }
                await authManager.login(this.email.trim(), this.password);
            }
            else {
                if (this.code.length === 0) {
                    this.error = '请输入验证码';
                    this.isLoading = false;
                    return;
                }
                let res: Record<string, Object> = await api.verifyLoginCode(this.email.trim(), this.code);
                await authManager.setAuth(res['token'] as string, res['role'] as string);
            }
            this.navigateToMain();
        }
        catch (err) {
            this.error = (err as Error).message;
        }
        finally {
            this.isLoading = false;
        }
    }
    private async sendCode(): Promise<void> {
        if (this.email.trim().length === 0) {
            this.error = '请先输入邮箱';
            return;
        }
        try {
            await api.sendLoginCode(this.email.trim());
            this.error = '';
        }
        catch (err) {
            this.error = (err as Error).message;
        }
    }
    private navigateToMain(): void {
        if (authManager.isAdmin()) {
            // Admin 没有在鸿蒙端实现，跳转到 Dashboard
            router.replaceUrl({ url: 'pages/DashboardPage' });
        }
        else {
            router.replaceUrl({ url: 'pages/DashboardPage' });
        }
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "LoginPage";
    }
}
registerNamedRoute(() => new LoginPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/LoginPage", pageFullPath: "entry/src/main/ets/pages/LoginPage", integratedHsp: "false", moduleType: "followWithHap" });
