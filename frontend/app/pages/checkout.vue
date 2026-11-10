<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  User,
  Phone,
  MapPin,
  Clock,
  CreditCard,
  Banknote,
  ShieldCheck,
  ArrowRight,
  CheckCircle2,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { useCartStore } from '~/stores/cart'
import { usePersian } from '~/composables/usePersian'
import GooeyButton from '~/components/ui/GooeyButton.vue'

const cartStore = useCartStore()
const { toPersianDigits, formatToman } = usePersian()

useHead({
  title: 'تکمیل و پرداخت سفارش | فست‌فودی',
})

const form = ref({
  fullName: '',
  phone: '',
  address: '',
  unit: '',
  deliveryNotes: '',
  deliveryTime: 'asap', // 'asap' | 'scheduled'
  scheduledTime: '19:30 - 20:30',
  paymentMethod: 'online', // 'online' | 'cash'
})

const isSubmitting = ref(false)
const orderCompleted = ref(false)
const orderTrackingId = ref('')

const handlePlaceOrder = async () => {
  if (cartStore.isEmpty) {
    toast.error('سبد خرید شما خالی است')
    return
  }

  if (!form.value.fullName || !form.value.phone || !form.value.address) {
    toast.error('لطفاً تمامی فیلدهای الزامی (نام، شماره تماس و آدرس) را تکمیل کنید')
    return
  }

  isSubmitting.value = true
  await new Promise(resolve => setTimeout(resolve, 1000))

  orderTrackingId.value = Math.floor(100000 + Math.random() * 900000).toString()
  isSubmitting.value = false
  orderCompleted.value = true

  cartStore.clearCart()
  toast.success('سفارش شما با موفقیت ثبت شد و به آشپزخانه ارسال گردید')
}
</script>

