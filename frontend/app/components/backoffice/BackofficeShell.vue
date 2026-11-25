<script setup lang="ts">
import { onMounted, ref } from 'vue'
import {
  ChefHat,
  ExternalLink,
  LogOut,
  RotateCcw,
  Settings,
  ShoppingBag,
  Users,
  Utensils,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { resetMockEnvironment } from '~/services/mockDatabase'
import { useAuthStore } from '~/stores/auth'
import { useBackofficeStore } from '~/stores/backoffice'
import { useCmsStore } from '~/stores/cms'
import { useMenuStore } from '~/stores/menu'

defineProps<{
  title: string
  subtitle?: string
}>()

const emit = defineEmits<{
  reset: []
}>()

const route = useRoute()
const router = useRouter()
const backofficeStore = useBackofficeStore()
const cmsStore = useCmsStore()
const authStore = useAuthStore()
const menuStore = useMenuStore()
const { toPersianDigits } = usePersian()

const resetting = ref(false)

const navItems = [
  { to: '/backoffice', label: 'POS زنده آشپزخانه', icon: ChefHat },
  { to: '/backoffice/orders', label: 'سفارش‌ها و عودت', icon: ShoppingBag },
  { to: '/backoffice/catalog', label: 'کاتالوگ و موجودی', icon: Utensils },
  { to: '/backoffice/customers', label: 'مشتریان (CRM)', icon: Users },
  { to: '/backoffice/cms', label: 'تنظیمات و CMS', icon: Settings },
]

function isActiveNav(path: string): boolean {
  if (path === '/backoffice') return route.path === '/backoffice'
  return route.path.startsWith(path)
}

async function handleLogout() {
  await backofficeStore.logout()
  toast.success('از پنل مدیریت خارج شدید')
  await router.replace('/backoffice/login')
}

async function handleResetDemoData() {
  resetting.value = true
  try {
    resetMockEnvironment()
    backofficeStore.hydrated = false
    authStore.hydrated = false
    await backofficeStore.hydrateSession()
    await Promise.all([cmsStore.fetchAll(true), menuStore.fetchMenu(true), authStore.hydrateSession()])
    toast.success('داده‌های آزمایشی به وضعیت اولیه بازنشانی شد')
    if (!backofficeStore.isAuthenticated) {
      await router.replace('/backoffice/login')
      return
    }
    emit('reset')
  } finally {
    resetting.value = false
  }
}

onMounted(async () => {
  await Promise.all([backofficeStore.hydrateSession(), cmsStore.fetchAll()])
  if (!backofficeStore.isAuthenticated) {
    await router.replace('/backoffice/login')
  }
})
</script>

<template>
  <div class="min-h-screen bg-[#FAF7F2] text-[#292B27]">
    <div
      v-if="!backofficeStore.hydrated || !backofficeStore.isAuthenticated"
      class="flex min-h-screen items-center justify-center p-6"
    >
      <div class="w-full max-w-sm rounded-3xl border border-[#E8E5DC] bg-white p-8 text-center shadow-sm">
        <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-[#F4EFE3] border-t-[#183A2D]" />
        <p class="text-sm font-semibold text-[#5A5D56]">در حال بررسی نشست مدیریت...</p>
      </div>
    </div>

    <template v-else>
      <header class="no-print border-b border-[#E8E5DC] bg-white">
        <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div class="flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#183A2D] text-white">
              <ChefHat class="h-6 w-6" />
            </div>
            <div>
              <p class="text-base font-extrabold text-[#292B27]">پنل مدیریت فست‌فودی</p>
              <p class="text-xs text-[#5A5D56]">
                {{ backofficeStore.staff?.full_name || 'مدیر رستوران' }}
                <span dir="ltr" class="mr-1.5 font-semibold">({{ toPersianDigits(backofficeStore.staff?.phone) }})</span>
              </p>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <span
              class="rounded-full px-3.5 py-1.5 text-xs font-bold"
              :class="cmsStore.isOpen ? 'bg-[#EDF7ED] text-[#1E5E22]' : 'bg-[#FDE8E8] text-[#A61B1B]'"
            >
              {{ cmsStore.isOpen ? 'رستوران باز است' : 'رستوران بسته است' }}
            </span>

            <button
              type="button"
              :disabled="resetting"
              class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2 text-xs font-semibold text-[#292B27] transition-colors hover:bg-[#F4EFE3] disabled:opacity-60"
              @click="handleResetDemoData"
            >
              <RotateCcw class="h-3.5 w-3.5" />
              <span>بازنشانی داده‌های آزمایشی</span>
            </button>

            <NuxtLink
              to="/"
              class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#E8E5DC] bg-white px-3.5 py-2 text-xs font-semibold text-[#183A2D] transition-colors hover:bg-[#F4EFE3]"
            >
              <ExternalLink class="h-3.5 w-3.5" />
              <span>مشاهده فروشگاه</span>
            </NuxtLink>

            <button
              type="button"
              class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#A61B1B]/25 bg-[#FDE8E8] px-3.5 py-2 text-xs font-semibold text-[#A61B1B] transition-colors hover:bg-[#A61B1B] hover:text-white"
              @click="handleLogout"
            >
              <LogOut class="h-3.5 w-3.5" />
              <span>خروج</span>
            </button>
          </div>
        </div>

        <nav
          aria-label="منوی مدیریت"
          class="mx-auto flex max-w-7xl items-center gap-2 overflow-x-auto border-t border-[#E8E5DC] px-4 py-2.5 sm:px-6"
        >
          <NuxtLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="touch-target inline-flex shrink-0 items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold transition-colors"
            :class="
              isActiveNav(item.to)
                ? 'bg-[#183A2D] text-white'
                : 'text-[#5A5D56] hover:bg-[#F4EFE3] hover:text-[#292B27]'
            "
          >
            <component :is="item.icon" class="h-4 w-4" />
            <span>{{ item.label }}</span>
          </NuxtLink>
        </nav>
      </header>

      <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <div class="no-print mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 class="text-2xl font-extrabold text-[#292B27] sm:text-3xl">{{ title }}</h1>
            <p v-if="subtitle" class="mt-1 text-sm text-[#5A5D56]">{{ subtitle }}</p>
          </div>
          <slot name="header-actions" />
        </div>
        <slot />
      </main>
    </template>
  </div>
</template>
