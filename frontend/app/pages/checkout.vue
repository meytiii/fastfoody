<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import {
  MapPin,
  Store,
  Plus,
  CreditCard,
  ShieldCheck,
  ArrowRight,
  Clock,
  AlertTriangle,
  User,
  Tag,
  X,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useCartStore } from '~/stores/cart'
import { useAuthStore } from '~/stores/auth'
import { useCmsStore } from '~/stores/cms'
import { usePersian } from '~/composables/usePersian'
import { storefrontApi } from '~/services/api'
import type { DeliveryType, ValidatePromoResponse } from '~/types'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const authStore = useAuthStore()
const cmsStore = useCmsStore()
const { toPersianDigits, formatToman, toEnglishDigits } = usePersian()

useHead({
  title: 'تکمیل و پرداخت سفارش | فست‌فودی',
})

const deliveryType = ref<DeliveryType>('DELIVERY')
const selectedAddressId = ref<number | null>(null)
const notesToKitchen = ref('')
const isSubmitting = ref(false)
const showNewAddressForm = ref(false)

const promoCodeInput = ref('')
const appliedPromo = ref<ValidatePromoResponse | null>(null)
const validatingPromo = ref(false)
const promoError = ref('')

const newAddress = ref({
  title: '',
  recipient_name: '',
  recipient_phone: '',
  address_text: '',
  is_out_of_zone: false,
  is_default: true,
  replace_address_id: null as number | null,
})
const savingAddress = ref(false)

