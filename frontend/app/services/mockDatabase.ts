import type { ApiErrorEnvelope } from '~/types'
import { getInitialMockDatabase, type MockDatabaseState } from './mockSeed'

const STORAGE_KEY = 'fastfoody_mock_db_v1'
const AUTH_SESSION_KEY = 'fastfoody_mock_auth_v1'

export class MockApiError extends Error {
  statusCode: number
  envelope: ApiErrorEnvelope

  constructor(
    statusCode: number,
    code: string,
    message: string,
    details: Record<string, unknown> | null = null
  ) {
    super(message)
    this.name = 'MockApiError'
    this.statusCode = statusCode
    this.envelope = {
      success: false,
      error: {
        code,
        message,
        details,
      },
    }
  }
}

export interface MockAuthSessionState {
  customerId: number | null
  accessToken: string | null
  refreshToken: string | null
  blacklistedRefreshTokens: string[]
  staffId: number | null
  csrfToken: string | null
  pendingOtps: Record<string, { code: string; expiresAt: number }>
}

function getDefaultAuthSession(): MockAuthSessionState {
  return {
    customerId: null,
    accessToken: null,
    refreshToken: null,
    blacklistedRefreshTokens: [],
    staffId: null,
    csrfToken: null,
    pendingOtps: {},
  }
}

let memoryDb: MockDatabaseState | null = null
let memoryAuth: MockAuthSessionState | null = null

export function readMockDb(): MockDatabaseState {
  if (import.meta.client) {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        memoryDb = JSON.parse(raw) as MockDatabaseState
        return memoryDb
      }
    } catch {
      memoryDb = null
    }
  }
  if (!memoryDb) {
    memoryDb = getInitialMockDatabase()
    writeMockDb(memoryDb)
  }
  return memoryDb
}

export function writeMockDb(db: MockDatabaseState): void {
  memoryDb = db
  if (import.meta.client) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(db))
    } catch {
      return
    }
  }
}

export function readMockAuthSession(): MockAuthSessionState {
  if (import.meta.client) {
    try {
      const raw = localStorage.getItem(AUTH_SESSION_KEY)
      if (raw) {
        memoryAuth = JSON.parse(raw) as MockAuthSessionState
        return memoryAuth
      }
    } catch {
      memoryAuth = null
    }
  }
  if (!memoryAuth) {
    memoryAuth = getDefaultAuthSession()
    writeMockAuthSession(memoryAuth)
  }
  return memoryAuth
}

export function writeMockAuthSession(auth: MockAuthSessionState): void {
  memoryAuth = auth
  if (import.meta.client) {
    try {
      localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(auth))
    } catch {
      return
    }
  }
}

export function resetMockEnvironment(): void {
  memoryDb = getInitialMockDatabase()
  memoryAuth = getDefaultAuthSession()
  if (import.meta.client) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(memoryDb))
    localStorage.setItem(AUTH_SESSION_KEY, JSON.stringify(memoryAuth))
  }
}

export function normalizeIranPhone(rawPhone: string): string {
  if (!rawPhone || !rawPhone.trim()) {
    throw new MockApiError(422, 'VALIDATION_ERROR', 'شماره موبایل الزامی است.', {
      phone: 'این فیلد الزامی است.',
    })
  }
  let digits = String(rawPhone)
    .replace(/[\u06f0-\u06f9]/g, ch => String(ch.charCodeAt(0) - 0x06f0))
    .replace(/[\u0660-\u0669]/g, ch => String(ch.charCodeAt(0) - 0x0660))
    .replace(/\D/g, '')

  if (digits.startsWith('0098')) {
    digits = digits.slice(4)
  } else if (digits.startsWith('98') && digits.length === 12) {
    digits = digits.slice(2)
  }
  if (digits.length === 10 && digits.startsWith('9')) {
    digits = `0${digits}`
  }
  if (digits.length !== 11 || !digits.startsWith('09')) {
    throw new MockApiError(422, 'VALIDATION_ERROR', 'فرمت شماره موبایل نامعتبر است.', {
      phone: 'شماره موبایل باید ۱۱ رقم و با ۰۹ شروع شود.',
    })
  }
  return digits
}

export function computeIsRestaurantOpen(
  openTime: string,
  closeTime: string,
  isTemporarilyClosed: boolean,
  nowDate = new Date()
): boolean {
  if (isTemporarilyClosed) return false
  const [oh, om] = openTime.split(':').map(Number)
  const [ch, cm] = closeTime.split(':').map(Number)
  if (
    oh === undefined ||
    om === undefined ||
    ch === undefined ||
    cm === undefined ||
    Number.isNaN(oh) ||
    Number.isNaN(om) ||
    Number.isNaN(ch) ||
    Number.isNaN(cm)
  ) {
    return false
  }
  const openMin = oh * 60 + om
  const closeMin = ch * 60 + cm
  if (openMin === closeMin) return false
  const currentMin = nowDate.getHours() * 60 + nowDate.getMinutes()
  if (openMin < closeMin) {
    return currentMin >= openMin && currentMin < closeMin
  }
  return currentMin >= openMin || currentMin < closeMin
}

export function delayMock(ms = 90): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}
