<script setup lang="ts">
import { ref } from 'vue'
import {
  Calendar,
  Clock,
  Users,
  Phone,
  Mail,
  User,
  CheckCircle2,
  MapPin,
  Sparkles,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { usePersian } from '~/composables/usePersian'

const { toPersianDigits } = usePersian()

const form = ref({
  fullName: '',
  phone: '',
  guestsCount: 2,
  date: '',
  time: '20:00',
  notes: '',
})

const isSubmitting = ref(false)
const isSubmitted = ref(false)

const guestOptions = [1, 2, 3, 4, 5, 6, 8, 10]
const timeSlots = ['13:00', '14:30', '19:30', '20:30', '21:30', '22:30']

const handleReservation = async () => {
  if (!form.value.fullName || !form.value.phone) {
    toast.error('لطفاً نام و شماره تماس خود را وارد نمایید')
    return
  }

  isSubmitting.value = true
  // Simulate API reservation request
  await new Promise(resolve => setTimeout(resolve, 800))
  isSubmitting.value = false
  isSubmitted.value = true

  toast.success('درخواست رزرو میز با موفقیت ثبت شد', {
    description: `میز ${toPersianDigits(form.value.guestsCount)} نفره برای ${form.value.fullName} ثبت گردید. همکاران ما جهت تایید با شما تماس خواهند گرفت.`,
  })
}
</script>

<template>
  <section
    id="reservation"
    class="relative bg-[var(--color-surface-cream)] py-16 sm:py-24"
    aria-label="رزرو آنلاین میز"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 gap-12 lg:grid-cols-12 lg:items-center">
        <!-- Info Column (5 cols) -->
        <div class="space-y-6 lg:col-span-5">
          <div class="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-bold text-[var(--color-brand-forest)] shadow-2xs">
            <Sparkles :size="14" />
            <span>تجربه حضور در رستوران</span>
          </div>

          <h2 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[var(--color-brand-forest)] leading-tight">
            میز خود را در محیط آرام و صمیمی فست‌فودی رزرو کنید
          </h2>

          <p class="text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
            برای دورهمی‌های خانوادگی، قرارهای کاری یا جشن‌های دوستانه، میز دلخواهتان را از پیش آماده می‌کنیم تا بدون انتظار، از تازه‌ترین دست‌پخت‌های سرآشپز لذت ببرید.
          </p>

          <!-- Contact details cards -->
          <div class="space-y-3 pt-2">
            <div class="flex items-center gap-3.5 rounded-2xl bg-white p-4 border border-[var(--color-border-subtle)] shadow-xs">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]">
                <MapPin :size="20" />
              </div>
              <div class="text-xs">
                <p class="font-bold text-[var(--color-text-primary)]">آدرس رستوران</p>
                <p class="text-[var(--color-text-secondary)] mt-0.5">تهران، خیابان ولیعصر، نرسیده به پارک‌وی، پلاک ۱۲۴</p>
              </div>
            </div>

            <div class="flex items-center gap-3.5 rounded-2xl bg-white p-4 border border-[var(--color-border-subtle)] shadow-xs">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]">
                <Phone :size="20" />
              </div>
              <div class="text-xs">
                <p class="font-bold text-[var(--color-text-primary)]">شماره تماس و پشتیبانی رزرو</p>
                <bdi class="text-[var(--color-text-primary)] font-bold mt-0.5 inline-block">۰۲۱-۲۲۰۰۵۵۸۸</bdi>
              </div>
            </div>

            <div class="flex items-center gap-3.5 rounded-2xl bg-white p-4 border border-[var(--color-border-subtle)] shadow-xs">
              <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--color-surface-cream)] text-[var(--color-brand-forest)]">
                <Clock :size="20" />
              </div>
              <div class="text-xs">
                <p class="font-bold text-[var(--color-text-primary)]">ساعات پذیرایی حضوری</p>
                <p class="text-[var(--color-text-secondary)] mt-0.5">همه‌روزه از ۱۲:۰۰ ظهر الی ۲۴:۰۰ شب (بدون تعطیلی)</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Reservation Form Card (7 cols) -->
        <div class="lg:col-span-7">
          <div
            class="rounded-3xl border border-[var(--color-border-subtle)] bg-white p-6 sm:p-10 shadow-[var(--shadow-lg)]"
          >
            <!-- Success Notification State -->
            <div
              v-if="isSubmitted"
              class="flex flex-col items-center justify-center py-10 text-center space-y-4"
            >
              <div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-success-bg)] text-[var(--color-brand-success)]">
                <CheckCircle2 :size="36" />
              </div>
              <h3 class="text-xl font-bold text-[var(--color-text-primary)]">
                درخواست رزرو شما ثبت گردید
              </h3>
              <p class="max-w-md text-xs sm:text-sm text-[var(--color-text-secondary)] leading-relaxed">
                از انتخاب فست‌فودی سپاسگزاریم. مشخصات رزرو شما بررسی و پیامک تایید نهایی به شماره <strong>{{ form.phone }}</strong> ارسال خواهد شد.
              </p>
              <button
                type="button"
                @click="isSubmitted = false"
                class="touch-target rounded-full border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)] px-6 py-2.5 text-xs font-bold text-[var(--color-text-primary)] hover:bg-[var(--color-surface-ivory)]"
              >
                ثبت رزرو میز جدید
              </button>
            </div>

            <!-- Form Body -->
            <form v-else @submit.prevent="handleReservation" class="space-y-5">
              <div class="border-b border-[var(--color-border-subtle)] pb-4">
                <h3 class="text-lg font-bold text-[var(--color-text-primary)]">
                  فرم درخواست رزرو میز
                </h3>
                <p class="text-xs text-[var(--color-text-secondary)] mt-1">
                  مشخصات خود را تکمیل کنید تا بهترین میز برای شما مهیا شود.
                </p>
              </div>

              <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <!-- Name -->
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
                      placeholder="مثال: سارا محمدی"
                      class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 py-2.5 ps-10 pe-3.5 text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>

                <!-- Phone -->
                <div class="space-y-1.5">
                  <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                    شماره همراه *
                  </label>
                  <div class="relative">
                    <Phone :size="16" class="absolute inset-inline-start-3.5 top-3.5 text-[var(--color-text-muted)]" />
                    <input
                      v-model="form.phone"
                      type="tel"
                      required
                      placeholder="۰۹۱۲۳۴۵۶۷۸۹"
                      dir="ltr"
                      class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 py-2.5 ps-10 pe-3.5 text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] text-end focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                    />
                  </div>
                </div>
              </div>

              <!-- Guests Selection -->
              <div class="space-y-2">
                <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                  تعداد نفرات
                </label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="count in guestOptions"
                    :key="count"
                    type="button"
                    @click="form.guestsCount = count"
                    class="touch-target flex h-10 min-w-10 items-center justify-center rounded-xl border px-3 text-xs font-bold transition-all"
                    :class="
                      form.guestsCount === count
                        ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white shadow-xs'
                        : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)]'
                    "
                  >
                    {{ toPersianDigits(count) }} نفر
                  </button>
                </div>
              </div>

              <!-- Time Slot -->
              <div class="space-y-2">
                <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                  ساعت حضور
                </label>
                <div class="grid grid-cols-3 sm:grid-cols-6 gap-2">
                  <button
                    v-for="slot in timeSlots"
                    :key="slot"
                    type="button"
                    @click="form.time = slot"
                    class="touch-target flex h-9 items-center justify-center rounded-xl border text-xs font-semibold transition-all"
                    :class="
                      form.time === slot
                        ? 'border-[var(--color-brand-forest)] bg-[var(--color-brand-forest)] text-white'
                        : 'border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/60 text-[var(--color-text-primary)] hover:border-[var(--color-brand-forest)]'
                    "
                  >
                    <bdi>{{ slot }}</bdi>
                  </button>
                </div>
              </div>

              <!-- Notes -->
              <div class="space-y-1.5">
                <label class="block text-xs font-bold text-[var(--color-text-primary)]">
                  توضیحات تکمیلی (مناسبت خاص، صندلی کودک و...)
                </label>
                <textarea
                  v-model="form.notes"
                  rows="2"
                  placeholder="در صورت داشتن درخواست خاص یا برگزاری جشن تولد اینجا یادداشت بفرمایید..."
                  class="w-full rounded-xl border border-[var(--color-border-subtle)] bg-[var(--color-surface-cream)]/50 p-3 text-xs text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:border-[var(--color-brand-forest)] focus:bg-white focus:outline-none focus:ring-2 focus:ring-[var(--color-brand-forest)]/10"
                />
              </div>

              <!-- Submit Button -->
              <button
                type="submit"
                :disabled="isSubmitting"
                class="touch-target flex w-full items-center justify-center gap-2 rounded-full bg-[var(--color-brand-forest)] py-3.5 text-sm font-bold text-white shadow-md transition-all hover:bg-[var(--color-brand-forest-light)] active:scale-98 disabled:opacity-50"
              >
                <span v-if="isSubmitting">در حال ارسال درخواست...</span>
                <span v-else>ثبت درخواست رزرو میز</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
