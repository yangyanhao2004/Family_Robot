if (!("finalizeConstruction" in ViewPU.prototype)) {
    Reflect.set(ViewPU.prototype, "finalizeConstruction", () => { });
}
interface ChatBubble_Params {
    message?: ChatMessage;
}
import type { ChatMessage } from '../model/Types';
export class ChatBubble extends ViewPU {
    constructor(parent, params, __localStorage, elmtId = -1, paramsLambda = undefined, extraInfo) {
        super(parent, __localStorage, elmtId, extraInfo);
        if (typeof paramsLambda === "function") {
            this.paramsGenerator_ = paramsLambda;
        }
        this.__message = new SynchedPropertyObjectOneWayPU(params.message, this, "message");
        this.setInitiallyProvidedValue(params);
        this.finalizeConstruction();
    }
    setInitiallyProvidedValue(params: ChatBubble_Params) {
        if (params.message === undefined) {
            this.__message.set({
                id: '',
                role: 'user',
                content: '',
                timestamp: 0,
                action: undefined,
                data: undefined
            });
        }
    }
    updateStateVars(params: ChatBubble_Params) {
        this.__message.reset(params.message);
    }
    purgeVariableDependenciesOnElmtId(rmElmtId) {
        this.__message.purgeDependencyOnElmtId(rmElmtId);
    }
    aboutToBeDeleted() {
        this.__message.aboutToBeDeleted();
        SubscriberManager.Get().delete(this.id__());
        this.aboutToBeDeletedInternal();
    }
    private __message: SynchedPropertySimpleOneWayPU<ChatMessage>;
    get message() {
        return this.__message.get();
    }
    set message(newValue: ChatMessage) {
        this.__message.set(newValue);
    }
    initialRender() {
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Row.create();
            Row.debugLine("entry/src/main/ets/components/ChatBubble.ets(18:5)", "entry");
            Row.width('100%');
            Row.padding({ left: 8, right: 8, top: 4, bottom: 4 });
        }, Row);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.message.role === 'user') {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Blank.create();
                        Blank.debugLine("entry/src/main/ets/components/ChatBubble.ets(20:9)", "entry");
                    }, Blank);
                    Blank.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            Column.create();
            Column.debugLine("entry/src/main/ets/components/ChatBubble.ets(23:7)", "entry");
            Column.alignItems(this.message.role === 'user' ? HorizontalAlign.End : HorizontalAlign.Start);
        }, Column);
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 消息文本
            Text.create(this.message.content);
            Text.debugLine("entry/src/main/ets/components/ChatBubble.ets(25:9)", "entry");
            // 消息文本
            Text.fontSize(15);
            // 消息文本
            Text.fontColor('#e0e0e0');
            // 消息文本
            Text.padding(12);
            // 消息文本
            Text.borderRadius(12);
            // 消息文本
            Text.backgroundColor(this.message.role === 'user' ? '#0f3460' : '#1e3a5f');
            // 消息文本
            Text.constraintSize({ maxWidth: '75%' });
            // 消息文本
            Text.textAlign(TextAlign.Start);
        }, Text);
        // 消息文本
        Text.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            // 操作标签
            if (this.message.action && this.message.action !== 'chat_reply') {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Row.create();
                        Row.debugLine("entry/src/main/ets/components/ChatBubble.ets(36:11)", "entry");
                        Row.margin({ top: 4 });
                    }, Row);
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Text.create(this.getActionLabel());
                        Text.debugLine("entry/src/main/ets/components/ChatBubble.ets(37:13)", "entry");
                        Text.fontSize(11);
                        Text.fontColor('#ffffff');
                        Text.padding({ left: 8, right: 8, top: 2, bottom: 2 });
                        Text.borderRadius(8);
                        Text.backgroundColor(this.message.action === 'control_robot' ? '#059669' : '#7c3aed');
                    }, Text);
                    Text.pop();
                    Row.pop();
                });
            }
            // 时间
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            // 时间
            Text.create(this.formatTime(this.message.timestamp));
            Text.debugLine("entry/src/main/ets/components/ChatBubble.ets(48:9)", "entry");
            // 时间
            Text.fontSize(10);
            // 时间
            Text.fontColor('#606060');
            // 时间
            Text.margin({ top: 4 });
        }, Text);
        // 时间
        Text.pop();
        Column.pop();
        this.observeComponentCreation2((elmtId, isInitialRender) => {
            If.create();
            if (this.message.role === 'assistant') {
                this.ifElseBranchUpdateFunction(0, () => {
                    this.observeComponentCreation2((elmtId, isInitialRender) => {
                        Blank.create();
                        Blank.debugLine("entry/src/main/ets/components/ChatBubble.ets(56:9)", "entry");
                    }, Blank);
                    Blank.pop();
                });
            }
            else {
                this.ifElseBranchUpdateFunction(1, () => {
                });
            }
        }, If);
        If.pop();
        Row.pop();
    }
    private getActionLabel(): string {
        if (this.message.action === 'control_robot')
            return '🤖 已操控';
        if (this.message.action === 'set_reminder')
            return '⏰ 已设提醒';
        return '';
    }
    private formatTime(timestamp: number): string {
        let date: Date = new Date(timestamp);
        let h: string = date.getHours().toString().padStart(2, '0');
        let m: string = date.getMinutes().toString().padStart(2, '0');
        return h + ':' + m;
    }
    rerender() {
        this.updateDirtyElements();
    }
}
