import { defineStore } from 'pinia'
import type {
  CartItem,
  CartItemAddOn,
  CartProductSnapshot,
  DeliveryType,
  OrderCreatePayload,
  ProductDetailPublic,
  ProductSummaryPublic,
} from '~/types'
import { useCmsStore } from './cms'

const CART_STORAGE_KEY = 'fastfoody_cart_v2'
const MAX_CART_ITEM_QUANTITY = 99

function isValidCartItem(raw: unknown): raw is CartItem {
  if (!raw || typeof raw !== 'object') return false
  const obj = raw as Record<string, unknown>
  return (
    typeof obj.id === 'string' &&
    typeof obj.productId === 'number' &&
    typeof obj.quantity === 'number' &&
    Array.isArray(obj.selectedAddons) &&
    typeof obj.unitPrice === 'number' &&
    typeof obj.totalPrice === 'number'
  )
}

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

    estimatedDeliveryFee(): number {
      if (this.subtotal === 0) return 0
      const cms = useCmsStore()
      return cms.inZoneFee
    },

    estimatedPrepMinutes(): number {
      if (this.items.length === 0) return 0
      const cms = useCmsStore()
      const maxPrep = Math.max(...this.items.map(i => i.product.prep_time_minutes || 0))
      return maxPrep + cms.prepBufferMinutes
    },

    isEmpty: (state): boolean => {
      return state.items.length === 0
    },
  },

  actions: {
    initFromStorage() {
      if (!import.meta.client || this.initialized) return
      try {
        const saved = localStorage.getItem(CART_STORAGE_KEY)
        if (saved) {
          const parsed = JSON.parse(saved)
          if (Array.isArray(parsed)) {
            this.items = parsed.filter(isValidCartItem)
          }
        }
      } catch {
        this.items = []
      } finally {
        this.initialized = true
      }
    },

    persist() {
      if (!import.meta.client) return
      try {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(this.items))
      } catch {
        return
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
      product: ProductDetailPublic | ProductSummaryPublic | CartProductSnapshot,
      quantity = 1,
      addons: CartItemAddOn[] = []
    ) {
      if (product.status !== 'AVAILABLE') {
        return
      }

      const normalizedAddons = addons
        .filter(a => a.quantity > 0)
        .map(a => ({ ...a }))
        .sort((a, b) => a.addon_id - b.addon_id)

      const addonSignature = normalizedAddons
        .map(a => `${a.addon_id}:${a.quantity}`)
        .join('-')
      const itemId = `${product.id}_${addonSignature || 'base'}`

      const categoryId =
        'category' in product ? product.category.id : product.category_id

      const snapshot: CartProductSnapshot = {
        id: product.id,
        slug: product.slug,
        name: product.name,
        price: product.price,
        compare_at_price: product.compare_at_price,
        prep_time_minutes: product.prep_time_minutes,
        image_url: product.image_url,
        status: product.status,
        category_id: categoryId,
      }

      const addonsTotal = normalizedAddons.reduce(
        (sum, a) => sum + a.price * a.quantity,
        0
      )
      const existing = this.items.find(item => item.id === itemId)

      if (existing) {
        const nextQty = existing.quantity + quantity
        existing.quantity = Math.max(1, Math.min(nextQty, MAX_CART_ITEM_QUANTITY))
        existing.product = snapshot
        existing.unitPrice = snapshot.price
        existing.addonsTotal = addonsTotal
        existing.totalPrice = existing.unitPrice * existing.quantity + addonsTotal
      } else {
        const safeQty = Math.min(quantity, MAX_CART_ITEM_QUANTITY)
        if (safeQty <= 0) return
        this.items.push({
          id: itemId,
          productId: snapshot.id,
          product: snapshot,
          quantity: safeQty,
          selectedAddons: normalizedAddons,
          unitPrice: snapshot.price,
          addonsTotal,
          totalPrice: snapshot.price * safeQty + addonsTotal,
        })
      }

      this.persist()
    },

    updateQuantity(itemId: string, delta: number) {
      const item = this.items.find(i => i.id === itemId)
      if (!item) return

      const newQty = item.quantity + delta
      if (newQty <= 0) {
        this.removeItem(itemId)
        return
      }

      if (newQty > MAX_CART_ITEM_QUANTITY) {
        return
      }

      item.quantity = newQty
      item.totalPrice = item.unitPrice * item.quantity + item.addonsTotal
      this.persist()
    },

    removeItem(itemId: string) {
      this.items = this.items.filter(i => i.id !== itemId)
      this.persist()
    },

    clearCart() {
      this.items = []
      this.persist()
    },

    buildOrderPayload(
      deliveryType: DeliveryType,
      addressId: number | null,
      notesToKitchen = ''
    ): OrderCreatePayload {
      return {
        delivery_type: deliveryType,
        address_id: deliveryType === 'DELIVERY' ? addressId : null,
        notes_to_kitchen: notesToKitchen,
        items: this.items.map(item => ({
          product_id: item.productId,
          quantity: item.quantity,
          addons: item.selectedAddons.map(a => ({
            addon_id: a.addon_id,
            quantity: a.quantity,
          })),
        })),
      }
    },
  },
})
