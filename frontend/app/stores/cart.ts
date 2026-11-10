import { defineStore } from 'pinia'
import type { CartItem, Product, ProductModifier, ProductSize } from '~/types'

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [] as CartItem[],
    isOpen: false,
    initialized: false,
  }),

  getters: {
    totalCount: (state): number => {
      return state.items.reduce((acc, item) => acc + item.quantity, 0)
    },

    subtotal: (state): number => {
      return state.items.reduce((acc, item) => acc + item.totalPrice, 0)
    },

    deliveryFee(): number {
      if (this.subtotal === 0) return 0
      // Free delivery on orders over 450,000 Tomans
      return this.subtotal >= 450000 ? 0 : 35000
    },

    packagingFee: (state): number => {
      return state.items.length > 0 ? 15000 : 0
    },

    grandTotal(): number {
      if (this.subtotal === 0) return 0
      return this.subtotal + this.deliveryFee + this.packagingFee
    },

    isEmpty: (state): boolean => {
      return state.items.length === 0
    },
  },

  actions: {
    initFromStorage() {
      if (!import.meta.client || this.initialized) return
      try {
        const saved = localStorage.getItem('fastfoody_cart')
        if (saved) {
          this.items = JSON.parse(saved)
        }
      } catch (e) {
        console.error('Failed to parse cart from storage:', e)
      } finally {
        this.initialized = true
      }
    },

    persist() {
      if (!import.meta.client) return
      try {
        localStorage.setItem('fastfoody_cart', JSON.stringify(this.items))
      } catch (e) {
        console.error('Failed to persist cart:', e)
      }
    },

    openCart() {
      this.isOpen = true
    },

    closeCart() {
      this.isOpen = false
    },

    toggleCart() {
      this.isOpen = !this.isOpen
    },

    addItem(
      product: Product,
      quantity = 1,
      options?: {
        size?: ProductSize
        addons?: ProductModifier[]
        specialInstructions?: string
      }
    ) {
      const selectedSize = options?.size
      const selectedAddons = options?.addons || []
      const instructions = options?.specialInstructions || ''

      // Calculate unit price based on base price, size offset and addons
      const sizeOffset = selectedSize?.priceOffset || 0
      const addonsTotal = selectedAddons.reduce((sum, a) => sum + a.price, 0)
      const unitPrice = product.price + sizeOffset + addonsTotal

      // Create a deterministic item ID based on product ID, size and addons
      const addonIds = selectedAddons.map(a => a.id).sort().join('-')
      const itemId = `${product.id}_${selectedSize?.id || 'standard'}_${addonIds}`

      const existingIndex = this.items.findIndex(item => item.id === itemId)

      if (existingIndex > -1) {
        const item = this.items[existingIndex]
        if (item) {
          item.quantity += quantity
          item.totalPrice = item.quantity * item.unitPrice
        }
      } else {
        this.items.push({
          id: itemId,
          productId: product.id,
          product,
          quantity,
          selectedSize,
          selectedAddons,
          unitPrice,
          totalPrice: unitPrice * quantity,
          specialInstructions: instructions,
        })
      }

      this.persist()
    },

    updateQuantity(itemId: string, delta: number) {
      const index = this.items.findIndex(i => i.id === itemId)
      if (index === -1) return

      const item = this.items[index]
      if (!item) return

      const newQty = item.quantity + delta
      if (newQty <= 0) {
        this.removeItem(itemId)
      } else {
        item.quantity = newQty
        item.totalPrice = item.quantity * item.unitPrice
        this.persist()
      }
    },

    removeItem(itemId: string) {
      this.items = this.items.filter(i => i.id !== itemId)
      this.persist()
    },

    clearCart() {
      this.items = []
      this.persist()
    },
  },
})
