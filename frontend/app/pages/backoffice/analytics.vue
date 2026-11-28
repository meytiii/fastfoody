<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { BarChart3, Clock, RefreshCw, TrendingDown, TrendingUp } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { backofficeApi } from '~/services/api'
import type { AnalyticsPeriod, SalesAnalyticsResponse } from '~/types'

const { formatToman, toPersianDigits } = usePersian()

const todayIso = new Date().toISOString().slice(0, 10)
const weekAgoDate = new Date()
weekAgoDate.setUTCDate(weekAgoDate.getUTCDate() - 6)
const weekAgoIso = weekAgoDate.toISOString().slice(0, 10)

const period = ref<AnalyticsPeriod>('7d')
const dateFrom = ref(weekAgoIso)
const dateTo = ref(todayIso)
const loading = ref(true)
const errorMessage = ref('')
const analytics = ref<SalesAnalyticsResponse | null>(null)

const periodOptions: Array<{ value: AnalyticsPeriod; label: string }> = [
  { value: 'today', label: 'امروز' },
  { value: '7d', label: '۷ روز گذشته' },
  { value: '30d', label: '۳۰ روز گذشته' },
  { value: 'custom', label: 'بازه دلخواه' },
]

const maxPeakOrders = computed(() => {
  if (!analytics.value) return 1
  return Math.max(1, ...analytics.value.peak_hours.map(h => h.order_count))
})

const peakHoursSortedHighlight = computed(() => {
  if (!analytics.value) return []
  return analytics.value.peak_hours.filter(h => h.order_count > 0)
})

async function loadAnalytics() {
  loading.value = true
  errorMessage.value = ''
  try {
    analytics.value = await backofficeApi.analytics.getSales({
      period: period.value,
      ...(period.value === 'custom'
        ? { date_from: dateFrom.value, date_to: dateTo.value }
        : {}),
    })
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'خطا در دریافت گزارش فروش'
    errorMessage.value = msg
    toast.error(msg)
  } finally {
    loading.value = false
  }
}

async function selectPeriod(nextPeriod: AnalyticsPeriod) {
  period.value = nextPeriod
  if (nextPeriod !== 'custom') {
    await loadAnalytics()
  }
}

onMounted(() => {
  void loadAnalytics()
})

