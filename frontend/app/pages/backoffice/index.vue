<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import {
  Bell,
  BellOff,
  CheckCircle2,
  Clock,
  MapPin,
  Printer,
  RefreshCw,
  Timer,
  XCircle,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import { backofficeApi } from '~/services/api'
import type { LiveOrderBackoffice } from '~/types'

const { formatDateTime, formatTime, formatToman, toPersianDigits } = usePersian()

const liveOrders = ref<LiveOrderBackoffice[]>([])
const loading = ref(true)
const errorMessage = ref('')
const autoRefresh = ref(true)
const soundEnabled = ref(false)
const lastUpdatedAt = ref<string | null>(null)
const prepInputs = reactive<Record<number, number>>({})
const busyOrderIds = reactive<Record<number, boolean>>({})

const receiptToPrint = ref<LiveOrderBackoffice | null>(null)
const cancelDialogRef = ref<HTMLDialogElement | null>(null)
const orderToCancel = ref<LiveOrderBackoffice | null>(null)
const cancelReason = ref('')
const canceling = ref(false)

useDialogLightDismiss(cancelDialogRef, () => {
  closeCancelDialog()
})

let pollTimer: number | null = null
let audioCtx: AudioContext | null = null

const unprintedCount = computed(() => liveOrders.value.filter(o => !o.is_printed).length)
const processingCount = computed(() => liveOrders.value.filter(o => o.status === 'PROCESSING').length)
const readyCount = computed(() => liveOrders.value.filter(o => o.status === 'READY').length)

function isOverdue(order: LiveOrderBackoffice): boolean {
  if (order.status !== 'PROCESSING' || !order.expected_ready_at) return false
  return new Date(order.expected_ready_at).getTime() < Date.now()
}

function playNotificationChime() {
  if (!soundEnabled.value || !import.meta.client) return
  try {
    if (!audioCtx) {
      audioCtx = new AudioContext()
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume()
    }
    const now = audioCtx.currentTime
    const frequencies = [587.33, 880]
    frequencies.forEach((freq, idx) => {
      if (!audioCtx) return
      const osc = audioCtx.createOscillator()
      const gain = audioCtx.createGain()
      osc.type = 'sine'
      osc.frequency.setValueAtTime(freq, now + idx * 0.16)
      gain.gain.setValueAtTime(0.08, now + idx * 0.16)
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.16 + 0.25)
      osc.connect(gain)
      gain.connect(audioCtx.destination)
      osc.start(now + idx * 0.16)
      osc.stop(now + idx * 0.16 + 0.26)
    })
  } catch {
  }
}

function toggleSound() {
  soundEnabled.value = !soundEnabled.value
  if (soundEnabled.value) {
    try {
      if (!audioCtx) audioCtx = new AudioContext()
      if (audioCtx.state === 'suspended') audioCtx.resume()
      playNotificationChime()
    } catch {
    }
  }
}

async function fetchLiveOrders(silent = false) {
  if (!silent) loading.value = true
  errorMessage.value = ''
  try {
    const data = await backofficeApi.orders.getLiveOrders()
    liveOrders.value = data
    for (const order of data) {
      if (prepInputs[order.id] === undefined) {
        prepInputs[order.id] = order.prep_time_minutes
      }
    }
    lastUpdatedAt.value = new Date().toISOString()
    if (data.some(o => !o.is_printed)) {
      playNotificationChime()
    }
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'خطا در دریافت سفارش‌های زنده'
  } finally {
    loading.value = false
  }
}

async function handlePrint(order: LiveOrderBackoffice) {
  busyOrderIds[order.id] = true
  try {
    if (!order.is_printed) {
      await backofficeApi.orders.markPrinted(order.id)
    }
    receiptToPrint.value = order
    await nextTick()
    window.print()
    await fetchLiveOrders(true)
    toast.success(`فیش سفارش #${toPersianDigits(order.daily_number ?? order.id)} چاپ شد`)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در ثبت چاپ فیش')
  } finally {
    busyOrderIds[order.id] = false
  }
}

