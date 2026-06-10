if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface SettingsPage_Params {
    settings?: RobotSettings;
    isLoading?: boolean;
    error?: string;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import type { RobotSettings } from '../model/Types';
class SettingsPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__settings = new ObservedPropertyObjectPU({ firmwareVersion: '', serialNumber: '' }, this, "settings");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.__error = new ObservedPropertySimplePU('', this, "error");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: SettingsPage_Params) {
        if (params.settings !== undefined) {
            this.settings = params.settings;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
    }
    updateStateVars(params: SettingsPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__settings.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__settings.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __settings: ObservedPropertyObjectPU<RobotSettings>;
    get settings() {
        return this.__settings.get();
    }
    set settings(newValue: RobotSettings) {
        this.__settings.set(newValue);
    }
    private __isLoading: ObservedPropertySimplePU<boolean>;
    get isLoading() {
        return this.__isLoading.get();
    }
    set isLoading(newValue: boolean) {
        this.__isLoading.set(newValue);
    }
    private __error: ObservedPropertySimplePU<string>;
    get error() {
        return this.__error.get();
    }
    set error(newValue: string) {
        this.__error.set(newValue);
    }
    aboutToAppear(): void {
        this.loadSettings();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(21:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/SettingsPage.ets(23:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/SettingsPage.ets(24:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => router.back());
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/SettingsPage.ets(28:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('设置');
            Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(29:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/SettingsPage.ets(31:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/SettingsPage.ets(32:9)", "entry");
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
                        Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(37:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        LoadingProgress.create();
                        LoadingProgress.debugLine("entry/src/main/ets/pages/SettingsPage.ets(38:11)", "entry");
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
                        Column.create({ space: 16 });
                        Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(42:9)", "entry");
                        Column.padding(16);
                        Column.width('100%');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 固件版本
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(44:11)", "entry");
                        // 固件版本
                        Column.width('100%');
                        // 固件版本
                        Column.alignItems(HorizontalAlign.Start);
                        // 固件版本
                        Column.padding(16);
                        // 固件版本
                        Column.borderRadius(8);
                        // 固件版本
                        Column.backgroundColor('#1a1a2e');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('固件版本');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(45:13)", "entry");
                        Text.fontSize(12);
                        Text.fontColor('#808080');
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.settings.firmwareVersion || '--');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(47:13)", "entry");
                        Text.fontSize(16);
                        Text.fontColor('#e0e0e0');
                        Text.margin({ top: 4 });
                    }, Text);
                    Text.pop();
                    // 固件版本
                    Column.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 序列号
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(54:11)", "entry");
                        // 序列号
                        Column.width('100%');
                        // 序列号
                        Column.alignItems(HorizontalAlign.Start);
                        // 序列号
                        Column.padding(16);
                        // 序列号
                        Column.borderRadius(8);
                        // 序列号
                        Column.backgroundColor('#1a1a2e');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('设备序列号');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(55:13)", "entry");
                        Text.fontSize(12);
                        Text.fontColor('#808080');
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.settings.serialNumber || '--');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(57:13)", "entry");
                        Text.fontSize(16);
                        Text.fontColor('#e0e0e0');
                        Text.margin({ top: 4 });
                    }, Text);
                    Text.pop();
                    // 序列号
                    Column.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 关于
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/SettingsPage.ets(64:11)", "entry");
                        // 关于
                        Column.width('100%');
                        // 关于
                        Column.alignItems(HorizontalAlign.Start);
                        // 关于
                        Column.padding(16);
                        // 关于
                        Column.borderRadius(8);
                        // 关于
                        Column.backgroundColor('#1a1a2e');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('关于');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(65:13)", "entry");
                        Text.fontSize(12);
                        Text.fontColor('#808080');
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('家庭服务机器人 v1.0.0');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(67:13)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#e0e0e0');
                        Text.margin({ top: 4 });
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('鸿蒙端 (HarmonyOS App)');
                        Text.debugLine("entry/src/main/ets/pages/SettingsPage.ets(69:13)", "entry");
                        Text.fontSize(12);
                        Text.fontColor('#606060');
                        Text.margin({ top: 2 });
                    }, Text);
                    Text.pop();
                    // 关于
                    Column.pop();
                    Column.pop();
                });
            }
        }, If);
        If.pop();
        Column.pop();
    }
    private async loadSettings(): Promise<void> {
        this.isLoading = true;
        try {
            let data: Record<string, Object> = await api.getSettings();
            this.settings = {
                firmwareVersion: data['firmwareVersion'] as string,
                serialNumber: data['serialNumber'] as string
            };
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
        return "SettingsPage";
    }
}
registerNamedRoute(() => new SettingsPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/SettingsPage", pageFullPath: "entry/src/main/ets/pages/SettingsPage", integratedHsp: "false", moduleType: "followWithHap" });
