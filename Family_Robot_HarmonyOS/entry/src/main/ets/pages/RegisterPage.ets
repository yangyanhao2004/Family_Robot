/**
 * 注册页面 — 对应 Vue 前端 RegisterView.vue
 * 两步流程：Step1 填信息发验证码 → Step2 输入验证码完成注册
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'

@Entry
@Component
struct RegisterPage {
  @State step: number = 1           // 1=填信息, 2=验码
  @State email: string = ''
  @State password: string = ''
  @State serialNumber: string = ''
  @State code: string = ''
  @State error: string = ''
  @State isLoading: boolean = false

  build() {
    Column() {
      // 标题栏
      Row() {
        Button('← 返回')
          .fontSize(14)
          .fontColor('#808080')
          .backgroundColor('transparent')
          .onClick(() => {
            if (this.step === 1) {
              router.back()
            } else {
              this.step = 1
            }
          })
        Blank()
        Text('注册账号')
          .fontSize(18)
          .fontColor('#ffffff')
        Blank()
        // 占位保持居中
        Row().width(60)
      }
      .width('100%')
      .padding(16)
      .margin({ top: 40 })

      // 步骤进度
      Row({ space: 8 }) {
        Row() {
          Text('1')
            .fontSize(12)
            .fontColor(this.step >= 1 ? '#ffffff' : '#808080')
        }
        .width(24).height(24)
        .borderRadius(12)
        .backgroundColor(this.step >= 1 ? '#3b82f6' : '#333333')
        .justifyContent(FlexAlign.Center)

        Divider().width(40).height(1).color(this.step >= 2 ? '#3b82f6' : '#333333')

        Row() {
          Text('2')
            .fontSize(12)
            .fontColor(this.step >= 2 ? '#ffffff' : '#808080')
        }
        .width(24).height(24)
        .borderRadius(12)
        .backgroundColor(this.step >= 2 ? '#3b82f6' : '#333333')
        .justifyContent(FlexAlign.Center)
      }
      .width('100%')
      .justifyContent(FlexAlign.Center)
      .margin({ top: 20, bottom: 30 })

      if (this.step === 1) {
        // Step 1: 填写信息
        this.BuildStep1()
      } else {
        // Step 2: 验证码
        this.BuildStep2()
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0a0a1a')
  }

  @Builder
  BuildStep1() {
    Column({ space: 16 }) {
      TextInput({ placeholder: '请输入邮箱', text: this.email })
        .width('100%').height(48)
        .backgroundColor('#1a1a2e').borderRadius(8)
        .border({ width: 1, color: '#333333' })
        .fontColor('#e0e0e0').placeholderColor('#606060')
        .type(InputType.Email)
        .onChange((v: string) => { this.email = v })

      TextInput({ placeholder: '请输入密码', text: this.password })
        .width('100%').height(48)
        .backgroundColor('#1a1a2e').borderRadius(8)
        .border({ width: 1, color: '#333333' })
        .fontColor('#e0e0e0').placeholderColor('#606060')
        .type(InputType.Password)
        .onChange((v: string) => { this.password = v })

      TextInput({ placeholder: '请输入机器人序列号', text: this.serialNumber })
        .width('100%').height(48)
        .backgroundColor('#1a1a2e').borderRadius(8)
        .border({ width: 1, color: '#333333' })
        .fontColor('#e0e0e0').placeholderColor('#606060')
        .onChange((v: string) => { this.serialNumber = v })

      if (this.error.length > 0) {
        Text(this.error)
          .fontSize(13).fontColor('#ef4444')
          .width('100%').textAlign(TextAlign.Center)
          .padding(10).backgroundColor('#2a1a1a').borderRadius(6)
      }

      Button('发送验证码')
        .width('100%').height(48)
        .fontSize(16).fontColor('#ffffff')
        .backgroundColor('#3b82f6').borderRadius(8)
        .enabled(!this.isLoading && this.email.length > 0
          && this.password.length > 0 && this.serialNumber.length > 0)
        .onClick(() => { this.sendRegisterCode() })
    }
    .padding({ left: 40, right: 40 })
  }

  @Builder
  BuildStep2() {
    Column({ space: 16 }) {
      Text('验证码已发送至 ' + this.email)
        .fontSize(14).fontColor('#a0a0a0')
        .margin({ bottom: 10 })

      TextInput({ placeholder: '请输入6位验证码', text: this.code })
        .width('100%').height(48)
        .backgroundColor('#1a1a2e').borderRadius(8)
        .border({ width: 1, color: '#333333' })
        .fontColor('#e0e0e0').placeholderColor('#606060')
        .maxLength(6).type(InputType.Number)
        .fontSize(20).letterSpacing(8)
        .textAlign(TextAlign.Center)
        .onChange((v: string) => { this.code = v })

      if (this.error.length > 0) {
        Text(this.error)
          .fontSize(13).fontColor('#ef4444')
          .width('100%').textAlign(TextAlign.Center)
          .padding(10).backgroundColor('#2a1a1a').borderRadius(6)
      }

      Button('完成注册')
        .width('100%').height(48)
        .fontSize(16).fontColor('#ffffff')
        .backgroundColor('#10b981').borderRadius(8)
        .enabled(!this.isLoading && this.code.length === 6)
        .onClick(() => { this.verifyCode() })
    }
    .padding({ left: 40, right: 40 })
  }

  private async sendRegisterCode(): Promise<void> {
    this.error = ''
    this.isLoading = true
    try {
      await api.register(this.email.trim(), this.password, this.serialNumber.trim())
      this.step = 2
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }

  private async verifyCode(): Promise<void> {
    this.error = ''
    this.isLoading = true
    try {
      await api.verify(this.email.trim(), this.code)
      router.replaceUrl({ url: 'pages/LoginPage' })
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }
}