async function handleUpdatePrepTime(order: LiveOrderBackoffice) {
  const nextMinutes = Number(prepInputs[order.id])
  if (!Number.isFinite(nextMinutes) || nextMinutes < 1) {
    toast.error('زمان آماده‌سازی باید حداقل ۱ دقیقه باشد')
    return
  }
  busyOrderIds[order.id] = true
  try {
    await backofficeApi.orders.updatePrepTime(order.id, Math.round(nextMinutes))
    await fetchLiveOrders(true)
    toast.success('زمان آماده‌سازی به‌روزرسانی شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در تغییر زمان آماده‌سازی')
  } finally {
    busyOrderIds[order.id] = false
  }
}

async function handleMarkReady(order: LiveOrderBackoffice) {
  busyOrderIds[order.id] = true
  try {
    await backofficeApi.orders.markReady(order.id)
    await fetchLiveOrders(true)
    toast.success(`سفارش #${toPersianDigits(order.daily_number ?? order.id)} آماده تحویل شد`)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در تغییر وضعیت')
  } finally {
    busyOrderIds[order.id] = false
  }
}

async function handleMarkCompleted(order: LiveOrderBackoffice) {
  busyOrderIds[order.id] = true
  try {
    await backofficeApi.orders.markCompleted(order.id)
    await fetchLiveOrders(true)
    toast.success(`سفارش #${toPersianDigits(order.daily_number ?? order.id)} تکمیل شد`)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در تکمیل سفارش')
  } finally {
    busyOrderIds[order.id] = false
  }
}

function openCancelDialog(order: LiveOrderBackoffice) {
  orderToCancel.value = order
  cancelReason.value = ''
  cancelDialogRef.value?.showModal()
}

async function closeCancelDialog() {
  await closeDialogSmoothly(cancelDialogRef.value)
  orderToCancel.value = null
  cancelReason.value = ''
}

async function confirmCancelOrder() {
  if (!orderToCancel.value) return
  canceling.value = true
  try {
    await backofficeApi.orders.cancelOrder(orderToCancel.value.id, cancelReason.value.trim())
    await closeCancelDialog()
    await fetchLiveOrders(true)
    toast.success('سفارش لغو و برای عودت ثبت شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در لغو سفارش')
  } finally {
    canceling.value = false
  }
}

onMounted(() => {
  fetchLiveOrders()
  pollTimer = window.setInterval(() => {
    if (autoRefresh.value) {
      fetchLiveOrders(true)
    }
  }, 10000)
})

onUnmounted(() => {
  if (pollTimer !== null) {
    window.clearInterval(pollTimer)
  }
})

