if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface ReminderPage_Params {
    reminders?: ReminderDto[];
    isLoading?: boolean;
    error?: string;
    showForm?: boolean;
    editId?: number;
    formText?: string;
    formScheduledTime?: string;
    formMethod?: string;
    formEmail?: string;
    formEnabled?: boolean;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
import type { ReminderDto } from '../model/Types';
class ReminderPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__reminders = new ObservedPropertyObjectPU([], this, "reminders");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.__error = new ObservedPropertySimplePU(''
        // 创建/编辑表单
        , this, "error");
        this.__showForm = new ObservedPropertySimplePU(false, this, "showForm");
        this.__editId = new ObservedPropertySimplePU(-1 // -1 = 新建
        , this, "editId");
        this.__formText = new ObservedPropertySimplePU('', this, "formText");
        this.__formScheduledTime = new ObservedPropertySimplePU('', this, "formScheduledTime");
        this.__formMethod = new ObservedPropertySimplePU('VOICE', this, "formMethod");
        this.__formEmail = new ObservedPropertySimplePU('', this, "formEmail");
        this.__formEnabled = new ObservedPropertySimplePU(true, this, "formEnabled");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: ReminderPage_Params) {
        if (params.reminders !== undefined) {
            this.reminders = params.reminders;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
        if (params.showForm !== undefined) {
            this.showForm = params.showForm;
        }
        if (params.editId !== undefined) {
            this.editId = params.editId;
        }
        if (params.formText !== undefined) {
            this.formText = params.formText;
        }
        if (params.formScheduledTime !== undefined) {
            this.formScheduledTime = params.formScheduledTime;
        }
        if (params.formMethod !== undefined) {
            this.formMethod = params.formMethod;
        }
        if (params.formEmail !== undefined) {
            this.formEmail = params.formEmail;
        }
        if (params.formEnabled !== undefined) {
            this.formEnabled = params.formEnabled;
        }
    }
    updateStateVars(params: ReminderPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__reminders.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
        this.__showForm.purgeDependencyOnElmtId(rmElmtId);
        this.__editId.purgeDependencyOnElmtId(rmElmtId);
        this.__formText.purgeDependencyOnElmtId(rmElmtId);
        this.__formScheduledTime.purgeDependencyOnElmtId(rmElmtId);
        this.__formMethod.purgeDependencyOnElmtId(rmElmtId);
        this.__formEmail.purgeDependencyOnElmtId(rmElmtId);
        this.__formEnabled.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__reminders.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        this.__showForm.aboutToBeDeleted();
        this.__editId.aboutToBeDeleted();
        this.__formText.aboutToBeDeleted();
        this.__formScheduledTime.aboutToBeDeleted();
        this.__formMethod.aboutToBeDeleted();
        this.__formEmail.aboutToBeDeleted();
        this.__formEnabled.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __reminders: ObservedPropertyObjectPU<ReminderDto[]>;
    get reminders() {
        return this.__reminders.get();
    }
    set reminders(newValue: ReminderDto[]) {
        this.__reminders.set(newValue);
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
    // 创建/编辑表单
    private __showForm: ObservedPropertySimplePU<boolean>;
    get showForm() {
        return this.__showForm.get();
    }
    set showForm(newValue: boolean) {
        this.__showForm.set(newValue);
    }
    private __editId: ObservedPropertySimplePU<number>; // -1 = 新建
    get editId() {
        return this.__editId.get();
    }
    set editId(newValue: number) {
        this.__editId.set(newValue);
    }
    private __formText: ObservedPropertySimplePU<string>;
    get formText() {
        return this.__formText.get();
    }
    set formText(newValue: string) {
        this.__formText.set(newValue);
    }
    private __formScheduledTime: ObservedPropertySimplePU<string>;
    get formScheduledTime() {
        return this.__formScheduledTime.get();
    }
    set formScheduledTime(newValue: string) {
        this.__formScheduledTime.set(newValue);
    }
    private __formMethod: ObservedPropertySimplePU<string>;
    get formMethod() {
        return this.__formMethod.get();
    }
    set formMethod(newValue: string) {
        this.__formMethod.set(newValue);
    }
    private __formEmail: ObservedPropertySimplePU<string>;
    get formEmail() {
        return this.__formEmail.get();
    }
    set formEmail(newValue: string) {
        this.__formEmail.set(newValue);
    }
    private __formEnabled: ObservedPropertySimplePU<boolean>;
    get formEnabled() {
        return this.__formEnabled.get();
    }
    set formEnabled(newValue: boolean) {
        this.__formEnabled.set(newValue);
    }
    aboutToAppear(): void {
        this.loadReminders();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/ReminderPage.ets(31:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(33:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(34:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => router.back());
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ReminderPage.ets(38:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('提醒');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(39:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/ReminderPage.ets(41:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('+ 新建');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(42:9)", "entry");
            Button.fontSize(13);
            Button.height(32);
            Button.padding({ left: 12, right: 12 });
            Button.backgroundColor('#3b82f6');
            Button.borderRadius(6);
            Button.fontColor('#ffffff');
            Button.onClick(() => { this.openCreateForm(); });
        }, Button);
        Button.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 新建/编辑表单
            if (this.showForm) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.BuildForm.bind(this)();
                });
            }
            // 提醒列表
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 提醒列表
            if (this.isLoading) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/ReminderPage.ets(57:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        LoadingProgress.create();
                        LoadingProgress.debugLine("entry/src/main/ets/pages/ReminderPage.ets(58:11)", "entry");
                        LoadingProgress.width(40);
                        LoadingProgress.height(40);
                        LoadingProgress.color('#3b82f6');
                    }, LoadingProgress);
                    Column.pop();
                });
            }
            else if (this.reminders.length === 0) {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/ReminderPage.ets(62:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('⏰');
                        Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(63:11)", "entry");
                        Text.fontSize(48);
                        Text.opacity(0.3);
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('暂无提醒');
                        Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(64:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#808080');
                        Text.margin({ top: 8 });
                    }, Text);
                    Text.pop();
                    Column.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(2, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        List.create();
                        List.debugLine("entry/src/main/ets/pages/ReminderPage.ets(68:9)", "entry");
                        List.layoutWeight(1);
                        List.width('100%');
                        List.backgroundColor('#0a0a1a');
                    }, List);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        ForEach.create();
                        const forEachItemGenFunction = _item => {
                            const item = _item;
                            {
                                const itemCreation = (elmtId, isInitialRender) => {
                                    ViewStackProcessor.StartGetAccessRecordingFor(elmtId);
                                    ListItem.create(deepRenderFunction, true);
                                    if (!isInitialRender) {
                                        ListItem.pop();
                                    }
                                    ViewStackProcessor.StopGetAccessRecording();
                                };
                                const itemCreation2 = (elmtId, isInitialRender) => {
                                    ListItem.create(deepRenderFunction, true);
                                    ListItem.debugLine("entry/src/main/ets/pages/ReminderPage.ets(70:13)", "entry");
                                };
                                const deepRenderFunction = (elmtId, isInitialRender) => {
                                    itemCreation(elmtId, isInitialRender);
                                    this.BuildReminderItem.bind(this)(item);
                                    ListItem.pop();
                                };
                                this.observeComponentCreation2(itemCreation2, ListItem);
                                ListItem.pop();
                            }
                        };
                        this.forEachUpdateFunction(elmtId, this.reminders, forEachItemGenFunction);
                    }, ForEach);
                    ForEach.pop();
                    List.pop();
                });
            }
        }, If);
        If.pop();
        Column.pop();
    }
    BuildForm(parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create({ space: 10 });
            Column.debugLine("entry/src/main/ets/pages/ReminderPage.ets(86:5)", "entry");
            Column.width('100%');
            Column.padding(16);
            Column.backgroundColor('#12122a');
            Column.borderRadius(8);
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(this.editId === -1 ? '新建提醒' : '编辑提醒');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(87:7)", "entry");
            Text.fontSize(15);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextInput.create({ placeholder: '提醒内容', text: this.formText });
            TextInput.debugLine("entry/src/main/ets/pages/ReminderPage.ets(90:7)", "entry");
            TextInput.width('100%');
            TextInput.height(42);
            TextInput.backgroundColor('#1a1a2e');
            TextInput.borderRadius(6);
            TextInput.border({ width: 1, color: '#333333' });
            TextInput.fontColor('#e0e0e0');
            TextInput.placeholderColor('#606060');
            TextInput.fontSize(14);
            TextInput.onChange((v: string) => { this.formText = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 日期时间选择
            TextInput.create({ placeholder: '时间 (YYYY-MM-DD HH:MM)', text: this.formScheduledTime });
            TextInput.debugLine("entry/src/main/ets/pages/ReminderPage.ets(99:7)", "entry");
            // 日期时间选择
            TextInput.width('100%');
            // 日期时间选择
            TextInput.height(42);
            // 日期时间选择
            TextInput.backgroundColor('#1a1a2e');
            // 日期时间选择
            TextInput.borderRadius(6);
            // 日期时间选择
            TextInput.border({ width: 1, color: '#333333' });
            // 日期时间选择
            TextInput.fontColor('#e0e0e0');
            // 日期时间选择
            TextInput.placeholderColor('#606060');
            // 日期时间选择
            TextInput.fontSize(14);
            // 日期时间选择
            TextInput.onChange((v: string) => { this.formScheduledTime = v; });
        }, TextInput);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 通知方式
            Row.create({ space: 16 });
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(108:7)", "entry");
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('通知方式:');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(109:9)", "entry");
            Text.fontSize(13);
            Text.fontColor('#a0a0a0');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(110:9)", "entry");
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Radio.create({ value: 'VOICE', group: 'method' });
            Radio.debugLine("entry/src/main/ets/pages/ReminderPage.ets(111:11)", "entry");
            Radio.checked(this.formMethod === 'VOICE');
            Radio.onChange((_checked: boolean) => { this.formMethod = 'VOICE'; });
        }, Radio);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('语音');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(114:11)", "entry");
            Text.fontSize(13);
            Text.fontColor('#c0c0c0');
        }, Text);
        Text.pop();
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(116:9)", "entry");
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Radio.create({ value: 'EMAIL', group: 'method' });
            Radio.debugLine("entry/src/main/ets/pages/ReminderPage.ets(117:11)", "entry");
            Radio.checked(this.formMethod === 'EMAIL');
            Radio.onChange((_checked: boolean) => { this.formMethod = 'EMAIL'; });
        }, Radio);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('邮件');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(120:11)", "entry");
            Text.fontSize(13);
            Text.fontColor('#c0c0c0');
        }, Text);
        Text.pop();
        Row.pop();
        // 通知方式
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.formMethod === 'EMAIL') {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        TextInput.create({ placeholder: '邮件地址', text: this.formEmail });
                        TextInput.debugLine("entry/src/main/ets/pages/ReminderPage.ets(125:9)", "entry");
                        TextInput.width('100%');
                        TextInput.height(42);
                        TextInput.backgroundColor('#1a1a2e');
                        TextInput.borderRadius(6);
                        TextInput.border({ width: 1, color: '#333333' });
                        TextInput.fontColor('#e0e0e0');
                        TextInput.placeholderColor('#606060');
                        TextInput.fontSize(14);
                        TextInput.type(InputType.Email);
                        TextInput.onChange((v: string) => { this.formEmail = v; });
                    }, TextInput);
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create({ space: 10 });
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(134:7)", "entry");
            Row.width('100%');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('取消');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(135:9)", "entry");
            Button.fontSize(13);
            Button.height(36);
            Button.layoutWeight(1);
            Button.backgroundColor('#333333');
            Button.borderRadius(6);
            Button.fontColor('#c0c0c0');
            Button.onClick(() => { this.showForm = false; });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('保存');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(141:9)", "entry");
            Button.fontSize(13);
            Button.height(36);
            Button.layoutWeight(1);
            Button.backgroundColor('#3b82f6');
            Button.borderRadius(6);
            Button.fontColor('#ffffff');
            Button.onClick(() => { this.saveReminder(); });
        }, Button);
        Button.pop();
        Row.pop();
        Column.pop();
    }
    BuildReminderItem(item: ReminderDto, parent = null) {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(157:5)", "entry");
            Row.width('100%');
            Row.padding({ left: 14, right: 8, top: 10, bottom: 10 });
            Row.border({ width: { bottom: 0.5 }, color: '#222' });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/ReminderPage.ets(158:7)", "entry");
            Column.alignItems(HorizontalAlign.Start);
            Column.layoutWeight(1);
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(item.text);
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(159:9)", "entry");
            Text.fontSize(14);
            Text.fontColor('#e0e0e0');
            Text.maxLines(2);
            Text.textOverflow({ overflow: TextOverflow.Ellipsis });
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create({ space: 8 });
            Row.debugLine("entry/src/main/ets/pages/ReminderPage.ets(162:9)", "entry");
            Row.margin({ top: 4 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(item.scheduledTime);
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(163:11)", "entry");
            Text.fontSize(11);
            Text.fontColor('#808080');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create(item.method === 'VOICE' ? '🔊语音' : '📧邮件');
            Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(165:11)", "entry");
            Text.fontSize(10);
            Text.fontColor('#606060');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (item.sent) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('已发送');
                        Text.debugLine("entry/src/main/ets/pages/ReminderPage.ets(168:13)", "entry");
                        Text.fontSize(10);
                        Text.fontColor('#10b981');
                        Text.padding({ left: 6, right: 6, top: 1, bottom: 1 });
                        Text.backgroundColor('#1a2a1a');
                        Text.borderRadius(4);
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
        Row.pop();
        Column.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 启用开关
            Toggle.create({ type: ToggleType.Switch, isOn: item.enabled });
            Toggle.debugLine("entry/src/main/ets/pages/ReminderPage.ets(180:7)", "entry");
            // 启用开关
            Toggle.width(36);
            // 启用开关
            Toggle.height(20);
            // 启用开关
            Toggle.onChange((isOn: boolean) => {
                let data: Record<string, Object> = { 'enabled': isOn };
                api.updateReminder(item.id, data);
            });
        }, Toggle);
        // 启用开关
        Toggle.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 编辑
            Button.createWithLabel('✏️');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(188:7)", "entry");
            // 编辑
            Button.fontSize(12);
            // 编辑
            Button.width(32);
            // 编辑
            Button.height(32);
            // 编辑
            Button.backgroundColor('transparent');
            // 编辑
            Button.onClick(() => { this.openEditForm(item); });
        }, Button);
        // 编辑
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 删除
            Button.createWithLabel('🗑');
            Button.debugLine("entry/src/main/ets/pages/ReminderPage.ets(194:7)", "entry");
            // 删除
            Button.fontSize(12);
            // 删除
            Button.width(32);
            // 删除
            Button.height(32);
            // 删除
            Button.backgroundColor('transparent');
            // 删除
            Button.onClick(() => { this.deleteReminder(item.id); });
        }, Button);
        // 删除
        Button.pop();
        Row.pop();
    }
    private async loadReminders(): Promise<void> {
        this.isLoading = true;
        try {
            let userId: number = authManager.getUserIdFromToken();
            let data: Array<Record<string, Object>> = await api.getReminders(userId);
            this.reminders = data.map((item: Record<string, Object>): ReminderDto => {
                return {
                    id: item['id'] as number,
                    text: item['text'] as string,
                    scheduledTime: item['scheduledTime'] as string,
                    method: item['method'] as 'EMAIL' | 'VOICE',
                    email: item['email'] as string | null,
                    enabled: item['enabled'] as boolean,
                    sent: item['sent'] as boolean
                };
            });
        }
        catch (err) {
            this.error = (err as Error).message;
        }
        finally {
            this.isLoading = false;
        }
    }
    private openCreateForm(): void {
        this.editId = -1;
        this.formText = '';
        // 默认5分钟后
        let now: Date = new Date(Date.now() + 300000);
        this.formScheduledTime = this.formatDateTime(now);
        this.formMethod = 'VOICE';
        this.formEmail = '';
        this.formEnabled = true;
        this.showForm = true;
    }
    private openEditForm(item: ReminderDto): void {
        this.editId = item.id;
        this.formText = item.text;
        this.formScheduledTime = item.scheduledTime;
        this.formMethod = item.method;
        this.formEmail = item.email || '';
        this.formEnabled = item.enabled;
        this.showForm = true;
    }
    private async saveReminder(): Promise<void> {
        if (this.formText.trim().length === 0)
            return;
        let data: Record<string, Object> = {
            'userId': authManager.getUserIdFromToken(),
            'text': this.formText.trim(),
            'scheduledTime': this.formScheduledTime,
            'method': this.formMethod,
            'email': this.formMethod === 'EMAIL' ? this.formEmail : '',
            'enabled': this.formEnabled
        };
        try {
            if (this.editId === -1) {
                await api.createReminder(data);
            }
            else {
                await api.updateReminder(this.editId, data);
            }
            this.showForm = false;
            this.loadReminders();
        }
        catch (err) {
            // 错误处理
        }
    }
    private async deleteReminder(id: number): Promise<void> {
        try {
            await api.deleteReminder(id);
            this.loadReminders();
        }
        catch (_err) { /* 忽略 */ }
    }
    private formatDateTime(date: Date): string {
        let y: string = date.getFullYear().toString();
        let mo: string = (date.getMonth() + 1).toString().padStart(2, '0');
        let d: string = date.getDate().toString().padStart(2, '0');
        let h: string = date.getHours().toString().padStart(2, '0');
        let mi: string = date.getMinutes().toString().padStart(2, '0');
        return y + '-' + mo + '-' + d + ' ' + h + ':' + mi;
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "ReminderPage";
    }
}
registerNamedRoute(() => new ReminderPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/ReminderPage", pageFullPath: "entry/src/main/ets/pages/ReminderPage", integratedHsp: "false", moduleType: "followWithHap" });
