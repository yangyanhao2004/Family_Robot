if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface VideoStream_Params {
    streamUrl?: string;
    pixelMap?: image.PixelMap | null;
    isLoading?: boolean;
    hasError?: boolean;
    retryCount?: number;
    frameTimer?: number | null;
    FRAME_INTERVAL?: number;
    MAX_RETRIES?: number;
}
import http from "@ohos:net.http";
import image from "@ohos:multimedia.image";
import { BACKEND_HTTP_URL } from "@bundle:com.familyrobot.harmonyos/entry/ets/common/Constants";
export class VideoStream extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__streamUrl = new SynchedPropertySimpleOneWayPU(params.streamUrl, this, "streamUrl");
        this.__pixelMap = new ObservedPropertyObjectPU(null, this, "pixelMap");
        this.__isLoading = new ObservedPropertySimplePU(false, this, "isLoading");
        this.__hasError = new ObservedPropertySimplePU(false, this, "hasError");
        this.__retryCount = new ObservedPropertySimplePU(0, this, "retryCount");
        this.frameTimer = null;
        this.FRAME_INTERVAL = 150 // ms
        ;
        this.MAX_RETRIES = 3;
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: VideoStream_Params) {
        if (params.streamUrl === undefined) {
            this.__streamUrl.set(BACKEND_HTTP_URL + '/video/stream');
        }
        if (params.pixelMap !== undefined) {
            this.pixelMap = params.pixelMap;
        }
        if (params.isLoading !== undefined) {
            this.isLoading = params.isLoading;
        }
        if (params.hasError !== undefined) {
            this.hasError = params.hasError;
        }
        if (params.retryCount !== undefined) {
            this.retryCount = params.retryCount;
        }
        if (params.frameTimer !== undefined) {
            this.frameTimer = params.frameTimer;
        }
        if (params.FRAME_INTERVAL !== undefined) {
            this.FRAME_INTERVAL = params.FRAME_INTERVAL;
        }
        if (params.MAX_RETRIES !== undefined) {
            this.MAX_RETRIES = params.MAX_RETRIES;
        }
    }
    updateStateVars(params: VideoStream_Params) {
        this.__streamUrl.reset(params.streamUrl);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__streamUrl.purgeDependencyOnElmtId(rmElmtId);
        this.__pixelMap.purgeDependencyOnElmtId(rmElmtId);
        this.__isLoading.purgeDependencyOnElmtId(rmElmtId);
        this.__hasError.purgeDependencyOnElmtId(rmElmtId);
        this.__retryCount.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__streamUrl.aboutToBeDeleted();
        this.__pixelMap.aboutToBeDeleted();
        this.__isLoading.aboutToBeDeleted();
        this.__hasError.aboutToBeDeleted();
        this.__retryCount.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __streamUrl: SynchedPropertySimpleOneWayPU<string>;
    get streamUrl() {
        return this.__streamUrl.get();
    }
    set streamUrl(newValue: string) {
        this.__streamUrl.set(newValue);
    }
    private __pixelMap: ObservedPropertyObjectPU<image.PixelMap | null>;
    get pixelMap() {
        return this.__pixelMap.get();
    }
    set pixelMap(newValue: image.PixelMap | null) {
        this.__pixelMap.set(newValue);
    }
    private __isLoading: ObservedPropertySimplePU<boolean>;
    get isLoading() {
        return this.__isLoading.get();
    }
    set isLoading(newValue: boolean) {
        this.__isLoading.set(newValue);
    }
    private __hasError: ObservedPropertySimplePU<boolean>;
    get hasError() {
        return this.__hasError.get();
    }
    set hasError(newValue: boolean) {
        this.__hasError.set(newValue);
    }
    private __retryCount: ObservedPropertySimplePU<number>;
    get retryCount() {
        return this.__retryCount.get();
    }
    set retryCount(newValue: number) {
        this.__retryCount.set(newValue);
    }
    private frameTimer: number | null;
    private readonly FRAME_INTERVAL: number; // ms
    private readonly MAX_RETRIES: number;
    aboutToAppear(): void {
        this.startFramePolling();
    }
    aboutToDisappear(): void {
        this.stopFramePolling();
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Stack.create();
            Stack.debugLine("entry/src/main/ets/components/VideoStream.ets(36:5)", "entry");
            Stack.width('100%');
            Stack.height('100%');
            Stack.backgroundColor('#0a0a0a');
        }, Stack);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 视频画面
            if (this.pixelMap !== null) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Image.create(this.pixelMap);
                        Image.debugLine("entry/src/main/ets/components/VideoStream.ets(39:9)", "entry");
                        Image.objectFit(ImageFit.Contain);
                        Image.width('100%');
                        Image.height('100%');
                    }, Image);
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        // 无画面时的占位
                        Column.create();
                        Column.debugLine("entry/src/main/ets/components/VideoStream.ets(45:9)", "entry");
                        // 无画面时的占位
                        Column.width('100%');
                        // 无画面时的占位
                        Column.height('100%');
                        // 无画面时的占位
                        Column.justifyContent(FlexAlign.Center);
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('📷');
                        Text.debugLine("entry/src/main/ets/components/VideoStream.ets(46:11)", "entry");
                        Text.fontSize(48);
                        Text.opacity(0.3);
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('等待视频流...');
                        Text.debugLine("entry/src/main/ets/components/VideoStream.ets(49:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#808080');
                        Text.margin({ top: 8 });
                    }, Text);
                    Text.pop();
                    // 无画面时的占位
                    Column.pop();
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 加载中遮罩
            if (this.isLoading && this.pixelMap === null) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/components/VideoStream.ets(61:9)", "entry");
                        Column.width('100%');
                        Column.height('100%');
                        Column.justifyContent(FlexAlign.Center);
                        Column.backgroundColor('rgba(0,0,0,0.7)');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        LoadingProgress.create();
                        LoadingProgress.debugLine("entry/src/main/ets/components/VideoStream.ets(62:11)", "entry");
                        LoadingProgress.width(40);
                        LoadingProgress.height(40);
                        LoadingProgress.color('#ffffff');
                    }, LoadingProgress);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('连接中...');
                        Text.debugLine("entry/src/main/ets/components/VideoStream.ets(66:11)", "entry");
                        Text.fontSize(13);
                        Text.fontColor('#c0c0c0');
                        Text.margin({ top: 8 });
                    }, Text);
                    Text.pop();
                    Column.pop();
                });
            }
            // 错误遮罩
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 错误遮罩
            if (this.hasError) {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Column.create();
                        Column.debugLine("entry/src/main/ets/components/VideoStream.ets(79:9)", "entry");
                        Column.width('100%');
                        Column.height('100%');
                        Column.justifyContent(FlexAlign.Center);
                        Column.backgroundColor('rgba(0,0,0,0.8)');
                    }, Column);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('⚠️');
                        Text.debugLine("entry/src/main/ets/components/VideoStream.ets(80:11)", "entry");
                        Text.fontSize(36);
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create('视频连接失败');
                        Text.debugLine("entry/src/main/ets/components/VideoStream.ets(82:11)", "entry");
                        Text.fontSize(14);
                        Text.fontColor('#ef4444');
                        Text.margin({ top: 6 });
                    }, Text);
                    Text.pop();
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Button.createWithLabel('重试');
                        Button.debugLine("entry/src/main/ets/components/VideoStream.ets(86:11)", "entry");
                        Button.fontSize(12);
                        Button.margin({ top: 10 });
                        Button.backgroundColor('#ef4444');
                        Button.borderRadius(6);
                        Button.onClick(() => {
                            this.hasError = false;
                            this.retryCount = 0;
                            this.startFramePolling();
                        });
                    }, Button);
                    Button.pop();
                    Column.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        Stack.pop();
    }
    /**
     * 启动帧轮询
     */
    private startFramePolling(): void {
        if (this.frameTimer !== null) {
            return;
        }
        this.isLoading = true;
        // 立即获取第一帧
        this.fetchFrame();
        // 定时获取后续帧
        this.frameTimer = setInterval(() => {
            this.fetchFrame();
        }, this.FRAME_INTERVAL);
    }
    /**
     * 停止帧轮询
     */
    private stopFramePolling(): void {
        if (this.frameTimer !== null) {
            clearInterval(this.frameTimer);
            this.frameTimer = null;
        }
        // 释放 PixelMap
        if (this.pixelMap !== null) {
            this.pixelMap.release();
            this.pixelMap = null;
        }
    }
    /**
     * 获取单帧 JPEG 图像
     */
    private async fetchFrame(): Promise<void> {
        try {
            // 使用 /video/stream 端点，配合短超时获取一帧
            let request: http.HttpRequest = http.createHttp();
            let response: http.HttpResponse = await request.request(this.streamUrl, {
                method: http.RequestMethod.GET,
                expectDataType: http.HttpDataType.ARRAY_BUFFER,
                connectTimeout: 3000,
                readTimeout: 5000
            });
            if (response.responseCode === 200 && response.result instanceof ArrayBuffer) {
                let imageData: ArrayBuffer = response.result as ArrayBuffer;
                await this.decodeAndRender(imageData);
                this.isLoading = false;
                this.hasError = false;
                this.retryCount = 0;
            }
            request.destroy();
        }
        catch (_err) {
            this.retryCount++;
            if (this.retryCount >= this.MAX_RETRIES) {
                this.isLoading = false;
                this.hasError = true;
                this.stopFramePolling();
            }
        }
    }
    /**
     * 解码 JPEG 数据为 PixelMap 并渲染
     */
    private async decodeAndRender(imageData: ArrayBuffer): Promise<void> {
        try {
            let imageSource: image.ImageSource = image.createImageSource(imageData);
            let decodeOptions: image.DecodingOptions = {
                desiredSize: { width: 640, height: 480 },
                desiredPixelFormat: image.PixelMapFormat.RGBA_8888
            };
            let newPm: image.PixelMap = await imageSource.createPixelMap(decodeOptions);
            // 释放旧 PixelMap
            if (this.pixelMap !== null) {
                this.pixelMap.release();
            }
            this.pixelMap = newPm;
            imageSource.release();
        }
        catch (_err) {
            // 解码失败，忽略此帧
        }
    }
    /**
     * 重置并重新开始
     */
    reset(newUrl?: string): void {
        this.stopFramePolling();
        if (newUrl) {
            this.streamUrl = newUrl;
        }
        this.hasError = false;
        this.retryCount = 0;
        this.startFramePolling();
    }
    rerender() {
        this.updateDirtyElements();
    }
}
