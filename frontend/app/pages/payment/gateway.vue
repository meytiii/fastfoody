<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-vue-next'
import { storefrontApi } from '~/services/api'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const route = useRoute()
const { formatToman, toPersianDigits } = usePersian()

const authority = String(route.query.authority || '')
const orderId = Number(route.query.order_id || 0)

const amount = ref<number | null>(null)
const processing = ref(false)
const errorMsg = ref('')

onMounted(async () => {
  if (!authority) return
  try {
    const info = await storefrontApi.payments.getPaymentStatus(authority)
    amount.value = info.payment.amount
  } catch {
    errorMsg.value = 'اطلاعات تراکنش در دسترس نیست یا متعلق به کاربر فعلی نیست.'
  }
})

const simulateGatewayAction = async (status: 'OK' | 'NOK') => {
  if (!authority) return
  processing.value = true
  try {
    const result = await storefrontApi.payments.verifyMockCallback(authority, status)
    await navigateTo(
      `/payment/result?status=${result.status}&authority=${encodeURIComponent(result.authority)}`
    )
  } catch (err: any) {
    errorMsg.value = err?.message || 'خطا در تایید تراکنش آزمایشی.'
    processing.value = false
  }
}

useHead({
  title: 'درگاه پرداخت آزمایشی زرین‌پال | فست‌فودی',
})
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-ivory)] flex items-center justify-center p-4">
    <div class="w-full max-w-md rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 sm:p-8 shadow-[var(--shadow-lg)] space-y-6">
      <div class="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-4">
        <div class="flex items-center gap-2.5">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-accent-gold-soft)] text-[var(--color-accent-gold-text)]">
            <ShieldCheck :size="22" aria-hidden="true" />
          </div>
          <div>
            <h1 class="text-base font-extrabold text-[var(--color-text-primary)]">
              شبیه‌ساز درگاه پرداخت زرین‌پال
            </h1>
            <p class="text-[11px] text-[var(--color-text-secondary)]">
              محیط آزمایشی بدون اتصال بانکی واقعی
            </p>
          </div>
        </div>
      </div>

      <div v-if="errorMsg" role="alert" class="rounded-2xl bg-[var(--color-danger-bg)] p-4 text-xs font-bold text-[var(--color-danger)]">
        {{ errorMsg }}
      </div>

      <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 space-y-2 text-xs">
        <div class="flex items-center justify-between">
          <span class="text-[var(--color-text-secondary)]">پذیرنده:</span>
          <strong class="text-[var(--color-brand-forest)]">فست‌فودی</strong>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-[var(--color-text-secondary)]">شماره سفارش:</span>
          <strong><bdi>#{{ toPersianDigits(orderId) }}</bdi></strong>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-[var(--color-text-secondary)]">شناسه مرجع (Authority):</span>
          <bdi class="font-mono text-[11px] text-[var(--color-text-primary)]">{{ authority }}</bdi>
        </div>
        <div v-if="amount !== null" class="flex items-center justify-between pt-2 border-t border-[var(--color-border-subtle)] text-sm">
          <span class="font-bold text-[var(--color-text-primary)]">مبلغ قابل پرداخت:</span>
          <strong class="font-extrabold text-[var(--color-brand-forest)]">{{ formatToman(amount) }}</strong>
        </div>
      </div>

      <div class="space-y-3">
        <GooeyButton
          type="button"
          variant="primary"
          size="lg"
          :disabled="processing || !authority"
          class="w-full"
          @click="simulateGatewayAction('OK')"
        >
          <CheckCircle2 :size="18" aria-hidden="true" />
          <span>{{ processing ? 'در حال ثبت...' : 'پرداخت موفق (بازگشت با تایید)' }}</span>
        </GooeyButton>

        <button
          type="button"
          :disabled="processing || !authority"
          @click="simulateGatewayAction('NOK')"
          class="touch-target flex w-full items-center justify-center gap-2 rounded-full border border-[var(--color-danger)]/40 bg-[var(--color-danger-bg)] px-5 py-3 text-xs font-bold text-[var(--color-danger)] hover:bg-[var(--color-danger)] hover:text-white transition-colors"
        >
          <XCircle :size="16" aria-hidden="true" />
          <span>انصراف یا خطای پرداخت (بازگشت ناموفق)</span>
        </button>
      </div>
    </div>
  </main>
</template>
