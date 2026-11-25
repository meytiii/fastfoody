import { defineStore } from 'pinia'
import { storefrontApi } from '~/services/api'
import { readMockAuthSession } from '~/services/mockDatabase'
import type {
  CustomerAddress,
  CustomerAddressPayload,
  CustomerProfile,
} from '~/types'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as CustomerProfile | null,
    accessToken: null as string | null,
    refreshToken: null as string | null,
    addresses: [] as CustomerAddress[],
    hydrated: false,
    loadingAddresses: false,
    authModalOpen: false,
    pendingDevOtp: null as string | null,
    onAuthenticatedCallback: null as (() => void) | null,
  }),

  getters: {
    isAuthenticated: (state): boolean => Boolean(state.user && state.accessToken),
    defaultAddress: (state): CustomerAddress | null => {
      return state.addresses.find(a => a.is_default) ?? state.addresses[0] ?? null
    },
  },

  actions: {
    openAuthModal(onSuccess?: () => void) {
      this.onAuthenticatedCallback = onSuccess ?? null
      this.authModalOpen = true
    },

    closeAuthModal() {
      this.authModalOpen = false
      this.onAuthenticatedCallback = null
    },

    async hydrateSession() {
      if (this.hydrated) return
      try {
        const session = readMockAuthSession()
        if (session.customerId && session.accessToken) {
          this.accessToken = session.accessToken
          this.refreshToken = session.refreshToken
          this.user = await storefrontApi.auth.me()
          await this.fetchAddresses()
        }
      } catch {
        this.user = null
        this.accessToken = null
        this.refreshToken = null
        this.addresses = []
      } finally {
        this.hydrated = true
      }
    },

    async requestOtp(phone: string) {
      const res = await storefrontApi.auth.requestOtp({ phone })
      this.pendingDevOtp = res.dev_code ?? null
      return res
    },

    async verifyOtp(phone: string, code: string) {
      const res = await storefrontApi.auth.verifyOtp({ phone, code })
      this.user = res.user
      this.accessToken = res.access
      this.refreshToken = res.refresh
      this.pendingDevOtp = null
      await this.fetchAddresses()
      const cb = this.onAuthenticatedCallback
      this.authModalOpen = false
      this.onAuthenticatedCallback = null
      if (cb) cb()
      return res
    },

    async logout() {
      await storefrontApi.auth.logout()
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.addresses = []
    },

    async fetchAddresses() {
      if (!this.isAuthenticated) {
        this.addresses = []
        return
      }
      this.loadingAddresses = true
      try {
        this.addresses = await storefrontApi.auth.listAddresses()
      } finally {
        this.loadingAddresses = false
      }
    },

    async addAddress(payload: CustomerAddressPayload): Promise<CustomerAddress> {
      const created = await storefrontApi.auth.createAddress(payload)
      await this.fetchAddresses()
      return created
    },

    async updateAddress(
      id: number,
      payload: Partial<CustomerAddressPayload>
    ): Promise<CustomerAddress> {
      const updated = await storefrontApi.auth.updateAddress(id, payload)
      await this.fetchAddresses()
      return updated
    },

    async removeAddress(id: number): Promise<void> {
      await storefrontApi.auth.deleteAddress(id)
      await this.fetchAddresses()
    },
  },
})
