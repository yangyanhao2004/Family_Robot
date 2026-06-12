/**
 * 设置页面 — 对应 Vue 前端 SettingsView.vue
 * 显示固件版本、序列号、紧急联系人设置
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { RobotSettings } from '../model/Types'
import promptAction from '@ohos.promptAction'

@Entry
@Component
struct SettingsPage {
  @State settings: RobotSettings = { firmwareVersion: '', serialNumber: '' }
  @State isLoading: boolean = false
  @State error: string = ''
  @State ecName: string = ''
  @State ecEmail: string = ''
  @State isSaving: boolean = false

  aboutToAppear(): void {
    this.loadSettings()
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
        Text('设置')
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
        Scroll() {
          Column({ space: 16 }) {
            // 固件版本
            Column() {
              Text('固件版本')
                .fontSize(12).fontColor('#808080')
              Text(this.settings.firmwareVersion || '--')
                .fontSize(16).fontColor('#e0e0e0').margin({ top: 4 })
            }
            .width('100%').alignItems(HorizontalAlign.Start)
            .padding(16).borderRadius(8).backgroundColor('#1a1a2e')

            // 序列号
            Column() {
              Text('设备序列号')
                .fontSize(12).fontColor('#808080')
              Text(this.settings.serialNumber || '--')
                .fontSize(16).fontColor('#e0e0e0').margin({ top: 4 })
            }
            .width('100%').alignItems(HorizontalAlign.Start)
            .padding(16).borderRadius(8).backgroundColor('#1a1a2e')

            // 紧急联系人
            Column({ space: 12 }) {
              Row() {
                Text('🆘').fontSize(16)
                Text('紧急联系人').fontSize(14).fontColor('#ef4444').margin({ left: 6 })
              }

              TextInput({ placeholder: '联系人姓名', text: this.ecName })
                .fontSize(14).fontColor('#e0e0e0')
                .placeholderColor('#606060')
                .backgroundColor('#0f0f2a').borderRadius(8).height(44).padding(12)
                .onChange((value: string) => { this.ecName = value })

              TextInput({ placeholder: '联系人邮箱', text: this.ecEmail })
                .fontSize(14).fontColor('#e0e0e0')
                .placeholderColor('#606060')
                .backgroundColor('#0f0f2a').borderRadius(8).height(44).padding(12)
                .type(InputType.Email)
                .onChange((value: string) => { this.ecEmail = value })

              Button(this.isSaving ? '保存中...' : '💾 保存紧急联系人')
                .fontSize(14).fontColor('#ffffff')
                .backgroundColor(this.isSaving ? '#4a1a1a' : '#dc2626')
                .borderRadius(8).height(44)
                .enabled(!this.isSaving)
                .onClick(() => { this.saveEmergencyContact() })
            }
            .width('100%').alignItems(HorizontalAlign.Start)
            .padding(16).borderRadius(8).backgroundColor('#1a1a2e')

            // 关于
            Column() {
              Text('关于')
                .fontSize(12).fontColor('#808080')
              Text('家庭服务机器人 v1.0.0')
                .fontSize(14).fontColor('#e0e0e0').margin({ top: 4 })
              Text('鸿蒙端 (HarmonyOS App)')
                .fontSize(12).fontColor('#606060').margin({ top: 2 })
            }
            .width('100%').alignItems(HorizontalAlign.Start)
            .padding(16).borderRadius(8).backgroundColor('#1a1a2e')
          }
          .padding(16).width('100%')
        }
        .layoutWeight(1)
      }
    }
    .width('100%').height('100%')
    .backgroundColor('#0a0a1a')
  }

  private async loadSettings(): Promise<void> {
    this.isLoading = true
    try {
      let data: Record<string, Object> = await api.getSettings()
      this.settings = {
        firmwareVersion: data['firmwareVersion'] as string,
        serialNumber: data['serialNumber'] as string,
        emergencyContactName: (data['emergencyContactName'] as string) || '',
        emergencyContactEmail: (data['emergencyContactEmail'] as string) || ''
      }
      this.ecName = this.settings.emergencyContactName || ''
      this.ecEmail = this.settings.emergencyContactEmail || ''
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }

  private async saveEmergencyContact(): Promise<void> {
    this.isSaving = true
    try {
      let result: Record<string, Object> = await api.updateEmergencyContact(this.ecName, this.ecEmail)
      this.settings.emergencyContactName = (result['emergencyContactName'] as string) || this.ecName
      this.settings.emergencyContactEmail = (result['emergencyContactEmail'] as string) || this.ecEmail
      promptAction.showToast({ message: '紧急联系人已保存', duration: 2000 })
    } catch (err) {
      promptAction.showToast({ message: '保存失败: ' + (err as Error).message, duration: 2000 })
    } finally {
      this.isSaving = false
    }
  }
}
