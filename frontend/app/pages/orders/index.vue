<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ReceiptText, ArrowLeft, User, RefreshCw, RotateCcw } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { storefrontApi } from '~/services/api'
import { useAuthStore } from '~/stores/auth'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import type { OrderRead, OrderStatus, PaymentStatus } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const authStore = useAuthStore()
const cartStore = useCartStore()
const { formatToman, toPersianDigits, formatDateTime } = usePersian()

const orders = ref<OrderRead[]>([])
const loading = ref(false)
const error = ref('')
const reorderingOrderId = ref<number | null>(null)

const handleReorder = async (orderId: number) => {
  reorderingOrderId.value = orderId
  try {
    const [reorderRes, catalogRes] = await Promise.all([
      storefrontApi.orders.reorder(orderId),
      storefrontApi.catalog.getProducts({ limit: 100 }),
    ])
    const addedCount = cartStore.applyReorder(reorderRes, catalogRes.results)
    for (const warning of reorderRes.warnings) {
      toast.warning(warning)
    }
    if (addedCount > 0) {
      toast.success(`${toPersianDigits(addedCount)} قلم به سبد خرید اضافه شد`)
      cartStore.openCart()
    } else {
      toast.error('هیچ‌یک از اقلام این سفارش در حال حاضر موجود نیست')
    }
  } catch (err: any) {
    toast.error(err?.message || 'خطا در ثبت سفارش مجدد')
  } finally {
    reorderingOrderId.value = null
  }
}

const statusLabels: Record<OrderStatus, { label: string; tone: string }> = {
  PENDING_PAYMENT: { label: 'در انتظار پرداخت', tone: 'bg-[var(--color-warning-bg)] text-[var(--color-warning)]' },
  PROCESSING: { label: 'در حال آماده‌سازی', tone: 'bg-[var(--color-info-bg)] text-[var(--color-info)]' },
  READY: { label: 'آماده تحویل', tone: 'bg-[var(--color-success-bg)] text-[var(--color-brand-success)]' },
  COMPLETED: { label: 'تکمیل‌شده', tone: 'bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]' },
  CANCELED: { label: 'لغوشده', tone: 'bg-[var(--color-danger-bg)] text-[var(--color-danger)]' },
}

const paymentLabels: Record<PaymentStatus, string> = {
  UNPAID: 'پرداخت‌نشده',
  PAID: 'پرداخت‌شده',
  AWAITING_REFUND: 'در انتظار عودت وجه',
  REFUNDED: 'وجه عودت داده‌شد',
}

const loadOrders = async () => {
  if (!authStore.isAuthenticated) return
  loading.value = true
  error.value = ''
  try {
    const res = await storefrontApi.orders.listOrders(50, 0)
    orders.value = res.results
  } catch (err: any) {
    error.value = err?.message || 'خطا در دریافت لیست سفارش‌ها'
  } finally {
    loading.value = false
  }
}

watch(
  () => authStore.isAuthenticated,
  (loggedIn) => {
    if (loggedIn) loadOrders()
    else orders.value = []
  }
)

onMounted(async () => {
  await authStore.hydrateSession()
  if (authStore.isAuthenticated) {
    await loadOrders()
  }
})

