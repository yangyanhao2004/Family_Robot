/**
 * 相册页面 — 对应 Vue 前端 AlbumView.vue
 * 浏览、下载、删除照片
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { AlbumPhoto } from '../model/Types'
import { BACKEND_HTTP_URL } from '../common/Constants'

@Entry
@Component
struct AlbumPage {
  @State photos: AlbumPhoto[] = []
  @State isLoading: boolean = false
  @State error: string = ''
  @State selectedIds: Set<string> = new Set()

  aboutToAppear(): void {
    this.loadPhotos()
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
        Text('相册')
          .fontSize(18).fontColor('#ffffff')
        Blank()

        if (this.selectedIds.size > 0) {
          // 选中操作栏
          Row({ space: 10 }) {
            Text('已选 ' + this.selectedIds.size)
              .fontSize(13).fontColor('#a0a0a0')

            Button('下载')
              .fontSize(12).height(30).padding({ left: 10, right: 10 })
              .backgroundColor('#0f3460').borderRadius(6)
              .fontColor('#ffffff')
              .onClick(() => { this.downloadSelected() })

            Button('删除')
              .fontSize(12).height(30).padding({ left: 10, right: 10 })
              .backgroundColor('#7f1d1d').borderRadius(6)
              .fontColor('#ffffff')
              .onClick(() => { this.deleteSelected() })
          }
        } else {
          Row().width(60)
        }
      }
      .width('100%').padding(16)

      // 内容
      if (this.isLoading) {
        Column() {
          LoadingProgress().width(40).height(40).color('#3b82f6')
          Text('加载中...').fontSize(14).fontColor('#808080').margin({ top: 12 })
        }
        .width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else if (this.error.length > 0) {
        Column() {
          Text('⚠️').fontSize(40)
          Text(this.error).fontSize(14).fontColor('#ef4444').margin({ top: 8 })
          Button('重试')
            .fontSize(13).margin({ top: 16 })
            .backgroundColor('#3b82f6').borderRadius(6)
            .onClick(() => this.loadPhotos())
        }
        .width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else if (this.photos.length === 0) {
        Column() {
          Text('📷').fontSize(48).opacity(0.3)
          Text('暂无照片').fontSize(14).fontColor('#808080').margin({ top: 8 })
          Text('在主控面板点击拍照按钮拍照').fontSize(12).fontColor('#606060').margin({ top: 4 })
        }
        .width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else {
        // 照片网格
        Grid() {
          ForEach(this.photos, (photo: AlbumPhoto) => {
            GridItem() {
              Stack() {
                // 照片缩略图
                Image(photo.url)
                  .objectFit(ImageFit.Cover)
                  .width('100%')
                  .height(120)
                  .borderRadius(8)

                // 选中标记
                if (this.selectedIds.has(photo.id)) {
                  Row() {
                    Text('✓')
                      .fontSize(14).fontColor('#ffffff')
                  }
                  .width(28).height(28)
                  .borderRadius(14)
                  .backgroundColor('#3b82f6')
                  .justifyContent(FlexAlign.Center)
                  .position({ right: 6, top: 6 })
                }

                // 日期
                Text(photo.date)
                  .fontSize(10).fontColor('#c0c0c0')
                  .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                  .backgroundColor('rgba(0,0,0,0.6)')
                  .borderRadius(4)
                  .position({ left: 6, bottom: 6 })
              }
              .onClick(() => { this.toggleSelect(photo.id) })
            }
          })
        }
        .columnsTemplate('1fr 1fr 1fr')
        .columnsGap(8).rowsGap(8)
        .padding(12)
        .layoutWeight(1)
        .width('100%')
        .backgroundColor('#1A1A1A')
      }
    }
    .width('100%').height('100%')
    .backgroundColor('#1A1A1A')
  }

  private async loadPhotos(): Promise<void> {
    this.isLoading = true
    this.error = ''
    try {
      let data: Array<Record<string, Object>> = await api.getPhotos()
      let baseUrl: string = BACKEND_HTTP_URL.replace(/\/$/, '')
      this.photos = data.map((item: Record<string, Object>): AlbumPhoto => {
        let relUrl: string = item['url'] as string
        return {
          id: item['id'] as string,
          url: relUrl.startsWith('http') ? relUrl : baseUrl + relUrl,
          date: item['date'] as string
        }
      })
    } catch (err) {
      this.error = (err as Error).message
    } finally {
      this.isLoading = false
    }
  }

  private toggleSelect(id: string): void {
    if (this.selectedIds.has(id)) {
      this.selectedIds.delete(id)
    } else {
      this.selectedIds.add(id)
    }
    // 触发状态更新
    this.selectedIds = new Set(this.selectedIds)
  }

  private async deleteSelected(): Promise<void> {
    for (let id of this.selectedIds) {
      try {
        await api.deletePhoto(id)
      } catch (_err) { /* 继续 */ }
    }
    this.selectedIds = new Set()
    this.loadPhotos()
  }

  private downloadSelected(): void {
    // 鸿蒙端下载到本地相册较复杂，简化处理
    // 可在后续完善
  }
}
