<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CheckCircle2, XCircle, RefreshCw, ArrowLeft } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { storefrontApi } from '~/services/api'
import { useAuthStore } from '~/stores/auth'
import { usePersian } from '~/composables/usePersian'
import type { OrderRead, PaymentPublic } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const route = useRoute()
const authStore = useAuthStore()
const { formatToman, toPersianDigits, formatTime } = usePersian()

const queryStatus = String(route.query.status || '')
const authority = String(route.query.authority || '')

const loading = ref(true)
const payment = ref<PaymentPublic | null>(null)
const order = ref<OrderRead | null>(null)
const error = ref('')
const retrying = ref(false)

onMounted(async () => {
  await authStore.hydrateSession()
  if (!authority) {
    error.value = 'شناسه تراکنش در آدرس بازگشت موجود نیست.'
    loading.value = false
    return
  }
  try {
    const res = await storefrontApi.payments.getPaymentStatus(authority)
    payment.value = res.payment
    order.value = await storefrontApi.orders.getOrder(res.order_id)
  } catch (err: any) {
    error.value = err?.message || 'امکان استعلام وضعیت پرداخت وجود ندارد.'
  } finally {
    loading.value = false
  }
})

const handleRetryPayment = async () => {
  if (!order.value) return
  retrying.value = true
  try {
    const res = await storefrontApi.payments.retryPayment(order.value.id)
    await navigateTo(res.payment_url)
  } catch (err: any) {
    toast.error(err?.message || 'امکان شروع مجدد پرداخت وجود ندارد')
    retrying.value = false
  }
}

const isSuccess = () => {
  return payment.value ? payment.value.status === 'SUCCEEDED' : queryStatus === 'success'
}

useHead({
  title: 'نتیجه پرداخت | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-cream)]/50 py-12 px-4">
    <div class="mx-auto max-w-lg rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 shadow-[var(--shadow-lg)] space-y-6 text-center">
      <div v-if="loading" class="py-10 text-xs text-[var(--color-text-secondary)]">
        در حال استعلام نتیجه تراکنش...
      </div>

      <template v-else-if="error">
        <div class="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-danger-bg)] text-[var(--color-danger)]">
          <XCircle :size="36" aria-hidden="true" />
        </div>
        <h1 class="text-xl font-extrabold text-[var(--color-text-primary)]">
          خطا در دریافت اطلاعات پرداخت
        </h1>
        <p class="text-xs text-[var(--color-text-secondary)]">{{ error }}</p>
        <NuxtLink
          to="/orders"
          class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-6 py-3 text-xs font-bold text-white"
        >
          مشاهده سفارش‌های من
        </NuxtLink>
      </template>

      <template v-else-if="isSuccess()">
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-success-bg)] text-[var(--color-brand-success)]">
          <CheckCircle2 :size="44" aria-hidden="true" />
        </div>
        <h1 class="text-2xl font-extrabold text-[var(--color-brand-forest)]">
          پرداخت با موفقیت انجام شد
        </h1>
        <p class="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
          سفارش شما ثبت و به آشپزخانه ارسال شد.
        </p>

        <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 text-xs space-y-2 text-start">
          <div v-if="order?.daily_number" class="flex items-center justify-between">
            <span class="text-[var(--color-text-secondary)]">شماره نوبت روزانه:</span>
            <strong class="text-base font-extrabold text-[var(--color-brand-forest)]">
              <bdi>#{{ toPersianDigits(order.daily_number) }}</bdi>
            </strong>
          </div>
          <div v-if="payment?.ref_id" class="flex items-center justify-between">
            <span class="text-[var(--color-text-secondary)]">کد رهگیری بانکی:</span>
            <strong><bdi>{{ toPersianDigits(payment.ref_id) }}</bdi></strong>
          </div>
          <div v-if="payment" class="flex items-center justify-between">
            <span class="text-[var(--color-text-secondary)]">مبلغ پرداخت‌شده:</span>
            <strong>{{ formatToman(payment.amount) }}</strong>
          </div>
          <div v-if="order?.expected_ready_at" class="flex items-center justify-between">
            <span class="text-[var(--color-text-secondary)]">ساعت تقریبی آماده‌سازی:</span>
            <strong><bdi>{{ formatTime(order.expected_ready_at) }}</bdi></strong>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row gap-3 pt-2">
          <GooeyButton
            v-if="order"
            variant="primary"
            size="md"
            class="flex-1"
            @click="navigateTo(`/orders/${order.id}`)"
          >
            <span>پیگیری زنده سفارش</span>
            <ArrowLeft :size="16" aria-hidden="true" class="icon-directional" />
          </GooeyButton>

          <NuxtLink
            to="/menu"
            class="touch-target inline-flex items-center justify-center rounded-full border border-[var(--color-border-subtle)] bg-white px-6 py-3 text-xs font-bold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)]"
          >
            بازگشت به منو
          </NuxtLink>
        </div>
      </template>

      <template v-else>
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-danger-bg)] text-[var(--color-danger)]">
          <XCircle :size="44" aria-hidden="true" />
        </div>
        <h1 class="text-2xl font-extrabold text-[var(--color-danger)]">
          پرداخت ناموفق بود
        </h1>
        <p class="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
          تراکنش تکمیل نشد. سفارش شما تا پایان مهلت ۱۵ دقیقه‌ای همچنان در انتظار پرداخت باقی می‌ماند و می‌توانید مجدداً تلاش کنید.
        </p>

        <div class="flex flex-col sm:flex-row gap-3 pt-2">
          <GooeyButton
            v-if="order && order.status === 'PENDING_PAYMENT'"
            variant="primary"
            size="md"
            :disabled="retrying"
            class="flex-1"
            @click="handleRetryPayment"
          >
            <RefreshCw :size="16" aria-hidden="true" />
            <span>{{ retrying ? 'در حال انتقال...' : 'تلاش مجدد برای پرداخت' }}</span>
          </GooeyButton>

          <NuxtLink
            v-if="order"
            :to="`/orders/${order.id}`"
            class="touch-target inline-flex items-center justify-center rounded-full border border-[var(--color-border-subtle)] bg-white px-6 py-3 text-xs font-bold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-cream)]"
          >
            مشاهده جزئیات سفارش
          </NuxtLink>
        </div>
      </template>
    </div>
  </main>
</template>
