if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface AlbumPage_Params {
    photos?: AlbumPhoto[];
    isLoading?: boolean;
    error?: string;
    selectedIds?: Set<string>;
}
import router from "@ohos:router";
import { api } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/ApiService";
import type { AlbumPhoto } from '../model/Types';
class AlbumPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__photos = new ObservedPropertyObjectPU([], this, "photos");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.__error = new ObservedPropertySimplePU('', this, "error");
        this.__selectedIds = new ObservedPropertyObjectPU(new Set(), this, "selectedIds");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: AlbumPage_Params) {
        if (params.photos !== undefined) {
            this.photos = params.photos;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
        if (params.error !== undefined) {
            this.error = params.error;
        }
        if (params.selectedIds !== undefined) {
            this.selectedIds = params.selectedIds;
        }
    }
    updateStateVars(params: AlbumPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__photos.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
        this.__error.purgeDependencyOnElmtId(rmElmtId);
        this.__selectedIds.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__photos.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        this.__error.aboutToBeDeleted();
        this.__selectedIds.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __photos: ObservedPropertyObjectPU<AlbumPhoto[]>;
    get photos() {
        return this.__photos.get();
    }
    set photos(newValue: AlbumPhoto[]) {
        this.__photos.set(newValue);
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
    private __selectedIds: ObservedPropertyObjectPU<Set<string>>;
    get selectedIds() {
        return this.__selectedIds.get();
    }
    set selectedIds(newValue: Set<string>) {
        this.__selectedIds.set(newValue);
    }
    aboutToAppear(): void {
        this.loadPhotos();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/AlbumPage.ets(22:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/AlbumPage.ets(24:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/AlbumPage.ets(25:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => router.back());
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/AlbumPage.ets(29:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('相册');
            Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(30:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/AlbumPage.ets(32:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.selectedIds.size > 0) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 选中操作栏
                        Row.create({ space: 10 });
                        Row.debugLine("entry/src/main/ets/pages/AlbumPage.ets(36:11)", "entry");
                    }, Row);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('已选 ' + this.selectedIds.size);
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(37:13)", "entry");
                        Text.fontSize(13);
                        Text.fontColor('#a0a0a0');
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('下载');
                        Button.debugLine("entry/src/main/ets/pages/AlbumPage.ets(40:13)", "entry");
                        Button.fontSize(12);
                        Button.height(30);
                        Button.padding({ left: 10, right: 10 });
                        Button.backgroundColor('#0f3460');
                        Button.borderRadius(6);
                        Button.fontColor('#ffffff');
                        Button.onClick(() => { this.downloadSelected(); });
                    }, Button);
                    Button.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('删除');
                        Button.debugLine("entry/src/main/ets/pages/AlbumPage.ets(46:13)", "entry");
                        Button.fontSize(12);
                        Button.height(30);
                        Button.padding({ left: 10, right: 10 });
                        Button.backgroundColor('#7f1d1d');
                        Button.borderRadius(6);
                        Button.fontColor('#ffffff');
                        Button.onClick(() => { this.deleteSelected(); });
                    }, Button);
                    Button.pop();
                    // 选中操作栏
                    Row.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Row.create();
                        Row.debugLine("entry/src/main/ets/pages/AlbumPage.ets(53:11)", "entry");
                        Row.width(60);
                    }, Row);
                    Row.pop();
                });
            }
        }, If);
        If.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 内容
            if (this.isLoading) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/AlbumPage.ets(60:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        LoadingProgress.create();
                        LoadingProgress.debugLine("entry/src/main/ets/pages/AlbumPage.ets(61:11)", "entry");
                        LoadingProgress.width(40);
                        LoadingProgress.height(40);
                        LoadingProgress.color('#3b82f6');
                    }, LoadingProgress);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('加载中...');
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(62:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#808080');
                        Text.margin({ top: 12 });
                    }, Text);
                    Text.pop();
                    Column.pop();
                });
            }
            else if (this.error.length > 0) {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/AlbumPage.ets(66:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('⚠️');
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(67:11)", "entry");
                        Text.fontSize(40);
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.error);
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(68:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#ef4444');
                        Text.margin({ top: 8 });
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('重试');
                        Button.debugLine("entry/src/main/ets/pages/AlbumPage.ets(69:11)", "entry");
                        Button.fontSize(13);
                        Button.margin({ top: 16 });
                        Button.backgroundColor('#3b82f6');
                        Button.borderRadius(6);
                        Button.onClick(() => this.loadPhotos());
                    }, Button);
                    Button.pop();
                    Column.pop();
                });
            }
            else if (this.photos.length === 0) {
                this.ifElseBranchUpdateFunction(2, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/pages/AlbumPage.ets(76:9)", "entry");
                        Column.width('100%');
                        Column.layoutWeight(1);
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('📷');
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(77:11)", "entry");
                        Text.fontSize(48);
                        Text.opacity(0.3);
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('暂无照片');
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(78:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#808080');
                        Text.margin({ top: 8 });
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('在主控面板点击拍照按钮拍照');
                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(79:11)", "entry");
                        Text.fontSize(12);
                        Text.fontColor('#606060');
                        Text.margin({ top: 4 });
                    }, Text);
                    Text.pop();
                    Column.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(3, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 照片网格
                        Grid.create();
                        Grid.debugLine("entry/src/main/ets/pages/AlbumPage.ets(84:9)", "entry");
                        // 照片网格
                        Grid.columnsTemplate('1fr 1fr 1fr');
                        // 照片网格
                        Grid.columnsGap(8);
                        // 照片网格
                        Grid.rowsGap(8);
                        // 照片网格
                        Grid.padding(12);
                        // 照片网格
                        Grid.layoutWeight(1);
                        // 照片网格
                        Grid.width('100%');
                        // 照片网格
                        Grid.backgroundColor('#0a0a1a');
                    }, Grid);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        ForEach.create();
                        const forEachItemGenFunction = _item => {
                            const photo = _item;
                            {
                                const itemCreation2 = (elmtId, isInitialRender) => {
                                    GridItem.create(() => { }, false);
                                    GridItem.debugLine("entry/src/main/ets/pages/AlbumPage.ets(86:13)", "entry");
                                };
                                const observedDeepRender = () => {
                                    this.observeComponentCreation2(itemCreation2, GridItem);
                                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                                        Stack.create();
                                        Stack.debugLine("entry/src/main/ets/pages/AlbumPage.ets(87:15)", "entry");
                                        Stack.onClick(() => { this.toggleSelect(photo.id); });
                                    }, Stack);
                                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                                        // 照片缩略图
                                        Image.create(photo.url);
                                        Image.debugLine("entry/src/main/ets/pages/AlbumPage.ets(89:17)", "entry");
                                        // 照片缩略图
                                        Image.objectFit(ImageFit.Cover);
                                        // 照片缩略图
                                        Image.width('100%');
                                        // 照片缩略图
                                        Image.height(120);
                                        // 照片缩略图
                                        Image.borderRadius(8);
                                    }, Image);
                                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                                        If.create();
                                        // 选中标记
                                        if (this.selectedIds.has(photo.id)) {
                                            this.ifElseBranchUpdateFunction(0, () => {
                                                this.observeComponentCreation2((elmtId, isInitialRender) => {
                                                    Row.create();
                                                    Row.debugLine("entry/src/main/ets/pages/AlbumPage.ets(97:19)", "entry");
                                                    Row.width(28);
                                                    Row.height(28);
                                                    Row.borderRadius(14);
                                                    Row.backgroundColor('#3b82f6');
                                                    Row.justifyContent(FlexAlign.Center);
                                                    Row.position({ right: 6, top: 6 });
                                                }, Row);
                                                this.observeComponentCreation2((elmtId, isInitialRender) => {
                                                    Text.create('✓');
                                                    Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(98:21)", "entry");
                                                    Text.fontSize(14);
                                                    Text.fontColor('#ffffff');
                                                }, Text);
                                                Text.pop();
                                                Row.pop();
                                            });
                                        }
                                        // 日期
                                        else {
                                            this.ifElseBranchUpdateFunction(1, () => {
                                            });
                                        }
                                    }, If);
                                    If.pop();
                                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                                        // 日期
                                        Text.create(photo.date);
                                        Text.debugLine("entry/src/main/ets/pages/AlbumPage.ets(109:17)", "entry");
                                        // 日期
                                        Text.fontSize(10);
                                        // 日期
                                        Text.fontColor('#c0c0c0');
                                        // 日期
                                        Text.padding({ left: 6, right: 6, top: 2, bottom: 2 });
                                        // 日期
                                        Text.backgroundColor('rgba(0,0,0,0.6)');
                                        // 日期
                                        Text.borderRadius(4);
                                        // 日期
                                        Text.position({ left: 6, bottom: 6 });
                                    }, Text);
                                    // 日期
                                    Text.pop();
                                    Stack.pop();
                                    GridItem.pop();
                                };
                                observedDeepRender();
                            }
                        };
                        this.forEachUpdateFunction(elmtId, this.photos, forEachItemGenFunction);
                    }, ForEach);
                    ForEach.pop();
                    // 照片网格
                    Grid.pop();
                });
            }
        }, If);
        If.pop();
        Column.pop();
    }
    private async loadPhotos(): Promise<void> {
        this.isLoading = true;
        this.error = '';
        try {
            let data: Array<Record<string, Object>> = await api.getPhotos();
            this.photos = data.map((item: Record<string, Object>): AlbumPhoto => {
                return {
                    id: item['id'] as string,
                    url: item['url'] as string,
                    date: item['date'] as string
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
    private toggleSelect(id: string): void {
        if (this.selectedIds.has(id)) {
            this.selectedIds.delete(id);
        }
        else {
            this.selectedIds.add(id);
        }
        // 触发状态更新
        this.selectedIds = new Set(this.selectedIds);
    }
    private async deleteSelected(): Promise<void> {
        for (let id of this.selectedIds) {
            try {
                await api.deletePhoto(id);
            }
            catch (_err) { /* 继续 */ }
        }
        this.selectedIds = new Set();
        this.loadPhotos();
    }
    private downloadSelected(): void {
        // 鸿蒙端下载到本地相册较复杂，简化处理
        // 可在后续完善
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "AlbumPage";
    }
}
registerNamedRoute(() => new AlbumPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/AlbumPage", pageFullPath: "entry/src/main/ets/pages/AlbumPage", integratedHsp: "false", moduleType: "followWithHap" });
