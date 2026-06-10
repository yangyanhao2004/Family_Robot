import UIAbility from "@ohos:app.ability.UIAbility";
import type Want from "@ohos:app.ability.Want";
import type AbilityConstant from "@ohos:app.ability.AbilityConstant";
import type window from "@ohos:window";
import { authManager } from "@bundle:com.familyrobot.harmonyos/entry/ets/services/AuthManager";
export default class EntryAbility extends UIAbility {
    onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
        // 初始化认证管理器（从 preferences 恢复登录态）
        authManager.init();
    }
    onDestroy(): void {
        // 清理
    }
    onWindowStageCreate(windowStage: window.WindowStage): void {
        // 加载首页
        windowStage.loadContent('pages/LoginPage', (_err, _data) => {
            // 页面加载完成
        });
    }
    onWindowStageDestroy(): void {
        // 窗口销毁
    }
    onForeground(): void {
        // 前台恢复
    }
    onBackground(): void {
        // 后台挂起
    }
}
