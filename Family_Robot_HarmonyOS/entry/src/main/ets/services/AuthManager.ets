/**
 * 认证管理器 — 对应 Vue 前端 authStore.ts
 * 使用 @ohos.data.preferences 替代 localStorage
 */
import preferences from '@ohos.data.preferences'
import util from '@ohos.util'
import type { ApiClient } from './ApiService'
import { UserProfile } from '../model/Types'

const STORE_NAME: string = 'family_robot_auth'

class AuthManager {
  private token: string = ''
  private role: string = ''
  private isLoading: boolean = false

  /**
   * 初始化：从 preferences 恢复登录态
   */
  async init(): Promise<void> {
    try {
      let prefs: preferences.Preferences = await preferences.getPreferences(
        getContext(), STORE_NAME)
      this.token = await prefs.get('auth_token', '') as string
      this.role = await prefs.get('auth_role', '') as string
    } catch (_err) {
      this.token = ''
      this.role = ''
    }
  }

  getToken(): string {
    return this.token
  }

  getRole(): string {
    return this.role
  }

  getLoading(): boolean {
    return this.isLoading
  }

  isAdmin(): boolean {
    return this.role === 'Admin'
  }

  isAuthenticated(): boolean {
    return this.token.length > 0
  }

  /**
   * 密码登录
   */
  async login(email: string, password: string): Promise<void> {
    this.isLoading = true
    try {
      // 动态导入避免循环依赖
      let apiModule: Record<string, Object> = await import('./ApiService') as Record<string, Object>
      let apiClient: ApiClient = apiModule['api'] as ApiClient
      let res: Record<string, Object> = await apiClient.login(email, password)
      let token: string = res['token'] as string
      let role: string = res['role'] as string
      await this.setAuth(token, role)
    } finally {
      this.isLoading = false
    }
  }

  /**
   * 验证码登录（token 由调用方通过 verifyLoginCode 获取后传入）
   */
  async setAuth(token: string, role: string): Promise<void> {
    this.token = token
    this.role = role
    try {
      let prefs: preferences.Preferences = await preferences.getPreferences(
        getContext(), STORE_NAME)
      await prefs.put('auth_token', token)
      await prefs.put('auth_role', role)
      await prefs.flush()
    } catch (_err) {
      // preferences 写入失败不影响内存状态
    }
  }

  /**
   * 登出
   */
  async logout(): Promise<void> {
    this.token = ''
    this.role = ''
    try {
      let prefs: preferences.Preferences = await preferences.getPreferences(
        getContext(), STORE_NAME)
      await prefs.delete('auth_token')
      await prefs.delete('auth_role')
      await prefs.flush()
    } catch (_err) {
      // 忽略
    }
  }

  /**
   * 获取 JWT 中的 userId
   */
  getUserIdFromToken(): number {
    if (this.token.length === 0) {
      return 0
    }
    try {
      let parts: string[] = this.token.split('.')
      if (parts.length < 2) {
        return 0
      }
      // Base64 解码 payload
      let payload: string = this.base64Decode(parts[1])
      let obj: Record<string, Object> = JSON.parse(payload) as Record<string, Object>
      return (obj['userId'] as number) || (obj['sub'] as number) || 0
    } catch (_err) {
      return 0
    }
  }

  /**
   * 获取 JWT 中的 email
   */
  getUserEmailFromToken(): string {
    if (this.token.length === 0) {
      return ''
    }
    try {
      let parts: string[] = this.token.split('.')
      if (parts.length < 2) {
        return ''
      }
      let payload: string = this.base64Decode(parts[1])
      let obj: Record<string, Object> = JSON.parse(payload) as Record<string, Object>
      return (obj['email'] as string) || ''
    } catch (_err) {
      return ''
    }
  }

  /**
   * Base64 解码（处理 URL-safe 变体）
   */
  private base64Decode(input: string): string {
    let base64: string = input
    // 还原 URL-safe 字符
    base64 = base64.replace(/-/g, '+').replace(/_/g, '/')
    // 补齐 padding
    while (base64.length % 4 !== 0) {
      base64 += '='
    }
    // 使用 util 的 Base64 解码
    let helper = new util.Base64Helper()
    let uint8Array: Uint8Array = helper.decodeSync(base64)
    let textDecoderOptions: util.TextDecoderOptions = { fatal: false, ignoreBOM: true }
    let decoder: util.TextDecoder = util.TextDecoder.create('utf-8', textDecoderOptions)
    return decoder.decodeToString(uint8Array)
  }
}

// 全局单例
export const authManager: AuthManager = new AuthManager()
