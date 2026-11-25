<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { X, Phone, KeyRound, RefreshCw, ArrowLeft } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useAuthStore } from '~/stores/auth'
import { usePersian } from '~/composables/usePersian'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const authStore = useAuthStore()
const { toPersianDigits, toEnglishDigits, formatCountdown } = usePersian()

const dialogRef = ref<HTMLDialogElement | null>(null)
const step = ref<'phone' | 'otp'>('phone')
const phone = ref('')
const code = ref('')
const devCodeHint = ref<string | null>(null)
const phoneError = ref('')
const codeError = ref('')
const isSubmitting = ref(false)
const countdownSeconds = ref(0)
let timerHandle: ReturnType<typeof setInterval> | null = null

const stopTimer = () => {
  if (timerHandle) {
    clearInterval(timerHandle)
    timerHandle = null
  }
}

const startTimer = (seconds: number) => {
  stopTimer()
  countdownSeconds.value = seconds
  timerHandle = setInterval(() => {
    if (countdownSeconds.value <= 1) {
      countdownSeconds.value = 0
      stopTimer()
    } else {
      countdownSeconds.value -= 1
    }
  }, 1000)
}

const requestClose = async () => {
  await closeDialogSmoothly(dialogRef.value)
  authStore.closeAuthModal()
}

useDialogLightDismiss(dialogRef, requestClose)

watch(
  () => authStore.authModalOpen,
  (isOpen) => {
    if (isOpen) {
      step.value = 'phone'
      code.value = ''
      phoneError.value = ''
      codeError.value = ''
      devCodeHint.value = null
      dialogRef.value?.showModal()
    } else {
      stopTimer()
      if (dialogRef.value?.open) {
        dialogRef.value.close()
      }
    }
  }
)

onUnmounted(() => {
  stopTimer()
})

const canResend = computed(() => countdownSeconds.value === 0 && !isSubmitting.value)

const handleRequestOtp = async () => {
  phoneError.value = ''
  const cleaned = toEnglishDigits(phone.value).replace(/\D/g, '')
  if (!cleaned) {
    phoneError.value = 'لطفاً شماره موبایل خود را وارد کنید.'
    return
  }

  isSubmitting.value = true
  try {
    const res = await authStore.requestOtp(cleaned)
    devCodeHint.value = res.dev_code ?? null
    step.value = 'otp'
    code.value = ''
    startTimer(res.expires_in || 120)
    toast.success('کد تایید ارسال شد')
  } catch (err: any) {
    phoneError.value = err?.message || 'خطا در ارسال کد تایید.'
  } finally {
    isSubmitting.value = false
  }
}

