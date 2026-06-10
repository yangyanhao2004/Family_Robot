/**
 * 相册页面 — 浏览、下载、删除照片
 */
import router from '@ohos.router'
import { api } from '../services/ApiService'
import { AlbumPhoto } from '../model/Types'
import { BACKEND_HTTP_URL } from '../common/Constants'
import request from '@ohos.request'

@Entry
@Component
struct AlbumPage {
  @State photos: AlbumPhoto[] = []
  @State isLoading: boolean = false
  @State error: string = ''
  @State selectedIds: Set<string> = new Set()
  @State downloading: boolean = false
  @State downloadMsg: string = ''

  aboutToAppear(): void { this.loadPhotos() }

  build() {
    Column() {
      // Title bar
      Row() {
        Button('← 返回').fontSize(14).fontColor('#71717A')
          .backgroundColor('transparent').onClick(() => router.back())
        Blank()
        Text('相册').fontSize(18).fontColor('#FFFFFF')
        Blank()

        if (this.selectedIds.size > 0) {
          Row({ space: 8 }) {
            Text('已选 ' + this.selectedIds.size).fontSize(12).fontColor('#A3A3A6')
            Button('下载').fontSize(12).height(30).padding({ left: 10, right: 10 })
              .backgroundColor('#2563EB').borderRadius(6).fontColor('#FFFFFF')
              .onClick(() => this.downloadSelected())
            Button('删除').fontSize(12).height(30).padding({ left: 10, right: 10 })
              .backgroundColor('#DC2626').borderRadius(6).fontColor('#FFFFFF')
              .onClick(() => this.deleteSelected())
          }
        } else {
          Row().width(60)
        }
      }.width('100%').padding({ left: 16, right: 16, top: 12, bottom: 12 })

      // Download status
      if (this.downloadMsg.length > 0) {
        Text(this.downloadMsg).fontSize(12).fontColor('#22C55E')
          .padding(8).width('100%').textAlign(TextAlign.Center)
          .backgroundColor('#22C55E20')
      }

      // Content
      if (this.isLoading) {
        Column() {
          LoadingProgress().width(40).height(40).color('#3B82F6')
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else if (this.photos.length === 0) {
        Column() {
          Text('📷').fontSize(48).opacity(0.3)
          Text('暂无照片').fontSize(14).fontColor('#A3A3A6').margin({ top: 8 })
        }.width('100%').layoutWeight(1).justifyContent(FlexAlign.Center)
      } else {
        Grid() {
          ForEach(this.photos, (photo: AlbumPhoto) => {
            GridItem() {
              Stack() {
                Image(photo.url).objectFit(ImageFit.Cover)
                  .width('100%').height(120).borderRadius(8)

                if (this.selectedIds.has(photo.id)) {
                  Row() {
                    Text('✓').fontSize(14).fontColor('#FFFFFF')
                  }.width(28).height(28).borderRadius(14)
                  .backgroundColor('#2563EB').justifyContent(FlexAlign.Center)
                  .position({ right: 6, top: 6 })
                }

                Text(photo.date).fontSize(10).fontColor('#D1D5DB')
                  .padding({ left: 6, right: 6, top: 2, bottom: 2 })
                  .backgroundColor('rgba(0,0,0,0.6)').borderRadius(4)
                  .position({ left: 6, bottom: 6 })
              }.onClick(() => this.toggleSelect(photo.id))
            }
          })
        }
        .columnsTemplate('1fr 1fr 1fr').columnsGap(8).rowsGap(8)
        .padding(12).layoutWeight(1).width('100%').backgroundColor('#1A1A1A')
      }
    }.width('100%').height('100%').backgroundColor('#1A1A1A')
  }

  private async loadPhotos(): Promise<void> {
    this.isLoading = true
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
      this.error = ''
    } catch (err) {
      this.error = (err as Error).message
    } finally { this.isLoading = false }
  }

  private toggleSelect(id: string): void {
    if (this.selectedIds.has(id)) {
      this.selectedIds.delete(id)
    } else {
      this.selectedIds.add(id)
    }
    this.selectedIds = new Set(this.selectedIds)
  }

  private async downloadSelected(): Promise<void> {
    if (this.downloading) return
    this.downloading = true
    let count = 0
    let fail = 0
    for (let id of this.selectedIds) {
      let photo = this.photos.find((p: AlbumPhoto) => p.id === id)
      if (photo) {
        try {
          let fileName = id.includes('.') ? id : id + '.jpg'
          let ctx = getContext(this)
          let filePath = ctx.filesDir + '/' + fileName
          let task = await request.downloadFile(ctx, { url: photo.url, filePath: filePath })
          await new Promise<void>((res) => {
            task.on('complete', () => res())
            task.on('fail', () => res())
          })
          count++
        } catch (_e) {
          fail++
        }
      }
    }
    this.downloading = false
    this.downloadMsg = '下载完成: ' + count + ' 成功' + (fail > 0 ? ', ' + fail + ' 失败' : '')
    this.selectedIds = new Set()
    setTimeout(() => { this.downloadMsg = '' }, 3000)
  }

  private async deleteSelected(): Promise<void> {
    for (let id of this.selectedIds) {
      try { await api.deletePhoto(id) } catch (_e) { }
    }
    this.selectedIds = new Set()
    this.loadPhotos()
  }
}
