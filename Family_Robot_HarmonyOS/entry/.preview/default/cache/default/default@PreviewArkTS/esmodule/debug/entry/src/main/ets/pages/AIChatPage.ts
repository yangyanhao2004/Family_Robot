if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface AIChatPage_Params {
    messages?: ChatMessage[];
    inputText?: string;
    isSending?: boolean;
    scroller?: Scroller;
    msgCounter?: number;
    wsListener?: (msg: WebSocketMessage) => void;
}
import router from "@ohos:router";
import { webSocketService } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/WebSocketService";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
import { ChatBubble } from "@bundle:com.familyrobot.harmonyos/entry/ets/components/ChatBubble";
import type { ChatMessage, WebSocketMessage, AIChatResponse } from '../model/Types';
class AIChatPage extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__messages = new ObservedPropertyObjectPU([], this, "messages");
        this.__inputText = new ObservedPropertySimplePU('', this, "inputText");
        this.__isSending = new ObservedPropertySimplePU(false, this, "isSending");
        this.scroller = new Scroller();
        this.msgCounter = 0;
        this.wsListener = (_msg: WebSocketMessage) => { };
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: AIChatPage_Params) {
        if (params.messages !== undefined) {
            this.messages = params.messages;
        }
        if (params.inputText !== undefined) {
            this.inputText = params.inputText;
        }
        if (params.isSending !== undefined) {
            this.isSending = params.isSending;
        }
        if (params.scroller !== undefined) {
            this.scroller = params.scroller;
        }
        if (params.msgCounter !== undefined) {
            this.msgCounter = params.msgCounter;
        }
        if (params.wsListener !== undefined) {
            this.wsListener = params.wsListener;
        }
    }
    updateStateVars(params: AIChatPage_Params) {
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__messages.purgeDependencyOnElmtId(rmElmtId);
        this.__inputText.purgeDependencyOnElmtId(rmElmtId);
        this.__isSending.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__messages.aboutToBeDeleted();
        this.__inputText.aboutToBeDeleted();
        this.__isSending.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __messages: ObservedPropertyObjectPU<ChatMessage[]>;
    get messages() {
        return this.__messages.get();
    }
    set messages(newValue: ChatMessage[]) {
        this.__messages.set(newValue);
    }
    private __inputText: ObservedPropertySimplePU<string>;
    get inputText() {
        return this.__inputText.get();
    }
    set inputText(newValue: string) {
        this.__inputText.set(newValue);
    }
    private __isSending: ObservedPropertySimplePU<boolean>;
    get isSending() {
        return this.__isSending.get();
    }
    set isSending(newValue: boolean) {
        this.__isSending.set(newValue);
    }
    private scroller: Scroller;
    private msgCounter: number;
    private wsListener: (msg: WebSocketMessage) => void;
    aboutToAppear(): void {
        this.wsListener = (msg: WebSocketMessage) => {
            if (msg.type === 'ai_chat_response' && msg.payload) {
                let payload: Record<string, Object> = msg.payload;
                let response: AIChatResponse = {
                    text: (payload['text'] as string) || '',
                    action: (payload['action'] as 'chat_reply' | 'control_robot' | 'set_reminder') || 'chat_reply',
                    data: payload['data'] as Record<string, Object> | undefined
                };
                this.addAssistantMessage(response);
                this.isSending = false;
            }
        };
        webSocketService.addMessageListener(this.wsListener);
    }
    aboutToDisappear(): void {
        webSocketService.removeMessageListener(this.wsListener);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/pages/AIChatPage.ets(43:5)", "entry");
            Column.width('100%');
            Column.height('100%');
            Column.backgroundColor('#0a0a1a');
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 标题栏
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/AIChatPage.ets(45:7)", "entry");
            // 标题栏
            Row.width('100%');
            // 标题栏
            Row.padding(16);
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('← 返回');
            Button.debugLine("entry/src/main/ets/pages/AIChatPage.ets(46:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#808080');
            Button.backgroundColor('transparent');
            Button.onClick(() => {
                // 结束AI会话
                webSocketService.sendAISessionEnd(authManager.getUserIdFromToken());
                router.back();
            });
        }, Button);
        Button.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/AIChatPage.ets(54:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Text.create('AI 对话');
            Text.debugLine("entry/src/main/ets/pages/AIChatPage.ets(55:9)", "entry");
            Text.fontSize(18);
            Text.fontColor('#ffffff');
        }, Text);
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Blank.create();
            Blank.debugLine("entry/src/main/ets/pages/AIChatPage.ets(57:9)", "entry");
        }, Blank);
        Blank.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/pages/AIChatPage.ets(58:9)", "entry");
            Row.width(60);
        }, Row);
        Row.pop();
        // 标题栏
        Row.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 消息列表
            List.create({ scroller: this.scroller });
            List.debugLine("entry/src/main/ets/pages/AIChatPage.ets(63:7)", "entry");
            // 消息列表
            List.layoutWeight(1);
            // 消息列表
            List.width('100%');
            // 消息列表
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
                        ListItem.debugLine("entry/src/main/ets/pages/AIChatPage.ets(65:11)", "entry");
                    };
                    const deepRenderFunction = (elmtId, isInitialRender) => {
                        itemCreation(elmtId, isInitialRender);
                        {
                            this.observeComponentCreation2((elmtId, isInitialRender) => {
                                if (isInitialRender) {
                                    let componentCall = new ChatBubble(this, { message: item }, undefined, elmtId, () => { }, { page: "entry/src/main/ets/pages/AIChatPage.ets", line: 66, col: 13 });
                                    ViewPU.create(componentCall);
                                    let paramsLambda = () => {
                                        return {
                                            message: item
                                        };
                                    };
                                    componentCall.paramsGenerator_ = paramsLambda;
                                }
                                else {
                                    this.updateStateVarsOfChildByElmtId(elmtId, {
                                        message: item
                                    });
                                }
                            }, { name: "ChatBubble" });
                        }
                        ListItem.pop();
                    };
                    this.observeComponentCreation2(itemCreation2, ListItem);
                    ListItem.pop();
                }
            };
            this.forEachUpdateFunction(elmtId, this.messages, forEachItemGenFunction);
        }, ForEach);
        ForEach.pop();
        // 消息列表
        List.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 发送区域
            Row.create({ space: 10 });
            Row.debugLine("entry/src/main/ets/pages/AIChatPage.ets(75:7)", "entry");
            // 发送区域
            Row.width('100%');
            // 发送区域
            Row.padding({ left: 12, right: 12, top: 8, bottom: 12 });
            // 发送区域
            Row.backgroundColor('#12122a');
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            TextArea.create({ placeholder: '输入消息... (Enter发送)', text: this.inputText });
            TextArea.debugLine("entry/src/main/ets/pages/AIChatPage.ets(76:9)", "entry");
            TextArea.layoutWeight(1);
            TextArea.height(44);
            TextArea.maxLength(500);
            TextArea.backgroundColor('#1a1a2e');
            TextArea.borderRadius(8);
            TextArea.border({ width: 1, color: '#333333' });
            TextArea.fontColor('#e0e0e0');
            TextArea.placeholderColor('#606060');
            TextArea.fontSize(14);
            TextArea.padding({ left: 12, right: 12, top: 10, bottom: 10 });
            TextArea.onChange((v: string) => { this.inputText = v; });
            TextArea.onKeyEvent((event) => {
                // Enter 键发送 (keyCode 2054=Enter, type 0=Down)
                if (event.keyCode === 2054 && event.type === 0) {
                    this.sendMessage();
                }
            });
        }, TextArea);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Button.createWithLabel('发送');
            Button.debugLine("entry/src/main/ets/pages/AIChatPage.ets(95:9)", "entry");
            Button.fontSize(14);
            Button.fontColor('#ffffff');
            Button.height(44);
            Button.padding({ left: 16, right: 16 });
            Button.backgroundColor('#3b82f6');
            Button.borderRadius(8);
            Button.enabled(!this.isSending && this.inputText.trim().length > 0);
            Button.onClick(() => { this.sendMessage(); });
        }, Button);
        Button.pop();
        // 发送区域
        Row.pop();
        Column.pop();
    }
    private sendMessage(): void {
        let text: string = this.inputText.trim();
        if (text.length === 0 || this.isSending)
            return;
        // 添加用户消息
        this.msgCounter++;
        this.messages = [...this.messages, {
                id: 'msg_' + this.msgCounter,
                role: 'user',
                content: text,
                timestamp: Date.now()
            }];
        this.inputText = '';
        this.isSending = true;
        // 滚动到底部
        setTimeout(() => {
            this.scroller.scrollToIndex(this.messages.length - 1, true);
        }, 100);
        // 通过 WebSocket 发送
        let userId: number = authManager.getUserIdFromToken();
        webSocketService.sendAIChat(userId, text);
    }
    private addAssistantMessage(response: AIChatResponse): void {
        this.msgCounter++;
        this.messages = [...this.messages, {
                id: 'msg_' + this.msgCounter,
                role: 'assistant',
                content: response.text,
                action: response.action,
                data: response.data,
                timestamp: Date.now()
            }];
        // 滚动到底部
        setTimeout(() => {
            this.scroller.scrollToIndex(this.messages.length - 1, true);
        }, 100);
    }
    rerender() {
        this.updateDirtyElements();
    }
    static getEntryName(): string {
        return "AIChatPage";
    }
}
registerNamedRoute(() => new AIChatPage(undefined, {}), "", { bundleName: "com.familyrobot.harmonyos", moduleName: "entry", pagePath: "pages/AIChatPage", pageFullPath: "entry/src/main/ets/pages/AIChatPage", integratedHsp: "false", moduleType: "followWithHap" });