const handleVerifyOtp = async () => {
  codeError.value = ''
  const cleanedCode = toEnglishDigits(code.value).replace(/\D/g, '')
  if (cleanedCode.length !== 6) {
    codeError.value = 'کد تایید باید ۶ رقم باشد.'
    return
  }

  isSubmitting.value = true
  try {
    await authStore.verifyOtp(toEnglishDigits(phone.value), cleanedCode)
    stopTimer()
    toast.success('ورود با موفقیت انجام شد')
  } catch (err: any) {
    codeError.value = err?.message || 'کد تایید نامعتبر است.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <dialog
    ref="dialogRef"
    closedby="any"
    aria-labelledby="auth-modal-title"
    @close="authStore.closeAuthModal"
    class="modal-top-layer fixed inset-0 m-auto z-50 w-[94%] max-w-md rounded-3xl border border-[var(--color-border-subtle)] bg-white p-0 shadow-[var(--shadow-lg)]"
  >
    <div class="flex flex-col overflow-hidden">
      <div class="flex items-center justify-between border-b border-[var(--color-border-subtle)] px-6 py-4">
        <h1 id="auth-modal-title" class="text-base font-bold text-[var(--color-brand-forest)]">
          {{ step === 'phone' ? 'ورود یا ثبت‌نام با موبایل' : 'تایید کد پیامکی' }}
        </h1>
        <button
          type="button"
          @click="requestClose"
          class="touch-target flex h-10 w-10 items-center justify-center rounded-full text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-cream)]"
          aria-label="بستن پنجره ورود"
        >
          <X :size="20" aria-hidden="true" />
        </button>
      </div>

      <div class="p-6">
        <form v-if="step === 'phone'" @submit.prevent="handleRequestOtp" class="space-y-4">
          <p class="text-xs leading-relaxed text-[var(--color-text-secondary)]">
            برای ثبت سفارش، مشاهده وضعیت لحظه‌ای و مدیریت آدرس‌ها، شماره موبایل خود را وارد کنید.
          </p>

          <div class="space-y-1.5">
            <label for="auth-phone-input" class="block text-xs font-bold text-[var(--color-text-primary)]">
              شماره موبایل <span aria-hidden="true">*</span>
            </label>
            <div class="relative">
              <Phone :size="16" aria-hidden="true" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
              <input
                id="auth-phone-input"
                v-model="phone"
                type="tel"
                name="phone"
                inputmode="tel"
                autocomplete="tel"
                enterkeyhint="next"
                required
                autofocus
                placeholder="۰۹۱۲۰۰۰۰۰۰۰"
                :aria-invalid="Boolean(phoneError)"
                :aria-describedby="phoneError ? 'auth-phone-error' : 'auth-phone-hint'"
                @input="phoneError = ''"
                dir="ltr"
                class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white ps-10 pe-3.5 text-sm text-[var(--color-text-primary)] text-end focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
              />
            </div>
            <p id="auth-phone-hint" class="text-[11px] text-[var(--color-text-secondary)]">
              مثال: ۰۹۱۲۰۰۰۰۰۰۰ (کاربر نمونه برای آزمایش: <bdi>09120000000</bdi>)
            </p>
            <p v-if="phoneError" id="auth-phone-error" role="alert" class="text-xs font-medium text-[var(--color-danger)]">
              {{ phoneError }}
            </p>
          </div>

          <GooeyButton
            type="submit"
            variant="primary"
            size="md"
            :disabled="isSubmitting"
            class="w-full"
          >
            <span>{{ isSubmitting ? 'در حال ارسال کد...' : 'ارسال کد تایید' }}</span>
            <ArrowLeft :size="16" aria-hidden="true" class="icon-directional" />
          </GooeyButton>
        </form>

        <form v-else @submit.prevent="handleVerifyOtp" class="space-y-4">
          <div class="flex items-center justify-between text-xs text-[var(--color-text-secondary)]">
            <span>
              کد ۶ رقمی به شماره <strong class="text-[var(--color-text-primary)]"><bdi>{{ toPersianDigits(phone) }}</bdi></strong> ارسال شد.
            </span>
            <button
              type="button"
              @click="step = 'phone'"
              class="font-bold text-[var(--color-brand-forest)] hover:underline"
            >
              تغییر شماره
            </button>
          </div>

          <div
            v-if="devCodeHint"
            class="rounded-xl border border-[var(--color-info)]/30 bg-[var(--color-info-bg)] px-3.5 py-2.5 text-xs text-[var(--color-text-primary)]"
          >
            <span>حالت آزمایشی (شبیه‌ساز کنسول سرور): کد تایید شما </span>
            <button
              type="button"
              @click="code = devCodeHint"
              class="font-extrabold text-[var(--color-brand-forest)] underline mx-1"
            >
              <bdi>{{ devCodeHint }}</bdi>
            </button>
          </div>

          <div class="space-y-1.5">
            <label for="auth-otp-input" class="block text-xs font-bold text-[var(--color-text-primary)]">
              کد تایید ۶ رقمی <span aria-hidden="true">*</span>
            </label>
            <div class="relative">
              <KeyRound :size="16" aria-hidden="true" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
              <input
                id="auth-otp-input"
                v-model="code"
                type="text"
                name="one-time-code"
                inputmode="numeric"
                autocomplete="one-time-code"
                autocorrect="off"
                autocapitalize="none"
                spellcheck="false"
                enterkeyhint="done"
                maxlength="6"
                required
                autofocus
                placeholder="۱۲۳۴۵۶"
                :aria-invalid="Boolean(codeError)"
                :aria-describedby="codeError ? 'auth-code-error' : undefined"
                @input="codeError = ''"
                dir="ltr"
                class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white ps-10 pe-3.5 text-center text-base font-bold tracking-[0.3em] text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
              />
            </div>
            <p v-if="codeError" id="auth-code-error" role="alert" class="text-xs font-medium text-[var(--color-danger)]">
              {{ codeError }}
            </p>
          </div>

          <div class="flex items-center justify-between text-xs">
            <span v-if="countdownSeconds > 0" class="text-[var(--color-text-secondary)]">
              زمان باقی‌مانده: <strong>{{ formatCountdown(countdownSeconds) }}</strong>
            </span>
            <button
              v-else
              type="button"
              :disabled="!canResend"
              @click="handleRequestOtp"
              class="inline-flex items-center gap-1.5 font-bold text-[var(--color-brand-forest)] hover:underline"
            >
              <RefreshCw :size="13" aria-hidden="true" />
              <span>ارسال مجدد کد</span>
            </button>
          </div>

          <GooeyButton
            type="submit"
            variant="primary"
            size="md"
            :disabled="isSubmitting"
            class="w-full"
          >
            <span>{{ isSubmitting ? 'در حال بررسی...' : 'تایید و ورود' }}</span>
          </GooeyButton>
        </form>
      </div>
    </div>
  </dialog>
</template>
