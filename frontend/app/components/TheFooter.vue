<script setup lang="ts">
import { computed } from 'vue'
import { MapPin, Phone, Clock, ShieldCheck } from 'lucide-vue-next'
import { useCmsStore } from '~/stores/cms'
import { usePersian } from '~/composables/usePersian'

const cmsStore = useCmsStore()
const { formatTime, formatToman } = usePersian()

const brandName = computed(() => cmsStore.headerSection?.restaurant_name || 'فست‌فودی')
const tagline = computed(() => cmsStore.headerSection?.tagline || 'دست‌پخت اصیل و مواد اولیه تازه')
const address = computed(
  () => cmsStore.footerSection?.address || 'تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴'
)
const phone = computed(() => cmsStore.footerSection?.phone || '۰۲۱-۲۲۰۰۵۵۸۸')
const workingHoursText = computed(() => cmsStore.footerSection?.working_hours_text || '')
const copyrightText = computed(
  () => cmsStore.footerSection?.copyright_text || 'تمامی حقوق برای آشپزخانه فست‌فودی محفوظ است.'
)
const socialLinks = computed(() => cmsStore.footerSection?.social_links || [])
</script>

<template>
  <footer
    class="no-print bg-[var(--color-brand-forest-deep)] text-white/85 pt-14 pb-10"
    role="contentinfo"
  >
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-12 pb-10 border-b border-white/10">
        <div class="space-y-4 lg:col-span-5">
          <div class="flex items-center gap-3">
            <div class="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--color-brand-forest)] text-white shadow-xs">
              <img
                src="/svg/chef.svg"
                :alt="brandName"
                width="24"
                height="24"
                class="h-6 w-6 filter invert brightness-0"
              />
            </div>
            <div>
              <span class="text-xl font-bold tracking-tight text-white">
                {{ brandName }}
              </span>
              <p class="text-[11px] text-[var(--color-accent-gold)]">
                {{ tagline }}
              </p>
            </div>
          </div>

          <div class="space-y-2.5 pt-2 text-xs">
            <div class="flex items-start gap-2.5">
              <MapPin :size="16" aria-hidden="true" class="mt-0.5 text-[var(--color-accent-gold)] shrink-0" />
              <span>{{ address }}</span>
            </div>
            <div class="flex items-center gap-2.5">
              <Phone :size="16" aria-hidden="true" class="text-[var(--color-accent-gold)] shrink-0" />
              <bdi class="text-white font-semibold">{{ phone }}</bdi>
            </div>
          </div>

          <div v-if="socialLinks.length > 0" class="flex flex-wrap gap-2 pt-2">
            <a
              v-for="link in socialLinks"
              :key="link.label"
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer"
              class="rounded-full border border-white/15 bg-white/5 px-3.5 py-1.5 text-xs font-medium text-white hover:bg-white/15"
            >
              {{ link.label }}
            </a>
          </div>
        </div>

        <div class="space-y-3 lg:col-span-3">
          <h2 class="text-sm font-bold text-white">دسترسی سریع</h2>
          <ul class="space-y-2 text-xs">
            <li>
              <NuxtLink to="/" class="hover:text-white transition-colors">صفحه نخست</NuxtLink>
            </li>
            <li>
              <NuxtLink to="/menu" class="hover:text-white transition-colors">منوی کامل و جستجو</NuxtLink>
            </li>
            <li>
              <NuxtLink to="/lucky-wheel" class="hover:text-white transition-colors">گردونه شانس غذا</NuxtLink>
            </li>
            <li>
              <NuxtLink to="/orders" class="hover:text-white transition-colors">پیگیری سفارش‌ها</NuxtLink>
            </li>
            <li>
              <NuxtLink to="/account" class="hover:text-white transition-colors">حساب کاربری و آدرس‌ها</NuxtLink>
            </li>
            <li>
              <NuxtLink to="/about" class="hover:text-white transition-colors">درباره ما</NuxtLink>
            </li>
          </ul>
        </div>

        <div class="space-y-3 lg:col-span-4">
          <h2 class="text-sm font-bold text-white">ساعات کاری و تعرفه ارسال</h2>
          <div class="space-y-2.5 text-xs text-white/80">
            <div class="rounded-xl bg-white/5 p-3.5 border border-white/10 space-y-1.5">
              <div class="flex items-center justify-between text-white font-semibold">
                <span class="inline-flex items-center gap-1.5">
                  <Clock :size="14" aria-hidden="true" class="text-[var(--color-accent-gold)]" />
                  <span>ساعت کاری روزانه:</span>
                </span>
                <bdi v-if="cmsStore.restaurantStatus">
                  {{ formatTime(cmsStore.restaurantStatus.open_time) }} تا {{ formatTime(cmsStore.restaurantStatus.close_time) }}
                </bdi>
              </div>
              <p v-if="workingHoursText" class="text-[11px] text-white/65">
                {{ workingHoursText }}
              </p>
            </div>

            <div v-if="cmsStore.restaurantStatus" class="rounded-xl bg-white/5 p-3.5 border border-white/10 space-y-1">
              <div class="flex items-center justify-between">
                <span>ارسال درون‌محدوده:</span>
                <strong class="text-white">{{ formatToman(cmsStore.restaurantStatus.in_zone_delivery_fee) }}</strong>
              </div>
              <div class="flex items-center justify-between">
                <span>ارسال برون‌محدوده:</span>
                <strong class="text-white">{{ formatToman(cmsStore.restaurantStatus.out_zone_delivery_fee) }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="pt-7 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-white/60">
        <p>{{ copyrightText }}</p>
        <NuxtLink
          to="/backoffice"
          class="inline-flex items-center gap-1.5 text-white/70 hover:text-white transition-colors"
        >
          <ShieldCheck :size="14" aria-hidden="true" />
          <span>ورود کارکنان و پنل مدیریت</span>
        </NuxtLink>
      </div>
    </div>
  </footer>
</template>
