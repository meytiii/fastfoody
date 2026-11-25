<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  ArrowRight,
  Clock,
  RefreshCw,
  CheckCircle2,
  XCircle,
  CreditCard,
  MapPin,
  Store,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { storefrontApi } from '~/services/api'
import { useAuthStore } from '~/stores/auth'
import { usePersian } from '~/composables/usePersian'
import type { OrderRead } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const route = useRoute()
const authStore = useAuthStore()
const { formatToman, toPersianDigits, formatTime, formatDateTime, formatCountdown } = usePersian()

const orderId = Number(route.params.id)
const order = ref<OrderRead | null>(null)
const loading = ref(true)
const error = ref('')
const retrying = ref(false)
const remainingSeconds = ref(0)
const lastUpdatedText = ref('')

let pollHandle: ReturnType<typeof setInterval> | null = null
let countdownHandle: ReturnType<typeof setInterval> | null = null

const isLiveStatus = computed(() => {
  if (!order.value) return false
  return (
    order.value.status === 'PENDING_PAYMENT' ||
    order.value.status === 'PROCESSING' ||
    order.value.status === 'READY'
  )
})

const updateExpiryCountdown = () => {
  if (!order.value || order.value.status !== 'PENDING_PAYMENT' || !order.value.expires_at) {
    remainingSeconds.value = 0
    return
  }
  const diff = Math.floor((new Date(order.value.expires_at).getTime() - Date.now()) / 1000)
  remainingSeconds.value = Math.max(0, diff)
}

const fetchOrder = async (silent = false) => {
  if (!silent) loading.value = true
  error.value = ''
  try {
    order.value = await storefrontApi.orders.getOrder(orderId)
    updateExpiryCountdown()
    lastUpdatedText.value = formatTime(new Date().toISOString())
  } catch (err: any) {
    error.value = err?.message || 'سفارش یافت نشد.'
  } finally {
    loading.value = false
  }
}

const handleRetryPayment = async () => {
  if (!order.value) return
  retrying.value = true
  try {
    const res = await storefrontApi.payments.retryPayment(order.value.id)
    await navigateTo(res.payment_url)
  } catch (err: any) {
    toast.error(err?.message || 'امکان شروع پرداخت وجود ندارد')
    retrying.value = false
  }
}

const activeStepIndex = computed(() => {
  if (!order.value) return 0
  switch (order.value.status) {
    case 'PENDING_PAYMENT':
      return 0
    case 'PROCESSING':
      return 1
    case 'READY':
      return 2
    case 'COMPLETED':
      return 3
    default:
      return -1
  }
})

onMounted(async () => {
  await authStore.hydrateSession()
  if (!authStore.isAuthenticated) {
    loading.value = false
    return
  }
  await fetchOrder(false)
  pollHandle = setInterval(() => {
    if (isLiveStatus.value) {
      fetchOrder(true)
    }
  }, 12_000)
  countdownHandle = setInterval(() => {
    updateExpiryCountdown()
  }, 1000)
})

onUnmounted(() => {
  if (pollHandle) clearInterval(pollHandle)
  if (countdownHandle) clearInterval(countdownHandle)
})