useHead({
  title: 'POS زنده آشپزخانه | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="POS زنده آشپزخانه"
      subtitle="پایش لحظه‌ای سفارش‌های پرداخت‌شده به ترتیب زمان تحویل"
      @reset="fetchLiveOrders"
    >
      <template #header-actions>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="touch-target inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-bold transition-colors"
            :class="
              soundEnabled
                ? 'border-[#183A2D] bg-[#183A2D] text-white'
                : 'border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            :aria-pressed="soundEnabled"
            @click="toggleSound"
          >
            <Bell v-if="soundEnabled" class="h-4 w-4" />
            <BellOff v-else class="h-4 w-4" />
            <span>{{ soundEnabled ? 'آژیر فعال است' : 'فعال‌سازی صدای هشدار' }}</span>
          </button>

          <button
            type="button"
            class="touch-target inline-flex items-center gap-2 rounded-full border border-[#E8E5DC] bg-white px-4 py-2 text-xs font-semibold text-[#292B27] hover:bg-[#F4EFE3]"
            :aria-pressed="autoRefresh"
            @click="autoRefresh = !autoRefresh"
          >
            <span>{{ autoRefresh ? 'به‌روزرسانی خودکار: روشن' : 'به‌روزرسانی خودکار: مکث' }}</span>
          </button>

          <button
            type="button"
            class="touch-target inline-flex items-center gap-2 rounded-full bg-[#183A2D] px-4 py-2 text-xs font-bold text-white hover:bg-[#12251D]"
            @click="fetchLiveOrders()"
          >
            <RefreshCw class="h-4 w-4" />
            <span>به‌روزرسانی</span>
          </button>
        </div>
      </template>

      <div class="no-print space-y-6">
        <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
            <p class="text-xs font-semibold text-[#5A5D56]">کل سفارش‌های فعال</p>
            <p class="mt-1 text-2xl font-extrabold text-[#292B27]">{{ toPersianDigits(liveOrders.length) }}</p>
          </div>
          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
            <p class="text-xs font-semibold text-[#5A5D56]">فیش چاپ‌نشده</p>
            <p class="mt-1 text-2xl font-extrabold" :class="unprintedCount > 0 ? 'text-[#A61B1B]' : 'text-[#1E5E22]'">
              {{ toPersianDigits(unprintedCount) }}
            </p>
          </div>
          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
            <p class="text-xs font-semibold text-[#5A5D56]">در حال آماده‌سازی</p>
            <p class="mt-1 text-2xl font-extrabold text-[#9A4300]">{{ toPersianDigits(processingCount) }}</p>
          </div>
          <div class="rounded-2xl border border-[#E8E5DC] bg-white p-4">
            <p class="text-xs font-semibold text-[#5A5D56]">آماده تحویل</p>
            <p class="mt-1 text-2xl font-extrabold text-[#1E5E22]">{{ toPersianDigits(readyCount) }}</p>
          </div>
        </div>

        <p v-if="lastUpdatedAt" class="text-xs text-[#72756E]">
          آخرین همگام‌سازی: {{ formatTime(lastUpdatedAt) }}
        </p>

        <div
          v-if="errorMessage"
          role="alert"
          class="rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4 text-sm font-medium text-[#A61B1B]"
        >
          {{ errorMessage }}
        </div>

        <div v-if="loading" class="grid gap-5 md:grid-cols-2">
          <div v-for="i in 2" :key="i" class="h-72 animate-pulse rounded-3xl bg-[#E8E5DC]" />
        </div>

        <div
          v-else-if="liveOrders.length === 0"
          class="rounded-3xl border border-[#E8E5DC] bg-white p-12 text-center shadow-sm"
        >
          <CheckCircle2 class="mx-auto mb-3 h-10 w-10 text-[#1E5E22]" />
          <h2 class="text-lg font-bold text-[#292B27]">سفارش فعالی در آشپزخانه نیست</h2>
          <p class="mt-1 text-sm text-[#5A5D56]">به‌محض ثبت و پرداخت سفارش جدید، فیش آن اینجا نمایش داده می‌شود.</p>
        </div>

        <div v-else class="grid gap-5 lg:grid-cols-2">
          <article
            v-for="order in liveOrders"
            :key="order.id"
            class="flex flex-col justify-between rounded-3xl border bg-white p-5 shadow-sm sm:p-6"
            :class="
              !order.is_printed
                ? 'border-[#D6A84B] ring-2 ring-[#D6A84B]/30'
                : isOverdue(order)
                  ? 'border-[#A61B1B]/40'
                  : 'border-[#E8E5DC]'
            "
          >
            <div class="space-y-4">
              <div class="flex flex-wrap items-start justify-between gap-3 border-b border-[#E8E5DC] pb-4">
                <div class="flex items-center gap-3">
                  <span class="flex h-12 min-w-12 items-center justify-center rounded-2xl bg-[#183A2D] px-3 text-lg font-extrabold text-white">
                    #{{ toPersianDigits(order.daily_number ?? order.id) }}
                  </span>
                  <div>
                    <p class="text-sm font-bold text-[#292B27]">
                      {{ order.delivery_type === 'DELIVERY' ? 'ارسال با پیک' : 'تحویل حضوری' }}
                    </p>
                    <p dir="ltr" class="text-xs font-semibold text-[#5A5D56]">
                      {{ toPersianDigits(order.customer_phone) }}
                    </p>
                  </div>
                </div>

                <div class="flex flex-wrap items-center gap-1.5">
                  <span
                    class="rounded-full px-3 py-1 text-xs font-bold"
                    :class="
                      order.status === 'READY'
                        ? 'bg-[#EDF7ED] text-[#1E5E22]'
                        : 'bg-[#FFF4E5] text-[#9A4300]'
                    "
                  >
                    {{ order.status === 'READY' ? 'آماده تحویل' : 'در حال پخت' }}
                  </span>
                  <span
                    v-if="!order.is_printed"
                    class="rounded-full bg-[#FDE8E8] px-3 py-1 text-xs font-bold text-[#A61B1B]"
                  >
                    چاپ‌نشده
                  </span>
                  <span
                    v-if="isOverdue(order)"
                    class="rounded-full bg-[#FDE8E8] px-3 py-1 text-xs font-bold text-[#A61B1B]"
                  >
                    تأخیر زمانی
                  </span>
                </div>
              </div>

              <div class="flex flex-wrap items-center gap-4 text-xs text-[#5A5D56]">
                <span class="inline-flex items-center gap-1 font-semibold">
                  <Clock class="h-3.5 w-3.5" />
                  موعد تحویل: {{ formatTime(order.expected_ready_at) }}
                </span>
                <span class="inline-flex items-center gap-1">
                  <Timer class="h-3.5 w-3.5" />
                  زمان پخت: {{ toPersianDigits(order.prep_time_minutes) }} دقیقه
                </span>
                <span class="font-bold text-[#292B27]">{{ formatToman(order.total_amount) }}</span>
              </div>

              <p
                v-if="order.delivery_type === 'DELIVERY' && order.delivery_address_snapshot"
                class="flex items-start gap-2 rounded-xl bg-[#FAF7F2] px-3.5 py-2.5 text-xs leading-5 text-[#292B27]"
              >
                <MapPin class="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#183A2D]" />
                <span>{{ order.delivery_address_snapshot }}</span>
              </p>

              <div
                v-if="order.notes_to_kitchen"
                class="rounded-xl border border-[#D6A84B]/40 bg-[#F8F3E8] px-3.5 py-2.5 text-xs font-semibold text-[#8A651C]"
              >
                توضیح مشتری برای آشپزخانه: {{ order.notes_to_kitchen }}
              </div>

              <ul class="space-y-2 rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2] p-3.5">
                <li v-for="item in order.items" :key="item.id" class="text-sm">
                  <div class="flex items-center justify-between gap-2 font-bold text-[#292B27]">
                    <span>{{ toPersianDigits(item.quantity) }}x {{ item.product_name_snapshot }}</span>
                    <span class="text-xs font-semibold text-[#5A5D56]">{{ formatToman(item.line_total) }}</span>
                  </div>
                  <ul v-if="item.addons.length > 0" class="mt-1 space-y-0.5 pe-4 text-xs text-[#5A5D56]">
                    <li v-for="addon in item.addons" :key="addon.addon_id">
                      + {{ toPersianDigits(addon.quantity) }}x {{ addon.addon_name_snapshot }}
                    </li>
                  </ul>
                </li>
              </ul>
            </div>

            <div class="mt-5 space-y-3 border-t border-[#E8E5DC] pt-4">
              <div class="flex flex-wrap items-center gap-2">
                <label :for="`prep-${order.id}`" class="text-xs font-semibold text-[#5A5D56]">
                  تغییر زمان (دقیقه):
                </label>
                <input
                  :id="`prep-${order.id}`"
                  v-model.number="prepInputs[order.id]"
                  type="number"
                  min="1"
                  max="180"
                  dir="ltr"
                  class="w-20 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-1.5 text-center text-sm font-bold"
                />
                <button
                  type="button"
                  :disabled="busyOrderIds[order.id]"
                  class="touch-target rounded-xl border border-[#E8E5DC] bg-white px-3.5 py-1.5 text-xs font-semibold text-[#292B27] hover:bg-[#F4EFE3]"
                  @click="handleUpdatePrepTime(order)"
                >
                  ثبت زمان
                </button>
              </div>

              <div class="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  :disabled="busyOrderIds[order.id]"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2 text-xs font-bold text-[#292B27] hover:bg-[#F4EFE3]"
                  @click="handlePrint(order)"
                >
                  <Printer class="h-3.5 w-3.5" />
                  <span>چاپ فیش</span>
                </button>

                <button
                  v-if="order.status === 'PROCESSING'"
                  type="button"
                  :disabled="busyOrderIds[order.id]"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#183A2D] px-4 py-2 text-xs font-bold text-white hover:bg-[#12251D]"
                  @click="handleMarkReady(order)"
                >
                  <span>آماده تحویل</span>
                </button>

                <button
                  type="button"
                  :disabled="busyOrderIds[order.id]"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#EDF7ED] px-4 py-2 text-xs font-bold text-[#1E5E22] hover:bg-[#1E5E22] hover:text-white"
                  @click="handleMarkCompleted(order)"
                >
                  <CheckCircle2 class="h-3.5 w-3.5" />
                  <span>تکمیل سفارش</span>
                </button>

                <button
                  type="button"
                  :disabled="busyOrderIds[order.id]"
                  class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#FDE8E8] px-4 py-2 text-xs font-bold text-[#A61B1B] hover:bg-[#A61B1B] hover:text-white"
                  @click="openCancelDialog(order)"
                >
                  <XCircle class="h-3.5 w-3.5" />
                  <span>لغو</span>
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>

      <section v-if="receiptToPrint" class="print-only-receipt hidden p-4 text-xs leading-6">
        <div class="border-b border-dashed border-black pb-2 text-center">
          <p class="text-base font-extrabold">فست‌فودی | فیش آشپزخانه</p>
          <p class="text-lg font-extrabold">
            شماره نوبت: #{{ toPersianDigits(receiptToPrint.daily_number ?? receiptToPrint.id) }}
          </p>
          <p>{{ formatDateTime(receiptToPrint.created_at) }}</p>
        </div>
        <div class="space-y-1 border-b border-dashed border-black py-2">
          <p>نوع: {{ receiptToPrint.delivery_type === 'DELIVERY' ? 'ارسال پیک' : 'حضوری' }}</p>
          <p>موبایل مشتری: {{ toPersianDigits(receiptToPrint.customer_phone) }}</p>
          <p v-if="receiptToPrint.delivery_address_snapshot">نشانی: {{ receiptToPrint.delivery_address_snapshot }}</p>
          <p v-if="receiptToPrint.notes_to_kitchen" class="font-bold">
            یادداشت: {{ receiptToPrint.notes_to_kitchen }}
          </p>
        </div>
        <div class="space-y-1 border-b border-dashed border-black py-2">
          <div v-for="item in receiptToPrint.items" :key="item.id">
            <div class="flex justify-between font-bold">
              <span>{{ toPersianDigits(item.quantity) }}x {{ item.product_name_snapshot }}</span>
              <span>{{ formatToman(item.line_total) }}</span>
            </div>
            <div v-for="addon in item.addons" :key="addon.addon_id" class="ps-3">
              + {{ toPersianDigits(addon.quantity) }}x {{ addon.addon_name_snapshot }}
            </div>
          </div>
        </div>
        <div class="pt-2 text-sm font-extrabold">
          مبلغ کل: {{ formatToman(receiptToPrint.total_amount) }}
        </div>
      </section>
    </BackofficeShell>

    <dialog
      ref="cancelDialogRef"
      closedby="any"
      aria-labelledby="cancel-dialog-title"
      class="modal-top-layer m-auto w-full max-w-md rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-xl"
    >
      <div class="p-6 sm:p-7">
        <h2 id="cancel-dialog-title" class="text-lg font-extrabold text-[#292B27]">
          لغو سفارش #{{ toPersianDigits(orderToCancel?.daily_number ?? orderToCancel?.id) }}
        </h2>
        <p class="mt-2 text-xs leading-6 text-[#5A5D56]">
          با لغو سفارش پرداخت‌شده، موجودی کالاها به انبار برمی‌گردد و وضعیت پرداخت به «در انتظار عودت وجه» منتقل می‌شود.
        </p>

        <form class="mt-4 space-y-4" @submit.prevent="confirmCancelOrder">
          <div>
            <label for="pos-cancel-reason" class="mb-1.5 block text-sm font-semibold text-[#292B27]">
              دلیل لغو سفارش
            </label>
            <textarea
              id="pos-cancel-reason"
              v-model="cancelReason"
              rows="3"
              placeholder="مثلاً اتمام مواد اولیه یا درخواست مشتری"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-3 text-sm focus:border-[#183A2D] focus:bg-white focus:outline-none"
            />
          </div>
          <div class="flex justify-end gap-2">
            <button
              type="button"
              class="touch-target rounded-full border border-[#E8E5DC] bg-white px-5 py-2 text-sm font-semibold text-[#292B27]"
              @click="closeCancelDialog"
            >
              انصراف
            </button>
            <button
              type="submit"
              :disabled="canceling"
              class="touch-target rounded-full bg-[#A61B1B] px-6 py-2 text-sm font-bold text-white hover:opacity-90 disabled:opacity-60"
            >
              {{ canceling ? 'در حال لغو...' : 'تأیید لغو سفارش' }}
            </button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
</template>
