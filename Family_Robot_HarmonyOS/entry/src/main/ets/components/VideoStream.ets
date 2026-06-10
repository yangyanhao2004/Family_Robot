/**
 * 视频流组件 — 单帧 JPEG 轮询显示
 *
 * 通过 HTTP 周期性请求 Python 后端 /video/frame 获取最新单帧 JPEG，
 * 解码为 PixelMap 后用 Image 组件渲染。
 */
import http from '@ohos.net.http'
import image from '@ohos.multimedia.image'
import { BACKEND_HTTP_URL } from '../common/Constants'

@Component
export struct VideoStream {
  @Prop streamUrl: string = BACKEND_HTTP_URL + '/video/frame'
  @State private pixelMap: image.PixelMap | null = null
  @State private isLoading: boolean = false
  @State private hasError: boolean = false
  private frameTimer: number | null = null
  private running: boolean = false
  private requestActive: boolean = false
  private startTime: number = 0
  private readonly FRAME_INTERVAL: number = 150
  private readonly ERROR_TIMEOUT: number = 10000

  aboutToAppear(): void {
    this.running = true
    this.startPolling()
  }

  aboutToDisappear(): void {
    this.running = false
    if (this.frameTimer !== null) {
      clearTimeout(this.frameTimer)
      this.frameTimer = null
    }
    if (this.pixelMap !== null) {
      this.pixelMap.release()
      this.pixelMap = null
    }
  }

  build() {
    Stack() {
      if (this.pixelMap !== null) {
        Image(this.pixelMap)
          .objectFit(ImageFit.Contain)
          .width('100%')
          .height('100%')
      } else if (!this.hasError) {
        Column() {
          Text('📷').fontSize(48).opacity(0.3)
          Text(this.isLoading ? '连接中...' : '等待视频流...')
            .fontSize(14).fontColor('#808080').margin({ top: 8 })
        }
        .width('100%').height('100%').justifyContent(FlexAlign.Center)
      }

      if (this.isLoading && this.pixelMap === null && !this.hasError) {
        LoadingProgress().width(40).height(40).color('#3b82f6')
      }

      if (this.hasError) {
        Column() {
          Text('⚠️').fontSize(36)
          Text('视频连接失败').fontSize(14).fontColor('#ef4444').margin({ top: 6 })
          Button('重试').fontSize(12).margin({ top: 10 })
            .backgroundColor('#ef4444').borderRadius(6)
            .onClick(() => {
              this.hasError = false
              this.isLoading = true
              this.running = true
              this.startPolling()
            })
        }
        .width('100%').height('100%').justifyContent(FlexAlign.Center)
        .backgroundColor('rgba(0,0,0,0.8)')
      }
    }
    .width('100%').height('100%').backgroundColor('#0a0a0a')
  }

  /**
   * 启动串行帧轮询（每次只发一个请求，完成后等 FRAME_INTERVAL 再发下一个）
   */
  private startPolling(): void {
    if (!this.running) return
    this.isLoading = true
    this.startTime = Date.now()
    this.scheduleNext()
  }

  private scheduleNext(): void {
    if (!this.running) return
    this.fetchFrame()
  }

  private async fetchFrame(): Promise<void> {
    if (this.requestActive || !this.running) {
      return
    }
    this.requestActive = true

    let req: http.HttpRequest | null = null
    try {
      req = http.createHttp()
      let resp: http.HttpResponse = await req.request(this.streamUrl, {
        method: http.RequestMethod.GET,
        expectDataType: http.HttpDataType.ARRAY_BUFFER,
        connectTimeout: 5000,
        readTimeout: 5000
      })

      if (resp.responseCode === 200) {
        let data: ArrayBuffer = resp.result as ArrayBuffer
        if (data !== null && data !== undefined && data.byteLength > 0) {
          let source: image.ImageSource = image.createImageSource(data)
          let opts: image.DecodingOptions = {
            desiredSize: { width: 640, height: 480 },
            desiredPixelFormat: image.PixelMapFormat.RGBA_8888
          }
          let newPm: image.PixelMap = await source.createPixelMap(opts)
          if (this.pixelMap !== null) {
            this.pixelMap.release()
          }
          this.pixelMap = newPm
          source.release()
          this.isLoading = false
          this.hasError = false
        }
      }
    } catch (_e) {
      // 单次失败不中断，继续尝试
    } finally {
      if (req !== null) {
        req.destroy()
      }
      this.requestActive = false

      // 如果持续失败超过 30 秒，显示错误
      if (this.isLoading && this.running) {
        let elapsed: number = Date.now() - this.startTime
        if (elapsed > this.ERROR_TIMEOUT) {
          this.isLoading = false
          this.hasError = true
          this.running = false
          return
        }
      }

      // 调度下一帧
      if (this.running) {
        this.frameTimer = setTimeout(() => {
          this.scheduleNext()
        }, this.FRAME_INTERVAL)
      }
    }
  }

  reset(newUrl?: string): void {
    this.running = false
    if (this.frameTimer !== null) {
      clearTimeout(this.frameTimer)
      this.frameTimer = null
    }
    if (newUrl) {
      this.streamUrl = newUrl
    }
    if (this.pixelMap !== null) {
      this.pixelMap.release()
      this.pixelMap = null
    }
    this.hasError = false
    this.isLoading = true
    this.running = true
    this.startPolling()
  }
}
