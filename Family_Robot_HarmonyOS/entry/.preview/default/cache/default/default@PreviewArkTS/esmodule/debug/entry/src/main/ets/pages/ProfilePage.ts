if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface ProfilePage_Params {
    profile?: UserProfile;
    isLoading?: boolean;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
import { webSocketService } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/WebSocketService";
import type { UserProfile } from '../model/Types';
class ProfilePage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__profile = new ObservedPropertyObjectPU({
            name: '', email: '', role: '', avatar: '', lastLogin: ''
        }, this, "profile");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: ProfilePage_Params) {
        if (params.profile !== undefined) {
            this.profile = params.profile;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
    }
    updateStateVars(params: ProfilePage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__profile.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__profile.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __profile: ObservedPropertyObjectPU<UserProfile>;
    get profile() {
        return this.__profile.get();
    }
    set profile(newValue: UserProfile) {
        this.__profile.set(newValue);
    }
    private __isLoading: ObservedPropertySimplePU<boolean>;
    get isLoading() {
        return this.__isLoading.get();
    }
    set isLoading(newValue: boolean) {
        this.__isLoading.set(newValue);
    }
    aboutToAppear(): void {
        this.loadProfile();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/ProfilePage.ets(24:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ProfilePage.ets(26:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/ProfilePage.ets(27:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => router.back());
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ProfilePage.ets(31:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('个人中心');
            Text.debugLine("entry/src/main/ets/pages/ProfilePage.ets(32:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ProfilePage.ets(34:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ProfilePage.ets(35:9)", "entry");
            Row.width(60);
        }, Row);
        Row.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.isLoading) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/ProfilePage.ets(40:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        LoadingProgress.create();
                        LoadingProgress.debugLine("entry/src/main/ets/pages/ProfilePage.ets(41:11)", "entry");
                        LoadingProgress.width(40);
                        LoadingProgress.height(40);
                        LoadingProgress.color('#3b82f6');
                    }, LoadingProgress);
                    Column.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create({ space: 20 });
                        Column.debugLine("entry/src/main/ets/pages/ProfilePage.ets(45:9)", "entry");
                        Column.padding(16);
                        Column.width('100%');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 头像
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/ProfilePage.ets(47:11)", "entry");
                        // 头像
                        Column.width(72);
                        // 头像
                        Column.height(72);
                        // 头像
                        Column.borderRadius(36);
                        // 头像
                        Column.backgroundColor('#3b82f6');
                        // 头像
                        Column.justifyContent(FlexAlign.Center);
                        // 头像
                        Column.margin({ top: 24 });
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.profile.name.length > 0
                            ? this.profile.name.charAt(0).toUpperCase()
                            : '?');
                        Text.debugLine("entry/src/main/ets/pages/ProfilePage.ets(48:13)", "entry");
                        Text.fontSize(36);
                        Text.fontColor('#ffffff');
                    }, Text);
                    Text.pop();
                    // 头像
                    Column.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 用户信息
                        Column.create({ space: 12 });
                        Column.debugLine("entry/src/main/ets/pages/ProfilePage.ets(60:11)", "entry");
                        // 用户信息
                        Column.width('100%');
                        // 用户信息
                        Column.padding(16);
                        // 用户信息
                        Column.borderRadius(8);
                        // 用户信息
                        Column.backgroundColor('#1a1a2e');
                    }, Column);
                    this.InfoRow.bind(this)('姓名', this.profile.name);
                    this.InfoRow.bind(this)('邮箱', this.profile.email);
                    this.InfoRow.bind(this)('角色', this.profile.role);
                    this.InfoRow.bind(this)('最后登录', this.profile.lastLogin);
                    // 用户信息
                    Column.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 操作按钮
                        Button.createWithLabel('修改密码');
                        Button.debugLine("entry/src/main/ets/pages/ProfilePage.ets(72:11)", "entry");
                        // 操作按钮
                        Button.width('100%');
                        // 操作按钮
                        Button.height(44);
                        // 操作按钮
                        Button.fontSize(15);
                        // 操作按钮
                        Button.fontColor('#ffffff');
                        // 操作按钮
                        Button.backgroundColor('#0f3460');
                        // 操作按钮
                        Button.borderRadius(8);
                        // 操作按钮
                        Button.onClick(() => {
                            router.pushUrl({ url: 'pages/ResetPwdPage' });
                        });
                    }, Button);
                    // 操作按钮
                    Button.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('退出登录');
                        Button.debugLine("entry/src/main/ets/pages/ProfilePage.ets(80:11)", "entry");
                        Button.width('100%');
                        Button.height(44);
                        Button.fontSize(15);
                        Button.fontColor('#ef4444');
                        Button.backgroundColor('transparent');
                        Button.border({ width: 1, color: '#ef4444' });
                        Button.borderRadius(8);
                        Button.onClick(() => { this.logout(); });
                    }, Button);
                    Button.pop();
                    Column.pop();
                });
            }
        }, If);
        If.pop();
        Column.pop();
    }
    InfoRow(label: string, value: string, parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ProfilePage.ets(97:5)", "entry");
            Row.width('100%');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(label);
            Text.debugLine("entry/src/main/ets/pages/ProfilePage.ets(98:7)", "entry");
            Text.fontSize(13);
            Text.fontColor('#808080');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ProfilePage.ets(100:7)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(value || '--');
            Text.debugLine("entry/src/main/ets/pages/ProfilePage.ets(101:7)", "entry");
            Text.fontSize(14);
            Text.fontColor('#e0e0e0');
        }, Text);
        Text.pop();
        Row.pop();
    }
    private async loadProfile(): Promise<void> {
        this.isLoading = true;
        try {
            let data: Record<string, Object> = await api.getProfile();
            this.profile = {
                name: (data['name'] as string) || '',
                email: (data['email'] as string) || '',
                role: (data['role'] as string) || '',
                avatar: (data['avatar'] as string) || '',
                lastLogin: (data['lastLogin'] as string) || ''
            };
        }
        catch (_err) {
            // 失败时使用基本数据
        }
        finally {
            this.isLoading = false;
        }
    }
    private async logout(): Promise<void> {
        // 结束 AI 会话
        let userId: number = authManager.getUserIdFromToken();
        webSocketService.sendAISessionEnd(userId);
        // 断开 WebSocket
        webSocketService.disconnect();
        // 清除认证
        await authManager.logout();
        // 跳转到登录页
        router.replaceUrl({ url: 'pages/LoginPage' });
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "ProfilePage";
    }
}
registerNamedRoute(() => new ProfilePage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/ProfilePage", pageFullPath: "entry/src/main/ets/pages/ProfilePage", integratedHsp: "false", moduleType: "followWithHap" });
