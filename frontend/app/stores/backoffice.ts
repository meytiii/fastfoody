import { defineStore } from 'pinia'
import { backofficeApi } from '~/services/api'
import { readMockAuthSession } from '~/services/mockDatabase'
import type { StaffProfile } from '~/types'

export const useBackofficeStore = defineStore('backoffice', {
  state: () => ({
    staff: null as StaffProfile | null,
    csrfToken: null as string | null,
    hydrated: false,
  }),

  getters: {
    isAuthenticated: (state): boolean => Boolean(state.staff && state.csrfToken),
  },

  actions: {
    async hydrateSession() {
      if (this.hydrated) return
      try {
        const session = readMockAuthSession()
        if (session.staffId && session.csrfToken) {
          this.csrfToken = session.csrfToken
          this.staff = await backofficeApi.auth.me()
        }
      } catch {
        this.staff = null
        this.csrfToken = null
      } finally {
        this.hydrated = true
      }
    },

    async login(phone: string, password: string) {
      const res = await backofficeApi.auth.login({ phone, password })
      this.staff = res.user
      this.csrfToken = res.csrf_token
      return res
    },

    async logout() {
      await backofficeApi.auth.logout()
      this.staff = null
      this.csrfToken = null
    },
  },
})