useHead({
  title: 'سفارش‌های من | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-cream)]/40 py-8 sm:py-14">
    <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 space-y-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-[var(--color-brand-forest)]">
            سفارش‌های من و پیگیری زنده
          </h1>
          <p class="mt-1 text-xs sm:text-sm text-[var(--color-text-secondary)]">
            مشاهده وضعیت آماده‌سازی، زمان تحویل و سوابق فاکتورها
          </p>
        </div>

        <button
          v-if="authStore.isAuthenticated"
          type="button"
          @click="loadOrders"
          class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-white px-4 py-2 text-xs font-bold text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)]"
        >
          <RefreshCw :size="14" aria-hidden="true" />
          <span>به‌روزرسانی</span>
        </button>
      </div>

      <div
        v-if="!authStore.isAuthenticated"
        class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 text-center space-y-4 shadow-[var(--shadow-sm)]"
      >
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]">
          <User :size="28" aria-hidden="true" />
        </div>
        <h2 class="text-lg font-bold text-[var(--color-text-primary)]">
          برای مشاهده سفارش‌ها وارد شوید
        </h2>
        <p class="text-xs text-[var(--color-text-secondary)] max-w-sm mx-auto">
          با شماره موبایلی که سفارش را ثبت کرده‌اید وارد شوید تا لیست و وضعیت زنده سفارش‌ها نمایش داده شود.
        </p>
        <GooeyButton variant="primary" size="md" @click="authStore.openAuthModal(loadOrders)">
          <span>ورود با کد پیامکی</span>
        </GooeyButton>
      </div>

      <div v-else-if="loading" class="space-y-3" aria-busy="true">
        <div
          v-for="n in 3"
          :key="n"
          class="h-28 rounded-2xl border border-[var(--color-border-subtle)] bg-white animate-pulse"
        />
      </div>

      <div
        v-else-if="error"
        role="alert"
        class="rounded-3xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-bg)] p-6 text-center space-y-3"
      >
        <p class="text-xs font-bold text-[var(--color-danger)]">{{ error }}</p>
        <GooeyButton variant="primary" size="sm" @click="loadOrders">
          <span>تلاش مجدد</span>
        </GooeyButton>
      </div>

      <div
        v-else-if="orders.length === 0"
        class="rounded-3xl border border-dashed border-[var(--color-border-subtle)] bg-white p-10 text-center space-y-4"
      >
        <ReceiptText :size="36" aria-hidden="true" class="mx-auto text-[var(--color-text-muted)]" />
        <h2 class="text-base font-bold text-[var(--color-text-primary)]">
          هنوز سفارشی ثبت نکرده‌اید
        </h2>
        <NuxtLink
          to="/menu"
          class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-6 py-2.5 text-xs font-bold text-white"
        >
          مشاهده منو و اولین سفارش
        </NuxtLink>
      </div>

      <div v-else class="space-y-4">
        <article
          v-for="order in orders"
          :key="order.id"
          class="rounded-2xl border border-[var(--color-border-subtle)] bg-white p-5 shadow-[var(--shadow-sm)] transition-all hover:border-[var(--color-brand-forest)] hover:shadow-[var(--shadow-md)]"
        >
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap items-center gap-2.5">
              <span class="rounded-xl bg-[var(--color-surface-cream)] px-3 py-1.5 text-xs font-extrabold text-[var(--color-brand-forest)]">
                {{ order.daily_number ? `نوبت #${toPersianDigits(order.daily_number)}` : `سفارش #${toPersianDigits(order.id)}` }}
              </span>
              <span
                class="rounded-full px-3 py-1 text-xs font-bold"
                :class="statusLabels[order.status].tone"
              >
                {{ statusLabels[order.status].label }}
              </span>
              <span
                v-if="order.cancellation_requested && order.status !== 'CANCELED'"
                class="rounded-full bg-[var(--color-warning-bg)] px-2.5 py-1 text-[11px] font-bold text-[var(--color-warning)]"
              >
                درخواست لغو ثبت شده
              </span>
              <span class="text-xs font-medium text-[var(--color-text-secondary)]">
                {{ paymentLabels[order.payment_status] }}
              </span>
            </div>

            <span class="text-sm font-extrabold text-[var(--color-brand-forest)]">
              {{ formatToman(order.total_amount) }}
            </span>
          </div>

          <p class="mt-3 text-xs text-[var(--color-text-secondary)]">
            {{ order.items.map(i => `${i.product_name_snapshot} (${toPersianDigits(i.quantity)})`).join('، ') }}
          </p>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-border-subtle)] pt-3 text-xs">
            <span class="text-[var(--color-text-secondary)]">
              {{ formatDateTime(order.created_at) }}
            </span>
            <div class="flex flex-wrap items-center gap-2">
              <button
                type="button"
                :disabled="reorderingOrderId === order.id"
                class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-3.5 py-1.5 font-bold text-[var(--color-brand-forest)] hover:border-[var(--color-brand-forest)] disabled:opacity-60"
                @click="handleReorder(order.id)"
              >
                <RotateCcw :size="13" aria-hidden="true" />
                <span>{{ reorderingOrderId === order.id ? 'در حال افزودن...' : 'سفارش مجدد' }}</span>
              </button>
              <NuxtLink
                :to="`/orders/${order.id}`"
                class="touch-target inline-flex items-center gap-1 rounded-full bg-[var(--color-brand-forest)] px-4 py-1.5 font-bold text-white hover:bg-[var(--color-brand-forest-light)]"
              >
                <span>پیگیری و جزئیات</span>
                <ArrowLeft :size="14" aria-hidden="true" class="icon-directional" />
              </NuxtLink>
            </div>
          </div>
        </article>
      </div>
    </div>
  </main>
</template>