useHead({
  title: 'تحلیل و گزارش فروش | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="تحلیل و گزارش فروش"
      subtitle="پایش فروش ناخالص و خالص، پرفروش‌ترین غذاها و ساعات شلوغی"
      @reset="loadAnalytics"
    >
      <template #header-actions>
        <button
          type="button"
          class="touch-target inline-flex items-center gap-2 rounded-full bg-[#183A2D] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#12251D]"
          @click="loadAnalytics"
        >
          <RefreshCw class="h-4 w-4" />
          <span>بروزرسانی گزارش</span>
        </button>
      </template>

      <div class="space-y-6">
        <div class="flex flex-wrap items-end justify-between gap-4 rounded-3xl border border-[#E8E5DC] bg-white p-5 shadow-sm">
          <div class="flex flex-wrap items-center gap-2" role="tablist" aria-label="بازه گزارش">
            <button
              v-for="opt in periodOptions"
              :key="opt.value"
              type="button"
              role="tab"
              :aria-selected="period === opt.value"
              class="touch-target rounded-full px-4 py-2 text-xs font-bold transition-colors"
              :class="
                period === opt.value
                  ? 'bg-[#183A2D] text-white'
                  : 'border border-[#E8E5DC] bg-[#FAF7F2] text-[#292B27] hover:bg-[#F4EFE3]'
              "
              @click="selectPeriod(opt.value)"
            >
              {{ opt.label }}
            </button>
          </div>

          <form
            v-if="period === 'custom'"
            class="flex flex-wrap items-end gap-3"
            @submit.prevent="loadAnalytics"
          >
            <div>
              <label for="an-from" class="mb-1 block text-xs font-semibold text-[#5A5D56]">از تاریخ</label>
              <input
                id="an-from"
                v-model="dateFrom"
                type="date"
                dir="ltr"
                required
                class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label for="an-to" class="mb-1 block text-xs font-semibold text-[#5A5D56]">تا تاریخ</label>
              <input
                id="an-to"
                v-model="dateTo"
                type="date"
                dir="ltr"
                required
                class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-xs"
              />
            </div>
            <button
              type="submit"
              class="touch-target rounded-full bg-[#183A2D] px-5 py-2 text-xs font-bold text-white hover:bg-[#12251D]"
            >
              اعمال بازه
            </button>
          </form>
        </div>

        <div
          v-if="errorMessage"
          role="alert"
          class="rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4 text-sm font-medium text-[#A61B1B]"
        >
          {{ errorMessage }}
        </div>

        <div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div v-for="i in 4" :key="i" class="h-28 animate-pulse rounded-3xl bg-[#E8E5DC]" />
        </div>

        <template v-else-if="analytics">
          <p dir="ltr" class="text-end text-xs font-semibold text-[#5A5D56]">
            {{ analytics.date_from }} - {{ analytics.date_to }}
          </p>

          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div class="rounded-3xl border border-[#E8E5DC] bg-white p-5 shadow-sm">
              <p class="text-xs font-semibold text-[#5A5D56]">فروش ناخالص</p>
              <p class="mt-2 text-xl font-extrabold text-[#292B27]">{{ formatToman(analytics.gross_sales) }}</p>
            </div>

            <div class="rounded-3xl border border-[#183A2D]/25 bg-[#FAF7F2] p-5 shadow-sm">
              <p class="text-xs font-semibold text-[#5A5D56]">فروش خالص</p>
              <p class="mt-2 text-xl font-extrabold text-[#183A2D]">{{ formatToman(analytics.net_sales) }}</p>
            </div>

            <div class="rounded-3xl border border-[#E8E5DC] bg-white p-5 shadow-sm">
              <p class="text-xs font-semibold text-[#5A5D56]">تعداد سفارش پرداخت‌شده</p>
              <p class="mt-2 text-xl font-extrabold text-[#292B27]">{{ toPersianDigits(analytics.paid_orders_count) }} سفارش</p>
            </div>

            <div class="rounded-3xl border border-[#E8E5DC] bg-white p-5 shadow-sm">
              <p class="text-xs font-semibold text-[#5A5D56]">میانگین سبد سفارش</p>
              <p class="mt-2 text-xl font-extrabold text-[#292B27]">{{ formatToman(analytics.average_order_value) }}</p>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
              <p class="text-xs text-[#5A5D56]">مجموع تخفیف‌ها</p>
              <p class="mt-1 text-base font-bold text-[#1E5E22]">{{ formatToman(analytics.total_discounts) }}</p>
            </div>
            <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
              <p class="text-xs text-[#5A5D56]">مجموع هزینه ارسال</p>
              <p class="mt-1 text-base font-bold text-[#292B27]">{{ formatToman(analytics.total_delivery_fees) }}</p>
            </div>
            <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
              <p class="text-xs text-[#5A5D56]">مجموع بسته‌بندی</p>
              <p class="mt-1 text-base font-bold text-[#292B27]">{{ formatToman(analytics.total_packaging_fees) }}</p>
            </div>
            <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
              <p class="text-xs text-[#5A5D56]">سفارش‌های مرجوع‌شده ({{ toPersianDigits(analytics.refunded_count) }})</p>
              <p class="mt-1 text-base font-bold text-[#A61B1B]">{{ formatToman(analytics.refunded_amount) }}</p>
            </div>
          </div>

          <div class="grid gap-6 lg:grid-cols-2">
            <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm space-y-4">
              <h2 class="flex items-center gap-2 text-base font-extrabold text-[#292B27]">
                <TrendingUp class="h-4 w-4 text-[#1E5E22]" />
                <span>۱۰ محصول پرفروش</span>
              </h2>
              <p v-if="analytics.top_products.length === 0" class="text-xs text-[#5A5D56]">
                در این بازه داده‌ای ثبت نشده است.
              </p>
              <ul v-else class="divide-y divide-[#E8E5DC] text-sm">
                <li
                  v-for="(item, idx) in analytics.top_products"
                  :key="`${item.product_name}-${idx}`"
                  class="flex items-center justify-between gap-3 py-2.5"
                >
                  <div class="min-w-0">
                    <p class="truncate font-bold text-[#292B27]">
                      {{ toPersianDigits(idx + 1) }}. {{ item.product_name }}
                    </p>
                    <p class="text-xs text-[#5A5D56]">{{ toPersianDigits(item.quantity) }} عدد</p>
                  </div>
                  <span class="shrink-0 text-xs font-extrabold text-[#183A2D]">
                    {{ formatToman(item.revenue) }}
                  </span>
                </li>
              </ul>
            </section>

            <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm space-y-4">
              <h2 class="flex items-center gap-2 text-base font-extrabold text-[#292B27]">
                <TrendingDown class="h-4 w-4 text-[#9A4300]" />
                <span>۵ محصول کم‌فروش (موجود)</span>
              </h2>
              <p v-if="analytics.least_selling_products.length === 0" class="text-xs text-[#5A5D56]">
                محصولی یافت نشد.
              </p>
              <ul v-else class="divide-y divide-[#E8E5DC] text-sm">
                <li
                  v-for="item in analytics.least_selling_products"
                  :key="item.id"
                  class="flex items-center justify-between gap-3 py-2.5"
                >
                  <span class="font-bold text-[#292B27]">{{ item.name }}</span>
                  <span class="rounded-full bg-[#F4EFE3] px-3 py-1 text-xs font-bold text-[#5A5D56]">
                    {{ toPersianDigits(item.quantity_sold) }} فروش
                  </span>
                </li>
              </ul>
            </section>
          </div>

          <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm space-y-4">
            <h2 class="flex items-center gap-2 text-base font-extrabold text-[#292B27]">
              <Clock class="h-4 w-4 text-[#183A2D]" />
              <span>ساعات اوج سفارش (۲۴ ساعته)</span>
            </h2>
            <p v-if="peakHoursSortedHighlight.length === 0" class="text-xs text-[#5A5D56]">
              سفارشی در این بازه ثبت نشده است.
            </p>
            <div v-else class="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              <div
                v-for="row in analytics.peak_hours"
                :key="row.hour"
                class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-xs"
              >
                <div class="flex items-center justify-between font-bold text-[#292B27]">
                  <span>ساعت {{ toPersianDigits(String(row.hour).padStart(2, '0')) }}:۰۰</span>
                  <span>{{ toPersianDigits(row.order_count) }} سفارش</span>
                </div>
                <div class="mt-1.5 h-2 overflow-hidden rounded-full bg-[#E8E5DC]">
                  <div
                    class="h-full rounded-full bg-[#183A2D]"
                    :style="{ width: `${Math.round((row.order_count / maxPeakOrders) * 100)}%` }"
                  />
                </div>
                <p class="mt-1 text-[11px] text-[#5A5D56]">{{ formatToman(row.revenue) }}</p>
              </div>
            </div>
          </section>

          <section class="rounded-3xl border border-[#E8E5DC] bg-white p-6 shadow-sm space-y-4">
            <h2 class="flex items-center gap-2 text-base font-extrabold text-[#292B27]">
              <BarChart3 class="h-4 w-4 text-[#183A2D]" />
              <span>روند روزانه فروش</span>
            </h2>
            <div class="overflow-x-auto">
              <table class="w-full border-collapse text-sm">
                <thead>
                  <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                    <th scope="col" class="px-3 py-2.5 text-start">تاریخ</th>
                    <th scope="col" class="px-3 py-2.5 text-start">تعداد سفارش</th>
                    <th scope="col" class="px-3 py-2.5 text-start">درآمد</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E8E5DC]">
                  <tr v-for="day in analytics.daily_trend" :key="day.date" class="hover:bg-[#FAF7F2]">
                    <td dir="ltr" class="px-3 py-2.5 text-end font-mono text-xs">{{ day.date }}</td>
                    <td class="px-3 py-2.5 text-xs font-bold">{{ toPersianDigits(day.order_count) }}</td>
                    <td class="px-3 py-2.5 text-xs font-bold text-[#183A2D]">{{ formatToman(day.revenue) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </template>
      </div>
    </BackofficeShell>
  </div>
</template>
