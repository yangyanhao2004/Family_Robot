/**
 * 登录页面 — 对应 Vue 前端 LoginView.vue
 * 支持密码登录 + 验证码登录双模式
 */
import router from '@ohos.router'
import { authManager } from '../services/AuthManager'
import { api } from '../services/ApiService'
import { authManager as auth } from '../services/AuthManager'

@Entry
@Component
struct LoginPage {
  @State email: string = ''
  @State password: string = ''
  @State code: string = ''
  @State loginMode: string = 'password' // 'password' | 'code'
  @State error: string = ''
  @State isLoading: boolean = false

  aboutToAppear(): void {
    // 已登录则直接跳转
    if (authManager.isAuthenticated()) {
      this.navigateToMain()
    }
  }

  build() {
    Column() {
      // 标题区域
      Column() {
        Text('家庭机器人')
          .fontSize(32)
          .fontWeight(FontWeight.Bold)
          .fontColor('#ffffff')
          .margin({ bottom: 8 })

        Text('Family Robot Control')
          .fontSize(15)
          .fontColor('#808080')
          .margin({ bottom: 40 })
      }
      .width('100%')
      .padding({ top: 80, bottom: 40 })
      .alignItems(HorizontalAlign.Center)

      // 登录模式切换
      Row({ space: 24 }) {
        Button('密码登录')
          .fontSize(14)
          .fontColor(this.loginMode === 'password' ? '#3b82f6' : '#808080')
          .backgroundColor('transparent')
          .border({ width: 0, color: this.loginMode === 'password' ? '#3b82f6' : 'transparent', style: BorderStyle.Solid })
          .borderWidth({ bottom: 2 })
          .borderRadius(0)
          .onClick(() => { this.loginMode = 'password' })
        Button('验证码登录')
          .fontSize(14)
          .fontColor(this.loginMode === 'code' ? '#3b82f6' : '#808080')
          .backgroundColor('transparent')
          .border({ width: 0, color: this.loginMode === 'code' ? '#3b82f6' : 'transparent', style: BorderStyle.Solid })
          .borderWidth({ bottom: 2 })
          .borderRadius(0)
          .onClick(() => { this.loginMode = 'code' })
      }
      .width('100%')
      .justifyContent(FlexAlign.Center)

      // 表单
      Column({ space: 16 }) {
        // 邮箱输入
        TextInput({ placeholder: '请输入邮箱', text: this.email })
          .width('100%')
          .height(48)
          .backgroundColor('#1a1a2e')
          .borderRadius(8)
          .border({ width: 1, color: '#333333' })
          .fontColor('#e0e0e0')
          .placeholderColor('#606060')
          .type(InputType.Email)
          .onChange((value: string) => { this.email = value })

        if (this.loginMode === 'password') {
          // 密码输入
          TextInput({ placeholder: '请输入密码', text: this.password })
            .width('100%')
            .height(48)
            .backgroundColor('#1a1a2e')
            .borderRadius(8)
            .border({ width: 1, color: '#333333' })
            .fontColor('#e0e0e0')
            .placeholderColor('#606060')
            .type(InputType.Password)
            .onChange((value: string) => { this.password = value })
        } else {
          // 验证码输入
          Row() {
            TextInput({ placeholder: '请输入验证码', text: this.code })
              .layoutWeight(1)
              .height(48)
              .backgroundColor('#1a1a2e')
              .borderRadius(8)
              .border({ width: 1, color: '#333333' })
              .fontColor('#e0e0e0')
              .placeholderColor('#606060')
              .maxLength(6)
              .type(InputType.Number)
              .onChange((value: string) => { this.code = value })

            Button('发送验证码')
              .fontSize(12)
              .height(48)
              .padding({ left: 12, right: 12 })
              .backgroundColor('#0f3460')
              .borderRadius(8)
              .fontColor('#ffffff')
              .margin({ left: 10 })
              .onClick(() => { this.sendCode() })
          }
          .width('100%')
        }

        // 错误提示
        if (this.error.length > 0) {
          Text(this.error)
            .fontSize(13)
            .fontColor('#ef4444')
            .width('100%')
            .textAlign(TextAlign.Center)
            .padding(10)
            .backgroundColor('#2a1a1a')
            .borderRadius(6)
        }

        // 登录按钮
        Button(this.isLoading ? '登录中...' : '登 录')
          .width('100%')
          .height(48)
          .fontSize(16)
          .fontColor('#ffffff')
          .backgroundColor('#3b82f6')
          .borderRadius(8)
          .enabled(!this.isLoading)
          .onClick(() => { this.handleLogin() })

        // 注册 / 忘记密码
        Row({ space: 20 }) {
          Button('注册账号')
            .fontSize(13)
            .fontColor('#808080')
            .backgroundColor('transparent')
            .onClick(() => { router.pushUrl({ url: 'pages/RegisterPage' }) })
          Button('忘记密码')
            .fontSize(13)
            .fontColor('#808080')
            .backgroundColor('transparent')
            .onClick(() => { router.pushUrl({ url: 'pages/ResetPwdPage' }) })
        }
        .width('100%')
        .justifyContent(FlexAlign.Center)
      }
      .padding({ left: 40, right: 40 })
      .width('100%')
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0a0a1a')
  }

  private async handleLogin(): Promise<void> {
    this.error = ''
    if (this.email.trim().length === 0) {
      this.error = '请输入邮箱'
      return
    }

    this.isLoading = true
    try {
      if (this.loginMode === 'password') {
        if (this.password.length === 0) {
          this.error = '请输入密码'
          this.isLoading = false
          return
        }
        await authManager.login(this.email.trim(), this.password)
      } else {
        if (this.code.length === 0) {
          this.error = '请输入验证码'
          this.isLoading = false
          return
        }
        let res: Record<string, Object> = await api.verifyLoginCode(this.email.trim(), this.code)
        await authManager.setAuth(res['token'] as string, res['role'] as string)
      }
      this.navigateToMain()
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }

  private async sendCode(): Promise<void> {
    if (this.email.trim().length === 0) {
      this.error = '请先输入邮箱'
      return
    }
    try {
      await api.sendLoginCode(this.email.trim())
      this.error = ''
    } catch (err) {
      this.error = (err as Error).message
    }
  }

  private navigateToMain(): void {
    if (authManager.isAdmin()) {
      // Admin 没有在鸿蒙端实现，跳转到 Dashboard
      router.replaceUrl({ url: 'pages/DashboardPage' })
    } else {
      router.replaceUrl({ url: 'pages/DashboardPage' })
    }
  }
}
