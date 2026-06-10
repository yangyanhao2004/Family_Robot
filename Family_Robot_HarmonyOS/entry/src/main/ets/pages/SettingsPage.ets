/**
 * 设置页面 — 对应 Vue 前端 SettingsView.vue
 * 显示固件版本和序列号
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { RobotSettings } from '../model/Types'

@Entry
@Component
struct SettingsPage {
  @State settings: RobotSettings = { firmwareVersion: '', serialNumber: '' }
  @State isLoading: boolean = false
  @State error: string = ''

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
        serialNumber: data['serialNumber'] as string
      }
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }
}