useHead(() => ({
  title: order.value
    ? `پیگیری سفارش #${toPersianDigits(order.value.daily_number || order.value.id)} | فست‌فودی`
    : 'جزئیات سفارش | فست‌فودی',
}))
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-cream)]/40 py-8 sm:py-14">
    <div class="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 space-y-6">
      <div class="flex items-center justify-between gap-4">
        <NuxtLink
          to="/orders"
          class="inline-flex items-center gap-2 text-xs font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)]"
        >
          <ArrowRight :size="15" aria-hidden="true" class="icon-directional" />
          <span>بازگشت به لیست سفارش‌ها</span>
        </NuxtLink>

        <div v-if="order && isLiveStatus" class="flex items-center gap-3 text-xs text-[var(--color-text-secondary)]">
          <span>به‌روزرسانی خودکار هر ۱۲ ثانیه (آخرین: {{ lastUpdatedText }})</span>
          <button
            type="button"
            @click="fetchOrder(false)"
            class="touch-target inline-flex items-center gap-1 rounded-full border border-[var(--color-border-subtle)] bg-white px-3 py-1.5 font-bold text-[var(--color-brand-forest)]"
          >
            <RefreshCw :size="13" aria-hidden="true" />
            <span>بروزرسانی</span>
          </button>
        </div>
      </div>

      <div
        v-if="!authStore.isAuthenticated"
        class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 text-center space-y-4"
      >
        <p class="text-sm font-bold text-[var(--color-text-primary)]">
          برای مشاهده جزئیات این سفارش ابتدا وارد حساب کاربری شوید.
        </p>
        <GooeyButton variant="primary" size="md" @click="authStore.openAuthModal(() => fetchOrder(false))">
          <span>ورود با کد پیامکی</span>
        </GooeyButton>
      </div>

      <div v-else-if="loading" class="h-80 rounded-3xl bg-white border border-[var(--color-border-subtle)] animate-pulse" />

      <div
        v-else-if="error || !order"
        role="alert"
        class="rounded-3xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-bg)] p-8 text-center space-y-3"
      >
        <p class="text-sm font-bold text-[var(--color-danger)]">{{ error || 'سفارش یافت نشد' }}</p>
        <NuxtLink to="/orders" class="text-xs font-bold text-[var(--color-brand-forest)] underline">
          بازگشت به سفارش‌های من
        </NuxtLink>
      </div>

      <template v-else>
        <section class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 sm:p-8 shadow-[var(--shadow-sm)] space-y-6">
          <div class="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--color-border-subtle)] pb-5">
            <div class="space-y-1">
              <h1 class="text-xl sm:text-2xl font-extrabold text-[var(--color-brand-forest)]">
                {{ order.daily_number ? `سفارش نوبت #${toPersianDigits(order.daily_number)}` : `سفارش #${toPersianDigits(order.id)}` }}
              </h1>
              <p class="text-xs text-[var(--color-text-secondary)]">
                زمان ثبت: {{ formatDateTime(order.created_at) }}
              </p>
            </div>

            <div class="text-end space-y-1">
              <p class="text-lg font-extrabold text-[var(--color-brand-forest)]">
                {{ formatToman(order.total_amount) }}
              </p>
              <p class="text-xs text-[var(--color-text-secondary)]">
                زمان آماده‌سازی: {{ toPersianDigits(order.prep_time_minutes) }} دقیقه
                <span v-if="order.expected_ready_at">
                  (تحویل حدود <bdi>{{ formatTime(order.expected_ready_at) }}</bdi>)
                </span>
              </p>
            </div>
          </div>

          <div
            v-if="order.status === 'CANCELED'"
            role="alert"
            class="rounded-2xl border border-[var(--color-danger)]/30 bg-[var(--color-danger-bg)] p-4 text-xs space-y-1.5 text-[var(--color-danger)]"
          >
            <div class="flex items-center gap-2 font-bold text-sm">
              <XCircle :size="18" aria-hidden="true" />
              <span>این سفارش لغو شده است</span>
            </div>
            <p v-if="order.cancellation_reason">علت: {{ order.cancellation_reason }}</p>
            <p v-if="order.payment_status === 'AWAITING_REFUND'" class="font-bold">
              وضعیت مالی: در انتظار عودت وجه توسط مدیریت رستوران.
            </p>
            <p v-else-if="order.payment_status === 'REFUNDED'" class="font-bold text-[var(--color-brand-success)]">
              وجه سفارش به کارت <bdi>{{ order.refund_card_number }}</bdi> با کد پیگیری <bdi>{{ order.refund_tracking_code }}</bdi> عودت داده شد.
            </p>
          </div>

          <div v-else class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div
              v-for="(label, idx) in ['در انتظار پرداخت', 'در حال آماده‌سازی', 'آماده تحویل', 'تحویل‌داده‌شده']"
              :key="label"
              class="rounded-2xl border p-3.5 text-xs transition-colors"
              :class="
                idx <= activeStepIndex
                  ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] font-bold'
                  : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-muted)]'
              "
            >
              <div class="flex items-center justify-between mb-1">
                <span>مرحله {{ toPersianDigits(idx + 1) }}</span>
                <CheckCircle2 v-if="idx <= activeStepIndex" :size="15" aria-hidden="true" />
              </div>
              <p>{{ label }}</p>
            </div>
          </div>

          <div
            v-if="order.status === 'PENDING_PAYMENT' && order.payment_status === 'UNPAID'"
            class="flex flex-col sm:flex-row items-center justify-between gap-4 rounded-2xl border border-[var(--color-warning)]/30 bg-[var(--color-warning-bg)] p-4"
          >
            <div class="flex items-center gap-2.5 text-xs font-bold text-[var(--color-warning)]">
              <Clock :size="18" aria-hidden="true" class="shrink-0" />
              <span v-if="remainingSeconds > 0">
                مهلت پرداخت آنلاین: <bdi>{{ formatCountdown(remainingSeconds) }}</bdi> (پس از انقضا، سفارش خودکار لغو می‌شود)
              </span>
              <span v-else>
                مهلت پرداخت به پایان رسیده است.
              </span>
            </div>
            <GooeyButton
              v-if="remainingSeconds > 0"
              variant="primary"
              size="sm"
              :disabled="retrying"
              @click="handleRetryPayment"
            >
              <CreditCard :size="15" aria-hidden="true" />
              <span>{{ retrying ? 'در حال انتقال...' : 'پرداخت سفارش' }}</span>
            </GooeyButton>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 space-y-1.5">
              <p class="font-bold text-[var(--color-text-primary)] flex items-center gap-1.5">
                <MapPin v-if="order.delivery_type === 'DELIVERY'" :size="15" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <Store v-else :size="15" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <span>{{ order.delivery_type === 'DELIVERY' ? 'ارسال با پیک' : 'تحویل حضوری' }}</span>
              </p>
              <p v-if="order.delivery_address_snapshot" class="text-[var(--color-text-secondary)] leading-relaxed">
                {{ order.delivery_address_snapshot }}
              </p>
              <p class="text-[var(--color-text-secondary)]">
                تحویل‌گیرنده: {{ order.delivery_recipient_name }} <bdi>{{ toPersianDigits(order.delivery_recipient_phone) }}</bdi>
              </p>
            </div>

            <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 space-y-1.5">
              <p class="font-bold text-[var(--color-text-primary)]">یادداشت برای آشپزخانه</p>
              <p class="text-[var(--color-text-secondary)]">
                {{ order.notes_to_kitchen || 'یادداشتی ثبت نشده است.' }}
              </p>
            </div>
          </div>

          <div class="space-y-3">
            <h2 class="text-sm font-bold text-[var(--color-text-primary)]">
              جزئیات اقلام فاکتور (قیمت ثابت لحظه سفارش)
            </h2>
            <div class="divide-y divide-[var(--color-border-subtle)] rounded-2xl border border-[var(--color-border-subtle)]">
              <div
                v-for="item in order.items"
                :key="item.id"
                class="flex items-start justify-between gap-4 p-4 text-xs"
              >
                <div class="space-y-1">
                  <p class="font-bold text-[var(--color-text-primary)]">
                    {{ item.product_name_snapshot }}
                    <span class="text-[var(--color-text-secondary)]">
                      ({{ toPersianDigits(item.quantity) }} × {{ formatToman(item.unit_price_snapshot) }})
                    </span>
                  </p>
                  <p
                    v-for="addon in item.addons"
                    :key="addon.addon_id"
                    class="text-[11px] text-[var(--color-text-secondary)]"
                  >
                    + {{ addon.addon_name_snapshot }} ({{ toPersianDigits(addon.quantity) }} × {{ formatToman(addon.unit_price_snapshot) }})
                  </p>
                </div>
                <strong class="text-[var(--color-brand-forest)] shrink-0">
                  {{ formatToman(item.line_total) }}
                </strong>
              </div>
            </div>

            <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-[var(--color-text-secondary)]">
                <span>جمع اقلام:</span>
                <strong>{{ formatToman(order.subtotal) }}</strong>
              </div>
              <div class="flex items-center justify-between text-[var(--color-text-secondary)]">
                <span>هزینه ارسال:</span>
                <strong>{{ order.delivery_fee === 0 ? 'رایگان' : formatToman(order.delivery_fee) }}</strong>
              </div>
              <div class="flex items-center justify-between pt-2 border-t border-[var(--color-border-subtle)] text-sm font-extrabold text-[var(--color-brand-forest)]">
                <span>مبلغ کل:</span>
                <span>{{ formatToman(order.total_amount) }}</span>
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>
