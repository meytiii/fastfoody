<script setup lang="ts">
import { onMounted } from 'vue'
import { Toaster } from 'vue-sonner'
import { useCartStore } from '~/stores/cart'
import TheHeader from '~/components/TheHeader.vue'
import TheFooter from '~/components/TheFooter.vue'
import FloatingCartPill from '~/components/FloatingCartPill.vue'
import CartDrawer from '~/components/CartDrawer.vue'
import MobileDrawer from '~/components/MobileDrawer.vue'
import SearchModal from '~/components/SearchModal.vue'
import ProductDetailModal from '~/components/ProductDetailModal.vue'

const cartStore = useCartStore()

onMounted(() => {
  cartStore.initFromStorage()
})
</script>

<template>
  <div class="flex min-h-screen flex-col bg-white text-[var(--color-text-primary)] selection:bg-[var(--color-accent-gold-soft)] selection:text-[var(--color-brand-forest)]">
    <!-- Navigation Header -->
    <TheHeader />

    <!-- Main View Content -->
    <div class="flex-1">
      <NuxtPage />
    </div>

    <!-- Site Footer -->
    <TheFooter />

    <!-- Global Floating Cart Pill -->
    <FloatingCartPill />

    <!-- Global Modals & Drawers -->
    <CartDrawer />
    <MobileDrawer />
    <SearchModal />
    <ProductDetailModal />

    <!-- Notifications Sonner Toaster -->
    <Toaster
      position="bottom-left"
      dir="rtl"
      :toast-options="{
        style: {
          fontFamily: 'var(--font-persian)',
          borderRadius: '16px',
          border: '1px solid var(--color-border-subtle)',
          boxShadow: 'var(--shadow-md)',
          background: '#FFFFFF',
          color: 'var(--color-text-primary)',
        },
      }"
    />
  </div>
</template>
