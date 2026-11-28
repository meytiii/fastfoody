<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { Toaster } from 'vue-sonner'
import { useCartStore } from '~/stores/cart'
import { useCmsStore } from '~/stores/cms'
import { useAuthStore } from '~/stores/auth'
import { useMenuStore } from '~/stores/menu'
import AnnouncementBar from '~/components/AnnouncementBar.vue'
import TheHeader from '~/components/TheHeader.vue'
import TheFooter from '~/components/TheFooter.vue'
import FloatingCartPill from '~/components/FloatingCartPill.vue'
import CartDrawer from '~/components/CartDrawer.vue'
import MobileDrawer from '~/components/MobileDrawer.vue'
import SearchModal from '~/components/SearchModal.vue'
import ProductDetailModal from '~/components/ProductDetailModal.vue'
import AuthModal from '~/components/AuthModal.vue'
import AuroraBackground from '~/components/ui/AuroraBackground.vue'

const cartStore = useCartStore()
const cmsStore = useCmsStore()
const authStore = useAuthStore()
const menuStore = useMenuStore()
const route = useRoute()

const isBackofficeRoute = computed(() => route.path.startsWith('/backoffice'))
const isGatewayRoute = computed(() => route.path.startsWith('/payment/gateway'))

onMounted(async () => {
  cartStore.initFromStorage()
  await Promise.all([
    cmsStore.fetchAll(),
    authStore.hydrateSession(),
    menuStore.fetchMenu(),
  ])
})
</script>

<template>
  <div class="relative min-h-screen flex flex-col bg-white text-[var(--color-text-primary)] selection:bg-[var(--color-accent-gold-soft)] selection:text-[var(--color-brand-forest)]">
    <a
      href="#main-content"
      class="visually-hidden focus:fixed focus:top-3 focus:start-3 focus:z-[120] focus:rounded-full focus:bg-[var(--color-brand-forest)] focus:px-4 focus:py-2 focus:text-xs focus:font-bold focus:text-white"
    >
      رفتن به محتوای اصلی
    </a>

    <AuroraBackground v-if="!isBackofficeRoute && !isGatewayRoute" as-backdrop />

    <AnnouncementBar v-if="!isBackofficeRoute && !isGatewayRoute" class="relative z-20" />
    <TheHeader v-if="!isBackofficeRoute && !isGatewayRoute" class="relative z-20" />

    <div id="main-content" tabindex="-1" class="flex-1 relative z-10 outline-none">
      <NuxtPage />
    </div>

    <TheFooter
      v-if="!isBackofficeRoute && !isGatewayRoute && route.path !== '/'"
      class="relative z-10"
    />

    <template v-if="!isBackofficeRoute && !isGatewayRoute">
      <FloatingCartPill />
      <CartDrawer />
      <MobileDrawer />
      <SearchModal />
      <ProductDetailModal />
      <AuthModal />
    </template>

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
