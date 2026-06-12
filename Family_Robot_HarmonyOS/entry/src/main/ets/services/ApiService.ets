/**
 * HTTP REST API 客户端 — 对应 Vue 前端 api.ts
 * 对接 Java Spring Boot 后端 (Port 8090)
 */
import http from '@ohos.net.http'
import { authManager } from './AuthManager'
import { JAVA_API_URL } from '../common/Constants'

export interface ApiClient {
  login: (email: string, password: string) => Promise<Record<string, Object>>
  register: (email: string, password: string, serialNumber: string,
             emergencyContactName?: string, emergencyContactEmail?: string) => Promise<Record<string, Object>>
  verify: (email: string, code: string) => Promise<Record<string, Object>>
  sendLoginCode: (email: string) => Promise<Record<string, Object>>
  verifyLoginCode: (email: string, code: string) => Promise<Record<string, Object>>
  sendResetPasswordCode: (email: string) => Promise<Record<string, Object>>
  resetPassword: (email: string, code: string, newPassword: string) => Promise<Record<string, Object>>
  getPhotos: () => Promise<Array<Record<string, Object>>>
  deletePhoto: (id: string) => Promise<void>
  addPhoto: (url: string, filename: string) => Promise<Record<string, Object>>
  getSettings: () => Promise<Record<string, Object>>
  updateEmergencyContact: (name: string, email: string) => Promise<Record<string, Object>>
  triggerFallAlert: (userId: number, userName: string) => Promise<Record<string, Object>>
  getProfile: () => Promise<Record<string, Object>>
  getReminders: (userId: number) => Promise<Array<Record<string, Object>>>
  createReminder: (data: Record<string, Object>) => Promise<Record<string, Object>>
  updateReminder: (id: number, data: Record<string, Object>) => Promise<Record<string, Object>>
  deleteReminder: (id: number) => Promise<Record<string, Object>>
}

function apiBase(): string {
  return JAVA_API_URL.replace(/\/$/, '')
}

/**
 * 通用请求方法
 */
async function doRequest<T>(path: string, options?: http.HttpRequestOptions): Promise<T> {
  let url: string = apiBase() + path

  let headers: Record<string, string> = {
    'Content-Type': 'application/json'
  }

  // 附带 JWT
  let token: string = authManager.getToken()
  if (token.length > 0) {
    headers['Authorization'] = 'Bearer ' + token
  }

  if (options && options.header) {
    let optHeaders: Record<string, Object> = options.header as Record<string, Object>
    let keys: string[] = Object.keys(optHeaders)
    for (let k of keys) {
      headers[k] = optHeaders[k] as string
    }
  }
  let method: http.RequestMethod = options?.method ?? http.RequestMethod.GET
  let extraData: string | undefined = undefined
  if (options && options.extraData) {
    if (typeof options.extraData === 'string') {
      extraData = options.extraData as string
    } else {
      extraData = JSON.stringify(options.extraData)
    }
  }

  let request: http.HttpRequest = http.createHttp()
  let response: http.HttpResponse

  try {
    response = await request.request(url, {
      method: method,
      header: headers,
      extraData: extraData,
      expectDataType: http.HttpDataType.STRING,
      connectTimeout: 10000,
      readTimeout: 30000
    })

    // 处理 401 未授权
    if (response.responseCode === 401 && !path.startsWith('/api/auth/')) {
      await authManager.logout()
      throw new Error('登录已过期，请重新登录')
    }

    if (response.responseCode < 200 || response.responseCode >= 300) {
      let message: string = method + ' ' + path + ' failed (' + response.responseCode + ')'
      try {
        if (response.result && typeof response.result === 'string') {
          let body: Record<string, Object> = JSON.parse(response.result as string) as Record<string, Object>
          if (body['message']) {
            message = body['message'] as string
          }
        }
      } catch (_e) {
        if (response.result && typeof response.result === 'string') {
          message = response.result as string
        }
      }
      throw new Error(message)
    }

    if (response.result && typeof response.result === 'string') {
      return JSON.parse(response.result as string) as T
    }
    return response.result as T
  } finally {
    request.destroy()
  }
}

class ApiServiceImpl implements ApiClient {
  // ==================== Auth ====================
  login(email: string, password: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/login', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email, 'password': password })
    })
  }

  register(email: string, password: string, serialNumber: string,
           emergencyContactName?: string, emergencyContactEmail?: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/register', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({
        'email': email, 'password': password, 'serialNumber': serialNumber,
        'emergencyContactName': emergencyContactName || '', 'emergencyContactEmail': emergencyContactEmail || ''
      })
    })
  }

  verify(email: string, code: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/verify', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email, 'code': code })
    })
  }

  sendLoginCode(email: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/login-code/send', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email })
    })
  }

  verifyLoginCode(email: string, code: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/login-code/verify', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email, 'code': code })
    })
  }

  sendResetPasswordCode(email: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/reset-password/send', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email })
    })
  }

  resetPassword(email: string, code: string, newPassword: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/auth/reset-password/verify', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'email': email, 'code': code, 'newPassword': newPassword })
    })
  }

  // ==================== Album ====================
  getPhotos(): Promise<Array<Record<string, Object>>> {
    return doRequest<Array<Record<string, Object>>>('/api/albums')
  }

  deletePhoto(id: string): Promise<void> {
    return doRequest<void>('/api/albums/' + id, { method: http.RequestMethod.DELETE })
  }

  addPhoto(url: string, filename: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/albums', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'url': url, 'filename': filename })
    })
  }

  // ==================== Settings ====================
  getSettings(): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/settings')
  }

  updateEmergencyContact(name: string, email: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/settings/emergency-contact', {
      method: http.RequestMethod.PUT,
      extraData: JSON.stringify({ 'name': name, 'email': email })
    })
  }

  // ==================== Emergency ====================
  triggerFallAlert(userId: number, userName: string): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('http://192.168.137.90:8080/emergency/fall', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify({ 'userId': userId, 'userName': userName })
    })
  }

  // ==================== User Profile ====================
  getProfile(): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/users/profile')
  }

  // ==================== Reminders ====================
  getReminders(userId: number): Promise<Array<Record<string, Object>>> {
    return doRequest<Array<Record<string, Object>>>('/api/reminders?userId=' + userId)
  }

  createReminder(data: Record<string, Object>): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/reminders', {
      method: http.RequestMethod.POST,
      extraData: JSON.stringify(data)
    })
  }

  updateReminder(id: number, data: Record<string, Object>): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/reminders/' + id, {
      method: http.RequestMethod.PUT,
      extraData: JSON.stringify(data)
    })
  }

  deleteReminder(id: number): Promise<Record<string, Object>> {
    return doRequest<Record<string, Object>>('/api/reminders/' + id, {
      method: http.RequestMethod.DELETE
    })
  }
}

export const api: ApiClient = new ApiServiceImpl()