<template>
  <main class="min-h-screen bg-[var(--color-surface-cream)]/50 py-8 sm:py-14">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <!-- Breadcrumb / Back Link -->
      <div class="mb-6">
        <NuxtLink
          to="/"
          class="inline-flex items-center gap-2 text-xs font-bold text-[var(--color-text-secondary)] hover:text-[var(--color-brand-forest)]"
        >
          <ArrowRight :size="15" class="icon-directional" />
          <span>بازگشت به منوی اصلی</span>
        </NuxtLink>
      </div>

      <!-- Order Completed View -->
      <div
        v-if="orderCompleted"
        class="mx-auto max-w-xl rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 sm:p-12 text-center shadow-[var(--shadow-md)] space-y-5"
      >
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-success-bg)] text-[var(--color-brand-success)]">
          <CheckCircle2 :size="44" />
        </div>
        <h1 class="text-2xl font-extrabold text-[var(--color-brand-forest)]">
          سفارش شما با موفقیت ثبت گردید
        </h1>
        <p class="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
          سفارش شما با شماره پیگیری <strong class="text-[var(--color-text-primary)] font-bold text-base"><bdi>{{ toPersianDigits(orderTrackingId) }}</bdi></strong> در حال آماده‌سازی در آشپزخانه است و تا کمتر از ۳۰ دقیقه دیگر تحویل پیک خواهد شد.
        </p>

        <div class="rounded-2xl bg-[var(--color-surface-cream)] p-4 text-xs text-[var(--color-text-secondary)] space-y-1.5 text-start">
          <p><strong>تحویل‌گیرنده:</strong> {{ form.fullName }}</p>
          <p><strong>شماره تماس:</strong> <bdi>{{ form.phone }}</bdi></p>
          <p><strong>آدرس ارسال:</strong> {{ form.address }}</p>
          <p><strong>روش پرداخت:</strong> {{ form.paymentMethod === 'online' ? 'پرداخت اینترنتی موفق' : 'پرداخت در محل هنگام تحویل' }}</p>
        </div>

        <div class="pt-4">
          <NuxtLink
            to="/"
            class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-8 py-3 text-sm font-bold text-white shadow-sm hover:bg-[var(--color-brand-forest-light)]"
          >
            بازگشت به صفحه اصلی
          </NuxtLink>
        </div>
      </div>

      <!-- Empty Cart View -->
      <div
        v-else-if="cartStore.isEmpty"
        class="mx-auto max-w-md rounded-3xl border border-[var(--color-border-subtle)] bg-white p-8 text-center shadow-[var(--shadow-sm)] space-y-4"
      >
        <div class="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-[var(--color-surface-cream)] p-4 border border-[var(--color-border-subtle)]">
          <img src="/svg/cart.svg" alt="سبد خرید خالی" class="h-12 w-12 object-contain" />
        </div>
        <h2 class="text-lg font-bold text-[var(--color-text-primary)]">
          سبد خرید شما خالی است
        </h2>
        <p class="text-xs text-[var(--color-text-secondary)]">
          برای تکمیل فرآیند خرید، لطفاً ابتدا غذاهای مورد علاقه خود را به سبد خرید اضافه فرمایید.
        </p>
        <NuxtLink
          to="/"
          class="touch-target inline-flex items-center justify-center rounded-full bg-[var(--color-brand-forest)] px-6 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-[var(--color-brand-forest-light)]"
        >
          مشاهده منوی غذاها
        </NuxtLink>
      </div>

      <!-- Main Checkout Layout (2-Column Desktop: 2/3 Form, 1/3 Summary) -->
      <div v-else class="grid grid-cols-1 gap-8 lg:grid-cols-12 items-start">
        <!-- Form Details (8 cols) -->
        <div class="lg:col-span-8 space-y-6">
          <form @submit.prevent="handlePlaceOrder" class="space-y-6">
            <!-- Section 1: Customer Information -->
            <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
              <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                  {{ toPersianDigits('۱') }}
                </div>
                <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                  اطلاعات تحویل‌گیرنده
                </h2>
              </div>

              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div class="space-y-1.5">
                  <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                    نام و نام خانوادگی *
                  </label>
                  <div class="relative">
                    <User :size="16" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
                    <input
                      v-model="form.fullName"
                      type="text"
                      required
                      placeholder="مثال: علی حسینی"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white ps-10 pe-3.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>

                <div class="space-y-1.5">
                  <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                    شماره تلفن همراه (جهت هماهنگی پیک) *
                  </label>
                  <div class="relative">
                    <Phone :size="16" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
                    <input
                      v-model="form.phone"
                      type="tel"
                      required
                      placeholder="۰۹۱۲۳۴۵۶۷۸۹"
                      dir="ltr"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white ps-10 pe-3.5 text-xs text-[var(--color-text-primary)] text-end focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Section 2: Delivery Address -->
            <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
              <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                  {{ toPersianDigits('۲') }}
                </div>
                <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                  نشانی محل تحویل سفارش
                </h2>
              </div>

              <div class="space-y-4">
                <div class="space-y-1.5">
                  <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                    آدرس کامل پستی *
                  </label>
                  <div class="relative">
                    <MapPin :size="16" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
                    <textarea
                      v-model="form.address"
                      rows="2"
                      required
                      placeholder="تهران، خیابان..."
                      class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-white p-3 ps-10 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div class="space-y-1.5">
                    <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                      پلاک، زنگ یا واحد (اختیاری)
                    </label>
                    <input
                      v-model="form.unit"
                      type="text"
                      placeholder="پلاک ۱۲، واحد ۴، زنگ غربی"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>

                  <div class="space-y-1.5">
                    <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                      یادداشت برای پیک (کد آسانسور، تماس قبل از ورود...)
                    </label>
                    <input
                      v-model="form.deliveryNotes"
                      type="text"
                      placeholder="مثال: لطفاً زنگ طبقه دوم فشرده شود"
                      class="h-12 w-full rounded-xl border border-[var(--color-border-subtle)] bg-white px-3.5 text-xs text-[var(--color-text-primary)] focus:border-[var(--color-brand-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Section 3: Delivery Timing -->
            <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
              <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                  {{ toPersianDigits('۳') }}
                </div>
                <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                  زمان تحویل
                </h2>
              </div>

              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  @click="form.deliveryTime = 'asap'"
                  class="flex items-start gap-3 rounded-2xl border p-4 text-start transition-all"
                  :class="
                    form.deliveryTime === 'asap'
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                      : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                  "
                >
                  <Clock :size="18" class="mt-0.5 shrink-0" />
                  <div>
                    <h3 class="text-xs font-bold">سریع‌ترین زمان ممکن (پیشنهادی)</h3>
                    <p class="text-[11px] text-[var(--color-text-secondary)] mt-0.5 font-normal">
                      آماده‌سازی فوری و ارسال گرم (حدود ۲۵ الی ۳۵ دقیقه)
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  @click="form.deliveryTime = 'scheduled'"
                  class="flex items-start gap-3 rounded-2xl border p-4 text-start transition-all"
                  :class="
                    form.deliveryTime === 'scheduled'
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                      : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                  "
                >
                  <Clock :size="18" class="mt-0.5 shrink-0" />
                  <div>
                    <h3 class="text-xs font-bold">زمان‌بندی برای ساعت مشخص</h3>
                    <p class="text-[11px] text-[var(--color-text-secondary)] mt-0.5 font-normal">
                      انتخاب بازه تحویل در ساعات بعد
                    </p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Section 4: Payment Method -->
            <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
              <div class="flex items-center gap-2.5 border-b border-[var(--color-border-subtle)] pb-3">
                <div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] text-xs font-bold">
                  {{ toPersianDigits('۴') }}
                </div>
                <h2 class="text-base font-bold text-[var(--color-text-primary)]">
                  شیوه پرداخت
                </h2>
              </div>

              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  @click="form.paymentMethod = 'online'"
                  class="flex items-start gap-3 rounded-2xl border p-4 text-start transition-all"
                  :class="
                    form.paymentMethod === 'online'
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                      : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                  "
                >
                  <CreditCard :size="18" class="mt-0.5 shrink-0" />
                  <div>
                    <h3 class="text-xs font-bold">پرداخت آنلاین با درگاه بانکی</h3>
                    <p class="text-[11px] text-[var(--color-text-secondary)] mt-0.5 font-normal">
                      کلیه کارت‌های عضو شتاب (سامان، ملت، زرین‌پال)
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  @click="form.paymentMethod = 'cash'"
                  class="flex items-start gap-3 rounded-2xl border p-4 text-start transition-all"
                  :class="
                    form.paymentMethod === 'cash'
                      ? 'border-[var(--color-brand-forest)] bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)] ring-2 ring-[var(--color-brand-forest)]/20 font-bold'
                      : 'border-[var(--color-border-subtle)] bg-white text-[var(--color-text-primary)]'
                  "
                >
                  <Banknote :size="18" class="mt-0.5 shrink-0" />
                  <div>
                    <h3 class="text-xs font-bold">پرداخت در محل (کارتخوان سیار)</h3>
                    <p class="text-[11px] text-[var(--color-text-secondary)] mt-0.5 font-normal">
                      تسویه توسط دستگاه کارتخوان سیار پیک هنگام تحویل
                    </p>
                  </div>
                </button>
              </div>
            </div>

            <!-- Submit Button with Gooey Liquid Effect -->
            <GooeyButton
              type="submit"
              variant="primary"
              size="lg"
              :disabled="isSubmitting"
              class="w-full !py-4"
              aria-label="ثبت نهایی و پرداخت سفارش"
            >
              <ShieldCheck :size="18" />
              <span v-if="isSubmitting">در حال ثبت سفارش...</span>
              <span v-else>ثبت نهایی و پرداخت سفارش ({{ formatToman(cartStore.grandTotal) }})</span>
            </GooeyButton>
          </form>
        </div>

        <!-- Sticky Order Summary (4 cols) -->
        <aside class="sticky top-24 lg:col-span-4 space-y-4">
          <div class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 shadow-xs space-y-4">
            <div class="border-b border-[var(--color-border-subtle)] pb-3">
              <h3 class="text-sm font-bold text-[var(--color-text-primary)]">
                خلاصه سفارش ({{ toPersianDigits(cartStore.totalCount) }} مورد)
              </h3>
            </div>

            <!-- Items Mini List -->
            <div class="max-h-[260px] overflow-y-auto space-y-3 pe-1">
              <div
                v-for="item in cartStore.items"
                :key="item.id"
                class="flex items-center justify-between gap-3 text-xs"
              >
                <div class="flex items-center gap-2.5 min-w-0">
                  <img
                    :src="item.product.image"
                    :alt="item.product.title"
                    class="h-10 w-10 rounded-lg object-cover bg-[var(--color-surface-cream)] shrink-0"
                  />
                  <div class="truncate">
                    <p class="font-bold text-[var(--color-text-primary)] truncate">
                      {{ item.product.title }}
                    </p>
                    <p class="text-[10px] text-[var(--color-text-secondary)]">
                      {{ toPersianDigits(item.quantity) }} × {{ formatToman(item.unitPrice) }}
                    </p>
                  </div>
                </div>
                <span class="font-bold text-[var(--color-brand-forest)] shrink-0">
                  {{ formatToman(item.totalPrice) }}
                </span>
              </div>
            </div>

            <!-- Price Breakdown -->
            <div class="border-t border-[var(--color-border-subtle)] pt-4 space-y-2.5 text-xs text-[var(--color-text-secondary)]">
              <div class="flex items-center justify-between">
                <span>مجموع اقلام</span>
                <span class="font-bold text-[var(--color-text-primary)]">
                  {{ formatToman(cartStore.subtotal) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>هزینه بسته‌بندی</span>
                <span class="font-bold text-[var(--color-text-primary)]">
                  {{ formatToman(cartStore.packagingFee) }}
                </span>
              </div>
              <div class="flex items-center justify-between">
                <span>هزینه ارسال پیک اختصاصی</span>
                <span
                  v-if="cartStore.deliveryFee === 0"
                  class="font-bold text-[var(--color-brand-success)]"
                >
                  رایگان
                </span>
                <span v-else class="font-bold text-[var(--color-text-primary)]">
                  {{ formatToman(cartStore.deliveryFee) }}
                </span>
              </div>
            </div>

            <!-- Grand Total -->
            <div class="border-t border-[var(--color-border-subtle)] pt-3 flex items-center justify-between">
              <span class="text-sm font-bold text-[var(--color-text-primary)]">
                مبلغ نهایی
              </span>
              <span class="text-lg font-extrabold text-[var(--color-brand-forest)]">
                {{ formatToman(cartStore.grandTotal) }}
              </span>
            </div>
          </div>

          <!-- Guarantee Badge -->
          <div class="flex items-center gap-3 rounded-2xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] p-4 text-xs text-[var(--color-text-secondary)]">
            <ShieldCheck :size="24" class="text-[var(--color-brand-forest)] shrink-0" />
            <span>ضمانت سلامت، گرمی و بهداشت غذا با بسته‌بندی حرارتی اختصاصی</span>
          </div>
        </aside>
      </div>
    </div>
  </main>
</template>

