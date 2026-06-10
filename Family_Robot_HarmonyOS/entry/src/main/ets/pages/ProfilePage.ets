/**
 * 个人中心页面 — 对应 Vue 前端 UserProfileView.vue
 * 显示用户信息 + 登出 + 修改密码入口
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { authManager } from '../services/AuthManager'
import { webSocketService } from '../services/WebSocketService'
import { UserProfile } from '../model/Types'

@Entry
@Component
struct ProfilePage {
  @State profile: UserProfile = {
    name: '', email: '', role: '', avatar: '', lastLogin: ''
  }
  @State isLoading: boolean = false

  aboutToAppear(): void {
    this.loadProfile()
  }

  build() {
    Column() {
      // 标题栏
      Row() {
        Button('← 返回')
          .fontSize(14).fontColor('#808080')
          .backgroundColor('transparent')
          .onClick(() => router.back())
        Blank()
        Text('个人中心')
          .fontSize(18).fontColor('#ffffff')
        Blank()
        Row().width(60)
      }
      .width('100%').padding(16)

      if (this.isLoading) {
        Column() {
          LoadingProgress().width(40).height(40).color('#3b82f6')
        }
        .width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else {
        Column({ space: 20 }) {
          // 头像
          Column() {
            Text(this.profile.name.length > 0
              ? this.profile.name.charAt(0).toUpperCase()
              : '?')
              .fontSize(36).fontColor('#ffffff')
          }
          .width(72).height(72)
          .borderRadius(36)
          .backgroundColor('#3b82f6')
          .justifyContent(FlexAlign.Center)
          .margin({ top: 24 })

          // 用户信息
          Column({ space: 12 }) {
            this.InfoRow('姓名', this.profile.name)
            this.InfoRow('邮箱', this.profile.email)
            this.InfoRow('角色', this.profile.role)
            this.InfoRow('最后登录', this.profile.lastLogin)
          }
          .width('100%')
          .padding(16)
          .borderRadius(8)
          .backgroundColor('#1a1a2e')

          // 操作按钮
          Button('修改密码')
            .width('100%').height(44)
            .fontSize(15).fontColor('#ffffff')
            .backgroundColor('#0f3460').borderRadius(8)
            .onClick(() => {
              router.pushUrl({ url: 'pages/ResetPwdPage' })
            })

          Button('退出登录')
            .width('100%').height(44)
            .fontSize(15).fontColor('#ef4444')
            .backgroundColor('transparent')
            .border({ width: 1, color: '#ef4444' })
            .borderRadius(8)
            .onClick(() => { this.logout() })
        }
        .padding(16).width('100%')
      }
    }
    .width('100%').height('100%')
    .backgroundColor('#0a0a1a')
  }

  @Builder
  InfoRow(label: string, value: string) {
    Row() {
      Text(label)
        .fontSize(13).fontColor('#808080')
      Blank()
      Text(value || '--')
        .fontSize(14).fontColor('#e0e0e0')
    }
    .width('100%')
  }

  private async loadProfile(): Promise<void> {
    this.isLoading = true
    try {
      let data: Record<string, Object> = await api.getProfile()
      this.profile = {
        name: (data['name'] as string) || '',
        email: (data['email'] as string) || '',
        role: (data['role'] as string) || '',
        avatar: (data['avatar'] as string) || '',
        lastLogin: (data['lastLogin'] as string) || ''
      }
    } catch (_err) {
      // 失败时使用基本数据
    } finally {
      this.isLoading = false
    }
  }

  private async logout(): Promise<void> {
    // 结束 AI 会话
    let userId: number = authManager.getUserIdFromToken()
    webSocketService.sendAISessionEnd(userId)

    // 断开 WebSocket
    webSocketService.disconnect()

    // 清除认证
    await authManager.logout()

    // 跳转到登录页
    router.replaceUrl({ url: 'pages/LoginPage' })
  }
}
