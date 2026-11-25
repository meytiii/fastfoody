import { defineStore } from 'pinia'
import { storefrontApi } from '~/services/api'
import type { MediaAssetPublic, RestaurantStatus, SiteSectionsMap } from '~/types'

export const useCmsStore = defineStore('cms', {
  state: () => ({
    restaurantStatus: null as RestaurantStatus | null,
    siteSections: null as SiteSectionsMap | null,
    mediaAssets: [] as MediaAssetPublic[],
    loading: false,
    loaded: false,
    error: null as string | null,
  }),

  getters: {
    isOpen: (state): boolean => {
      return state.restaurantStatus?.is_open ?? true
    },

    inZoneFee: (state): number => {
      return state.restaurantStatus?.in_zone_delivery_fee ?? 50000
    },

    outZoneFee: (state): number => {
      return state.restaurantStatus?.out_zone_delivery_fee ?? 100000
    },

    prepBufferMinutes: (state): number => {
      return state.restaurantStatus?.prep_time_buffer_minutes ?? 5
    },

    announcement: (state) => {
      return state.siteSections?.announcement ?? { text: '', is_active: false, link: '' }
    },

    heroSection: (state) => {
      return state.siteSections?.hero
    },

    headerSection: (state) => {
      return state.siteSections?.header
    },

    footerSection: (state) => {
      return state.siteSections?.footer
    },

    luckyWheelSection: (state) => {
      return state.siteSections?.lucky_wheel
    },

    aboutUsSection: (state) => {
      return state.siteSections?.about_us
    },
  },

  actions: {
    async fetchAll(force = false) {
      if (this.loaded && !force) return
      this.loading = true
      this.error = null
      try {
        const [status, sections, assets] = await Promise.all([
          storefrontApi.cms.getRestaurantStatus(),
          storefrontApi.cms.getSiteSections(),
          storefrontApi.cms.getMediaAssets(),
        ])
        this.restaurantStatus = status
        this.siteSections = sections
        this.mediaAssets = assets
        this.loaded = true
      } catch (err: any) {
        this.error = err?.message || 'خطا در دریافت تنظیمات رستوران'
      } finally {
        this.loading = false
      }
    },

    async refreshStatus() {
      try {
        this.restaurantStatus = await storefrontApi.cms.getRestaurantStatus()
      } catch {
        return
      }
    },
  },
})