watch(
  () => authStore.addresses,
  (list) => {
    if (list.length > 0 && !list.some(a => a.id === selectedAddressId.value)) {
      selectedAddressId.value = authStore.defaultAddress?.id ?? list[0]!.id
    }
    if (list.length >= 4 && !newAddress.value.replace_address_id) {
      const fallback = list.find(a => !a.is_default) ?? list[0]
      newAddress.value.replace_address_id = fallback ? fallback.id : null
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await cmsStore.refreshStatus()
  await authStore.hydrateSession()
  if (authStore.isAuthenticated && authStore.addresses.length === 0) {
    showNewAddressForm.value = true
  }
})

const selectedAddress = computed(() => {
  return authStore.addresses.find(a => a.id === selectedAddressId.value) ?? null
})

const deliveryFee = computed(() => {
  if (cartStore.isEmpty) return 0
  if (deliveryType.value === 'PICKUP') return 0
  if (!selectedAddress.value) return cmsStore.inZoneFee
  return selectedAddress.value.is_out_of_zone ? cmsStore.outZoneFee : cmsStore.inZoneFee
})

const packagingFee = computed(() => {
  if (cartStore.isEmpty) return 0
  return cmsStore.packagingFee
})

const belowMinDeliveryAmount = computed(() => {
  return (
    deliveryType.value === 'DELIVERY' &&
    !cartStore.isEmpty &&
    cmsStore.minDeliveryAmount > 0 &&
    cartStore.subtotal < cmsStore.minDeliveryAmount
  )
})

const discountAmount = computed(() => appliedPromo.value?.discount_amount ?? 0)

const grandTotal = computed(() => {
  return Math.max(
    0,
    cartStore.subtotal + deliveryFee.value + packagingFee.value - discountAmount.value
  )
})

const handleApplyPromo = async () => {
  const code = promoCodeInput.value.trim()
  if (!code) {
    promoError.value = 'لطفاً کد تخفیف را وارد کنید.'
    return
  }
  if (!authStore.isAuthenticated) {
    authStore.openAuthModal(() => {
      void handleApplyPromo()
    })
    return
  }
  validatingPromo.value = true
  promoError.value = ''
  try {
    const res = await storefrontApi.orders.validatePromo({
      code,
      subtotal: cartStore.subtotal,
    })
    appliedPromo.value = res
    promoCodeInput.value = res.code
    toast.success(`کد تخفیف ${res.code} اعمال شد`)
  } catch (err: any) {
    appliedPromo.value = null
    promoError.value = err?.message || 'کد تخفیف معتبر نیست.'
  } finally {
    validatingPromo.value = false
  }
}

const clearPromo = () => {
  appliedPromo.value = null
  promoCodeInput.value = ''
  promoError.value = ''
}

const handleCreateAddress = async () => {
  if (!newAddress.value.address_text.trim()) {
    toast.error('لطفاً نشانی کامل پستی را وارد کنید')
    return
  }
  if (authStore.isAddressLimitReached && !newAddress.value.replace_address_id) {
    toast.error('به سقف ۴ نشانی رسیده‌اید؛ یک نشانی را برای جایگزینی انتخاب کنید')
    return
  }
  savingAddress.value = true
  try {
    const created = await authStore.addAddress({
      title: newAddress.value.title,
      recipient_name: newAddress.value.recipient_name || authStore.user?.full_name || '',
      recipient_phone:
        toEnglishDigits(newAddress.value.recipient_phone) || authStore.user?.phone || '',
      address_text: newAddress.value.address_text,
      is_out_of_zone: newAddress.value.is_out_of_zone,
      is_default: newAddress.value.is_default,
      ...(authStore.isAddressLimitReached && newAddress.value.replace_address_id
        ? { replace_address_id: newAddress.value.replace_address_id }
        : {}),
    })
    selectedAddressId.value = created.id
    showNewAddressForm.value = false
    newAddress.value = {
      title: '',
      recipient_name: '',
      recipient_phone: '',
      address_text: '',
      is_out_of_zone: false,
      is_default: false,
      replace_address_id: null,
    }
    toast.success('آدرس جدید ثبت شد')
  } catch (err: any) {
    toast.error(err?.message || 'خطا در ثبت آدرس')
  } finally {
    savingAddress.value = false
  }
}

const submitOrderAndPay = async () => {
  if (cartStore.isEmpty) {
    toast.error('سبد خرید شما خالی است')
    return
  }
  if (!cmsStore.isOpen) {
    toast.error('رستوران در حال حاضر خارج از ساعت کاری است')
    return
  }
  if (belowMinDeliveryAmount.value) {
    toast.error(
      `حداقل مبلغ سفارش برای ارسال با پیک ${formatToman(cmsStore.minDeliveryAmount)} است.`
    )
    return
  }
  if (!authStore.isAuthenticated) {
    authStore.openAuthModal(() => {
      if (authStore.addresses.length === 0) {
        showNewAddressForm.value = true
      }
    })
    return
  }
  if (deliveryType.value === 'DELIVERY' && !selectedAddressId.value) {
    toast.error('لطفاً یک آدرس ارسال انتخاب یا ثبت کنید')
    showNewAddressForm.value = true
    return
  }

  isSubmitting.value = true
  try {
    const payload = cartStore.buildOrderPayload(
      deliveryType.value,
      selectedAddressId.value,
      notesToKitchen.value,
      appliedPromo.value?.code
    )
    const order = await storefrontApi.orders.createOrder(payload)
    const payment = await storefrontApi.payments.requestPayment(order.id)
    cartStore.clearCart()
    await navigateTo(payment.payment_url)
  } catch (err: any) {
    toast.error(err?.message || 'خطا در ثبت سفارش یا اتصال به درگاه')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-cream)]/50 py-8 sm:py-14">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-6">
        <NuxtLink
          to="/menu"
          class="inline-flex items-center gap-2 text-xs font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)]"
        >
          <ArrowRight :size="15" aria-hidden="true" class="icon-directional" />
          <span>بازگشت به منوی غذاها</span>
        </NuxtLink>
      </div>

      <div
        v-if="cartStore.isEmpty"
        class="mx-auto max-w-md rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 text-center shadow-[var(--shadow-sm)] space-y-4"
      >
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-surface-cream)] p-4 border border-[var(--color-border-subtle)]">
          <img src="/svg/cart.svg" alt="" width="48" height="48" aria-hidden="true" class="h-12 w-12 object-contain" />
        </div>
        <h1 class="text-lg font-bold text-[var(--color-text-primary)]">
          سبد خرید شما خالی است
        </h1>
        <p class="text-xs text-[var(--color-text-secondary)]">
          برای تکمیل خرید، ابتدا غذاهای مورد نظر خود را به سبد خرید اضافه کنید.
        </p>
        <NuxtLink
          to="/menu"
          class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[var(--color-brand-forest-light)]"
        >
          مشاهده منوی غذاها
        </NuxtLink>
      </div>

      <div v-else class="grid grid-cols-1 gap-8 lg:grid-cols-12 items-start">
        <div class="lg:col-span-8 space-y-6">
          <h1 class="text-2xl font-extrabold text-[var(--color-brand-forest)]">
            تکمیل سفارش و اتصال به درگاه پرداخت
          </h1>

          <div
            v-if="!cmsStore.isOpen"
            role="alert"
            class="flex items-center gap-3 rounded-2xl border border-[var(--color-warning)]/30 bg-[var(--color-warning-bg)] p-4 text-xs font-bold text-[var(--color-warning)]"
          >
            <AlertTriangle :size="18" aria-hidden="true" class="shrink-0" />
            <span>
              رستوران در حال حاضر بسته است و امکان ثبت سفارش جدید وجود ندارد.
            </span>
          </div>

          <div
            v-if="belowMinDeliveryAmount"
            role="alert"
            class="flex items-center gap-3 rounded-2xl border border-[var(--color-warning)]/30 bg-[var(--color-warning-bg)] p-4 text-xs font-bold text-[var(--color-warning)]"
          >
            <AlertTriangle :size="18" aria-hidden="true" class="shrink-0" />
            <span>
              حداقل مبلغ سبد برای ارسال با پیک {{ formatToman(cmsStore.minDeliveryAmount) }} است. برای ادامه، اقلام بیشتری اضافه کنید یا تحویل حضوری را انتخاب نمایید.
            </span>
          </div>

          <section class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
            <div class="flex items-center justify-between border-b border-[var(--color-border-subtle)] pb-3">
              <div class="flex items-center gap-2.5">
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                  {{ toPersianDigits('1') }}
                </div>
                <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                  احراز هویت مشتری
                </h2>
              </div>
              <NuxtLink
                v-if="authStore.isAuthenticated"
                to="/account"
                class="text-xs font-bold text-[var(--color-brand-forest)] hover:underline"
              >
                مدیریت حساب
              </NuxtLink>
            </div>

            <div
              v-if="authStore.isAuthenticated && authStore.user"
              class="flex items-center justify-between rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-4 py-3 text-xs"
            >
              <div class="flex items-center gap-3">
                <User :size="18" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <div>
                  <p class="font-bold text-[var(--color-text-primary)]">
                    {{ authStore.user.full_name || 'کاربر تاییدشده' }}
                  </p>
                  <p class="text-[var(--color-text-secondary)]">
                    شماره موبایل: <bdi>{{ toPersianDigits(authStore.user.phone) }}</bdi>
                  </p>
                </div>
              </div>
              <span class="rounded-full bg-[var(--color-success-bg)] px-2.5 py-1 text-[11px] font-bold text-[var(--color-brand-success)]">
                وارد شده
              </span>
            </div>

            <div v-else class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl border border-dashed border-[var(--color-brand-forest)]/40 bg-[var(--color-surface-cream)] p-4">
              <p class="text-xs text-[var(--color-text-secondary)]">
                برای ثبت سفارش و انتخاب آدرس ارسال، ابتدا با شماره موبایل خود وارد شوید. سبد خرید شما حفظ می‌شود.
              </p>
              <GooeyButton
                type="button"
                variant="primary"
                size="sm"
                class="shrink-0"
                @click="authStore.openAuthModal()"
              >
                <span>ورود با کد پیامکی</span>
              </GooeyButton>
            </div>
          </section>

          <section class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
            <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                {{ toPersianDigits('2') }}
              </div>
              <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                روش دریافت سفارش
              </h2>
            </div>

            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2" role="radiogroup" aria-label="روش دریافت سفارش">
              <label
                class="flex items-start gap-3 rounded-2xl border p-4 transition-[border-color,background-color] duration-200 ease-[var(--ease-out)]"
                :class="
                  deliveryType === 'DELIVERY'
                    ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                    : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                "
              >
                <input
                  v-model="deliveryType"
                  type="radio"
                  value="DELIVERY"
                  name="delivery_type"
                  class="mt-1 accent-[var(--color-brand-forest)]"
                />
                <div>
                  <span class="flex items-center gap-1.5 text-xs font-bold">
                    <MapPin :size="16" aria-hidden="true" />
                    <span>ارسال با پیک به آدرس</span>
                  </span>
                  <p class="text-[11px] text-[var(--color-text-secondary)] mt-1 font-normal">
                    درون‌محدوده: {{ formatToman(cmsStore.inZoneFee) }} | برون‌محدوده: {{ formatToman(cmsStore.outZoneFee) }}
                  </p>
                </div>
              </label>

              <label
                class="flex items-start gap-3 rounded-2xl border p-4 transition-[border-color,background-color] duration-200 ease-[var(--ease-out)]"
                :class="
                  deliveryType === 'PICKUP'
                    ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                    : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                "
              >
                <input
                  v-model="deliveryType"
                  type="radio"
                  value="PICKUP"
                  name="delivery_type"
                  class="mt-1 accent-[var(--color-brand-forest)]"
                />
                <div>
                  <span class="flex items-center gap-1.5 text-xs font-bold">
                    <Store :size="16" aria-hidden="true" />
                    <span>تحویل حضوری از رستوران</span>
                  </span>
                  <p class="text-[11px] text-[var(--color-text-secondary)] mt-1 font-normal">
                    بدون هزینه ارسال (رایگان)
                  </p>
                </div>
              </label>
            </div>

            <div v-if="deliveryType === 'PICKUP'" class="rounded-2xl bg-[var(--color-surface-cream)] p-4 text-xs text-[var(--color-text-secondary)]">
              <p class="font-bold text-[var(--color-text-primary)] mb-1">نشانی تحویل حضوری:</p>
              <p>{{ cmsStore.footerSection?.address || 'تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴' }}</p>
            </div>

            <div v-else-if="authStore.isAuthenticated" class="space-y-4 pt-2">
              <div class="flex items-center justify-between">
                <h3 class="text-xs font-bold text-[var(--color-text-primary)]">
                  انتخاب از آدرس‌های ذخیره‌شده
                </h3>
                <button
                  type="button"
                  @click="showNewAddressForm = !showNewAddressForm"
                  class="touch-target inline-flex items-center gap-1 px-2 text-xs font-bold text-[var(--color-brand-forest)] hover:underline"
                >
                  <Plus :size="14" aria-hidden="true" />
                  <span>{{ showNewAddressForm ? 'بستن فرم آدرس' : 'افزودن آدرس جدید' }}</span>
                </button>
              </div>

              <div v-if="authStore.addresses.length > 0" class="grid grid-cols-1 gap-3">
                <label
                  v-for="addr in authStore.addresses"
                  :key="addr.id"
                  class="flex items-start gap-3 rounded-2xl border p-4 transition-[border-color,background-color] duration-200 ease-[var(--ease-out)]"
                  :class="
                    selectedAddressId === addr.id
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] ring-2 ring-[var(--color-brand-forest)]/15'
                      : 'border-[var(--color-border-subtle)] bg-white'
                  "
                >
                  <input
                    v-model="selectedAddressId"
                    type="radio"
                    :value="addr.id"
                    name="address_id"
                    class="mt-1 accent-[var(--color-brand-forest)]"
                  />
                  <div class="flex-1 text-xs space-y-1">
                    <div class="flex flex-wrap items-center justify-between gap-2">
                      <span class="font-bold text-[var(--color-text-primary)]">
                        {{ addr.title || 'آدرس ثبت‌شده' }}
                        <span v-if="addr.is_default" class="text-[10px] font-semibold text-[var(--color-brand-forest)]">
                          (پیش‌فرض)
                        </span>
                      </span>
                      <span
                        class="rounded-full px-2.5 py-0.5 text-[10px] font-bold"
                        :class="
                          addr.is_out_of_zone
                            ? 'bg-[var(--color-warning-bg)] text-[var(--color-warning)]'
                            : 'bg-[var(--color-success-bg)] text-[var(--color-brand-success)]'
                        "
                      >
                        {{ addr.is_out_of_zone ? `برون‌محدوده (${formatToman(cmsStore.outZoneFee)})` : `درون‌محدوده (${formatToman(cmsStore.inZoneFee)})` }}
                      </span>
                    </div>
                    <p class="text-[var(--color-text-secondary)] leading-relaxed">
                      {{ addr.address_text }}
                    </p>
                    <p v-if="addr.recipient_name || addr.recipient_phone" class="text-[11px] text-[var(--color-text-secondary)]">
                      تحویل‌گیرنده: {{ addr.recipient_name }} <bdi>{{ toPersianDigits(addr.recipient_phone) }}</bdi>
                    </p>
                  </div>
                </label>
              </div>

              <form
                v-if="showNewAddressForm || authStore.addresses.length === 0"
                @submit.prevent="handleCreateAddress"
                class="rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 p-4 space-y-3"
              >
                <h4 class="text-xs font-bold text-[var(--color-brand-forest)]">
                  ثبت آدرس جدید
                </h4>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div class="space-y-1">
                    <label for="addr-title" class="block text-xs font-bold text-[var(--color-text-primary)]">
                      عنوان (مثلاً خانه)
                    </label>
                    <input
                      id="addr-title"
                      v-model="newAddress.title"
                      type="text"
                      placeholder="منزل یا محل کار"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-3 focus:ring-[rgba(24,58,45,0.12)]"
                    />
                  </div>
                  <div class="space-y-1">
                    <label for="addr-recipient" class="block text-xs font-bold text-[var(--color-text-primary)]">
                      نام تحویل‌گیرنده
                    </label>
                    <input
                      id="addr-recipient"
                      v-model="newAddress.recipient_name"
                      type="text"
                      autocomplete="name"
                      placeholder="نام کامل"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-3 focus:ring-[rgba(24,58,45,0.12)]"
                    />
                  </div>
                  <div class="space-y-1">
                    <label for="addr-phone" class="block text-xs font-bold text-[var(--color-text-primary)]">
                      تلفن تحویل‌گیرنده
                    </label>
                    <input
                      id="addr-phone"
                      v-model="newAddress.recipient_phone"
                      type="tel"
                      inputmode="tel"
                      autocomplete="tel"
                      dir="ltr"
                      placeholder="۰۹۱۲..."
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3 text-xs text-end focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-3 focus:ring-[rgba(24,58,45,0.12)]"
                    />
                  </div>
                </div>

                <div class="space-y-1">
                  <label for="addr-text" class="block text-xs font-bold text-[var(--color-text-primary)]">
                    نشانی کامل پستی <span aria-hidden="true">*</span>
                  </label>
                  <textarea
                    id="addr-text"
                    v-model="newAddress.address_text"
                    rows="2"
                    required
                    autocomplete="street-address"
                    placeholder="خیابان، کوچه، پلاک، طبقه و واحد..."
                    class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-white p-3 text-xs"
                  />
                </div>

                <div
                  v-if="authStore.isAddressLimitReached"
                  class="space-y-1.5 rounded-xl border border-[#D6A84B]/50 bg-[#F8F3E8] p-3 text-xs"
                >
                  <p class="font-bold text-[#8A651C]">
                    حداکثر ۴ نشانی ذخیره می‌شود؛ یکی از نشانی‌ها را برای جایگزینی انتخاب کنید:
                  </p>
                  <label for="checkout-replace-addr" class="visually-hidden">انتخاب نشانی برای جایگزینی</label>
                  <select
                    id="checkout-replace-addr"
                    v-model.number="newAddress.replace_address_id"
                    class="h-10 w-full rounded-xl border border-[#E8E5DC] bg-white px-3 text-xs text-[#292B27]"
                  >
                    <option
                      v-for="addr in authStore.addresses"
                      :key="addr.id"
                      :value="addr.id"
                    >
                      {{ addr.title || 'نشانی' }}: {{ addr.address_text }}
                    </option>
                  </select>
                </div>

                <div class="flex flex-wrap items-center justify-between gap-3">
                  <label class="inline-flex items-center gap-2 text-xs font-semibold text-[var(--color-text-primary)]">
                    <input
                      v-model="newAddress.is_out_of_zone"
                      type="checkbox"
                      class="h-4 w-4 accent-[var(--color-brand-forest)]"
                    />
                    <span>آدرس خارج از محدوده اصلی است ({{ formatToman(cmsStore.outZoneFee) }})</span>
                  </label>

                  <GooeyButton type="submit" variant="primary" size="sm" :disabled="savingAddress">
                    <span>
                      {{
                        savingAddress
                          ? 'در حال ذخیره...'
                          : authStore.isAddressLimitReached
                            ? 'جایگزینی و ذخیره آدرس'
                            : 'ذخیره آدرس'
                      }}
                    </span>
                  </GooeyButton>
                </div>
              </form>
            </div>
          </section>

          <section class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
            <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
              <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                {{ toPersianDigits('3') }}
              </div>
              <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                یادداشت برای آشپزخانه و پرداخت آنلاین
              </h2>
            </div>

            <div class="space-y-1.5">
              <label for="notes-to-kitchen" class="block text-xs font-bold text-[var(--color-text-primary)]">
                توضیحات سفارش برای آشپزخانه (اختیاری)
              </label>
              <textarea
                id="notes-to-kitchen"
                v-model="notesToKitchen"
                rows="2"
                maxlength="300"
                placeholder="مثال: سس کنار غذا ارسال شود، بدون پیاز..."
                class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-white p-3 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none"
              />
            </div>

            <div class="flex items-start gap-3 rounded-2xl border border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] p-4">
              <CreditCard :size="20" aria-hidden="true" class="mt-0.5 shrink-0 text-[var(--color-brand-forest)]" />
              <div class="text-xs space-y-1">
                <p class="font-bold text-[var(--color-brand-forest)]">
                  پرداخت آنلاین از طریق درگاه زرین‌پال
                </p>
                <p class="text-[var(--color-text-secondary)]">
                  پس از ثبت سفارش، ۱۵ دقیقه برای تکمیل پرداخت اینترنتی فرصت دارید و بلافاصله شماره نوبت روزانه صادر می‌شود.
                </p>
              </div>
            </div>

            <GooeyButton
              type="button"
              variant="primary"
              size="lg"
              :disabled="isSubmitting || !cmsStore.isOpen || belowMinDeliveryAmount"
              class="w-full !py-4"
              @click="submitOrderAndPay"
            >
              <ShieldCheck :size="18" aria-hidden="true" />
              <span v-if="isSubmitting">در حال ثبت سفارش و انتقال به درگاه...</span>
              <span v-else-if="!authStore.isAuthenticated">ورود و ادامه پرداخت ({{ formatToman(grandTotal) }})</span>
              <span v-else>ثبت سفارش و پرداخت ({{ formatToman(grandTotal) }})</span>
            </GooeyButton>
          </section>
        </div>

        <aside class="sticky top-24 lg:col-span-4 space-y-4">
          <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
            <div class="border-b border-[var(--color-border-subtle)] pb-3 flex items-center justify-between">
              <h2 class="text-sm font-bold text-[var(--color-text-primary)]">
                خلاصه سفارش ({{ toPersianDigits(cartStore.totalCount) }} مورد)
              </h2>
              <span class="inline-flex items-center gap-1 text-xs font-semibold text-[var(--color-brand-forest)]">
                <Clock :size="13" aria-hidden="true" />
                <span>{{ toPersianDigits(cartStore.estimatedPrepMinutes) }} دقیقه</span>
              </span>
            </div>

            <div class="max-h-[280px] overflow-y-auto space-y-3 pe-1">
              <div
                v-for="item in cartStore.items"
                :key="item.id"
                class="flex items-start justify-between gap-3 text-xs"
              >
                <div class="flex items-start gap-2.5 min-w-0">
                  <img
                    :src="item.product.image_url || '/img/placeholder.webp'"
                    :alt="item.product.name"
                    width="40"
                    height="40"
                    class="h-10 w-10 rounded-lg object-cover bg-[var(--color-surface-cream)] shrink-0"
                  />
                  <div class="min-w-0">
                    <p class="font-bold text-[var(--color-text-primary)] truncate">
                      {{ item.product.name }}
                    </p>
                    <p class="text-[11px] text-[var(--color-text-secondary)]">
                      {{ toPersianDigits(item.quantity) }} × {{ formatToman(item.unitPrice) }}
                    </p>
                    <p
                      v-for="addon in item.selectedAddons"
                      :key="addon.addon_id"
                      class="text-[10px] text-[var(--color-text-secondary)]"
                    >
                      + {{ addon.name }} ({{ toPersianDigits(addon.quantity) }})
                    </p>
                  </div>
                </div>
                <span class="font-bold text-[var(--color-brand-forest)] shrink-0">
                  {{ formatToman(item.totalPrice) }}
                </span>
              </div>
            </div>

            <div class="border-t border-[var(--color-border-subtle)] pt-4 space-y-2">
              <label for="checkout-promo-code" class="flex items-center gap-1.5 text-xs font-bold text-[var(--color-text-primary)]">
                <Tag :size="14" aria-hidden="true" class="text-[var(--color-brand-forest)]" />
                <span>کد تخفیف</span>
              </label>

              <div v-if="appliedPromo" class="flex items-center justify-between rounded-xl border border-[#1E5E22]/30 bg-[#EDF7ED] px-3 py-2 text-xs">
                <span class="font-bold text-[#1E5E22]">
                  کد <bdi dir="ltr">{{ appliedPromo.code }}</bdi> اعمال شد
                </span>
                <button
                  type="button"
                  class="touch-target inline-flex items-center gap-1 rounded-full px-2 py-1 text-[11px] font-bold text-[#A61B1B] hover:bg-white/70"
                  @click="clearPromo"
                >
                  <X :size="13" aria-hidden="true" />
                  <span>حذف</span>
                </button>
              </div>

              <div v-else class="flex gap-2">
                <input
                  id="checkout-promo-code"
                  v-model="promoCodeInput"
                  type="text"
                  dir="ltr"
                  placeholder="WELCOME20"
                  class="h-10 flex-1 rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 px-3 text-xs uppercase text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none"
                  @keydown.enter.prevent="handleApplyPromo"
                />
                <button
                  type="button"
                  :disabled="validatingPromo"
                  class="touch-target rounded-xl bg-[var(--color-brand-forest)] px-4 text-xs font-bold text-white transition-colors hover:bg-[var(--color-brand-forest-light)] disabled:opacity-60"
                  @click="handleApplyPromo"
                >
                  {{ validatingPromo ? '...' : 'اعمال' }}
                </button>
              </div>
              <p v-if="promoError" role="alert" class="text-[11px] font-medium text-[#A61B1B]">
                {{ promoError }}
              </p>
            </div>

            <div class="border-t border-[var(--color-border-subtle)] pt-4 space-y-2.5 text-xs text-[var(--color-text-secondary)]">
              <div class="flex items-center justify-between">
                <span>جمع اقلام</span>
                <span class="font-bold text-[var(--color-text-primary)]">
                  {{ formatToman(cartStore.subtotal) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>هزینه بسته‌بندی</span>
                <span class="font-bold text-[var(--color-text-primary)]">
                  {{ packagingFee === 0 ? 'رایگان' : formatToman(packagingFee) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>هزینه ارسال</span>
                <span
                  v-if="deliveryFee === 0"
                  class="font-bold text-[var(--color-brand-success)]"
                >
                  رایگان (تحویل حضوری)
                </span>
                <span v-else class="font-bold text-[var(--color-text-primary)]">
                  {{ formatToman(deliveryFee) }}
                </span>
              </div>
              <div v-if="discountAmount > 0 && appliedPromo" class="flex items-center justify-between text-[#1E5E22]">
                <span>تخفیف (<bdi dir="ltr">{{ appliedPromo.code }}</bdi>)</span>
                <span class="font-bold">- {{ formatToman(discountAmount) }}</span>
              </div>
            </div>

            <div class="border-t border-[var(--color-border-subtle)] pt-3 flex items-center justify-between">
              <span class="text-sm font-bold text-[var(--color-text-primary)]">
                مبلغ قابل پرداخت
              </span>
              <span class="text-lg font-extrabold text-[var(--color-brand-forest)]">
                {{ formatToman(grandTotal) }}
              </span>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </main>
</template>
