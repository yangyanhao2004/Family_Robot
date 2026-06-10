/**
 * 密码重置页面 — 对应 Vue 前端 ResetPasswordView.vue
 * 两步流程：发验证码 → 输入新密码
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { authManager } from '../services/AuthManager'

@Entry
@Component
struct ResetPwdPage {
  @State step: number = 1
  @State email: string = ''
  @State code: string = ''
  @State newPassword: string = ''
  @State error: string = ''
  @State isLoading: boolean = false

  build() {
    Column() {
      // 标题栏
      Row() {
        Button('← 返回')
          .fontSize(14).fontColor('#808080')
          .backgroundColor('transparent')
          .onClick(() => {
            if (this.step === 1) {
              if (authManager.isAuthenticated()) {
                router.back()
              } else {
                router.replaceUrl({ url: 'pages/LoginPage' })
              }
            } else {
              this.step = 1
            }
          })
        Blank()
        Text('重置密码')
          .fontSize(18).fontColor('#ffffff')
        Blank()
        Row().width(60)
      }
      .width('100%').padding(16).margin({ top: 40 })

      Column({ space: 16 }) {
        if (this.step === 1) {
          Text('请输入注册邮箱，我们将发送验证码')
            .fontSize(14).fontColor('#a0a0a0').margin({ bottom: 10 })

          TextInput({ placeholder: '请输入邮箱', text: this.email })
            .width('100%').height(48)
            .backgroundColor('#1a1a2e').borderRadius(8)
            .border({ width: 1, color: '#333333' })
            .fontColor('#e0e0e0').placeholderColor('#606060')
            .type(InputType.Email)
            .onChange((v: string) => { this.email = v })
        } else {
          TextInput({ placeholder: '请输入6位验证码', text: this.code })
            .width('100%').height(48)
            .backgroundColor('#1a1a2e').borderRadius(8)
            .border({ width: 1, color: '#333333' })
            .fontColor('#e0e0e0').placeholderColor('#606060')
            .maxLength(6).type(InputType.Number)
            .fontSize(20).letterSpacing(8).textAlign(TextAlign.Center)
            .onChange((v: string) => { this.code = v })

          TextInput({ placeholder: '请输入新密码', text: this.newPassword })
            .width('100%').height(48)
            .backgroundColor('#1a1a2e').borderRadius(8)
            .border({ width: 1, color: '#333333' })
            .fontColor('#e0e0e0').placeholderColor('#606060')
            .type(InputType.Password)
            .onChange((v: string) => { this.newPassword = v })
        }

        if (this.error.length > 0) {
          Text(this.error)
            .fontSize(13).fontColor('#ef4444')
            .width('100%').textAlign(TextAlign.Center)
            .padding(10).backgroundColor('#2a1a1a').borderRadius(6)
        }

        Button(this.step === 1 ? '发送验证码' : '重置密码')
          .width('100%').height(48)
          .fontSize(16).fontColor('#ffffff')
          .backgroundColor('#3b82f6').borderRadius(8)
          .enabled(!this.isLoading)
          .onClick(() => {
            if (this.step === 1) this.sendCode()
            else this.resetPassword()
          })
      }
      .padding({ left: 40, right: 40 })
    }
    .width('100%').height('100%')
    .backgroundColor('#0a0a1a')
  }

  private async sendCode(): Promise<void> {
    this.error = ''
    this.isLoading = true
    try {
      await api.sendResetPasswordCode(this.email.trim())
      this.step = 2
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }

  private async resetPassword(): Promise<void> {
    this.error = ''
    this.isLoading = true
    try {
      await api.resetPassword(this.email.trim(), this.code, this.newPassword)
      router.replaceUrl({ url: 'pages/LoginPage' })
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }
}
