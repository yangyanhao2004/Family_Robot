/**
 * 应用入口 — EntryAbility
 * 初始化认证管理器，跳转到登录页或主控面板
 */
import UIAbility from '@ohos.app.ability.UIAbility'
import { Want } from '@kit.AbilityKit'
import { AbilityConstant } from '@kit.AbilityKit'
import window from '@ohos.window'
import { authManager } from '../services/AuthManager'

export default class EntryAbility extends UIAbility {
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    // 初始化认证管理器（从 preferences 恢复登录态）
    authManager.init()
  }

  onDestroy(): void {
    // 清理
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    // 加载首页
    windowStage.loadContent('pages/LoginPage', (_err, _data) => {
      // 页面加载完成
    })
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
