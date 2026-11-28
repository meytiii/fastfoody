<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { Eye, Search, Wallet } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import { backofficeApi } from '~/services/api'
import type {
  DeliveryType,
  OrderDetailBackoffice,
  OrderListBackoffice,
  OrderStatus,
  PaymentBackoffice,
  PaymentStatus,
} from '~/types'

const { formatDateTime, formatToman, toPersianDigits } = usePersian()

const orders = ref<OrderListBackoffice[]>([])
const totalCount = ref(0)
const loading = ref(true)
const errorMessage = ref('')

const filters = reactive({
  search: '',
  status: '' as OrderStatus | '',
  payment_status: '' as PaymentStatus | '',
  delivery_type: '' as DeliveryType | '',
  date_from: '',
  date_to: '',
  limit: 15,
  offset: 0,
})

const detailDialogRef = ref<HTMLDialogElement | null>(null)
const detailOrder = ref<OrderDetailBackoffice | null>(null)
const detailPayments = ref<PaymentBackoffice[]>([])
const detailLoading = ref(false)
const actionBusy = ref(false)
const cancelReasonInput = ref('')
const refundForm = reactive({
  card_number: '',
  tracking_code: '',
})

useDialogLightDismiss(detailDialogRef, () => {
  closeDetailDialog()
})

const statusLabels: Record<OrderStatus, string> = {
  PENDING_PAYMENT: 'در انتظار پرداخت',
  PROCESSING: 'در حال آماده‌سازی',
  READY: 'آماده تحویل',
  COMPLETED: 'تکمیل شده',
  CANCELED: 'لغو شده',
}

const paymentLabels: Record<PaymentStatus, string> = {
  UNPAID: 'پرداخت‌نشده',
  PAID: 'پرداخت‌شده',
  AWAITING_REFUND: 'در انتظار عودت',
  REFUNDED: 'عودت شده',
}

const awaitingRefundInPage = computed(
  () => orders.value.filter(o => o.payment_status === 'AWAITING_REFUND').length
)

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / filters.limit)))
const currentPage = computed(() => Math.floor(filters.offset / filters.limit) + 1)

function statusBadgeClass(status: OrderStatus): string {
  if (status === 'COMPLETED' || status === 'READY') return 'bg-[#EDF7ED] text-[#1E5E22]'
  if (status === 'CANCELED') return 'bg-[#FDE8E8] text-[#A61B1B]'
  return 'bg-[#FFF4E5] text-[#9A4300]'
}

function paymentBadgeClass(status: PaymentStatus): string {
  if (status === 'PAID') return 'bg-[#EDF7ED] text-[#1E5E22]'
  if (status === 'AWAITING_REFUND') return 'bg-[#FDE8E8] text-[#A61B1B]'
  if (status === 'REFUNDED') return 'bg-[#E1F5FE] text-[#026AA7]'
  return 'bg-[#F4EFE3] text-[#5A5D56]'
}

async function fetchOrders(resetOffset = false) {
  if (resetOffset) filters.offset = 0
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await backofficeApi.orders.listOrders({
      search: filters.search || undefined,
      status: filters.status || undefined,
      payment_status: filters.payment_status || undefined,
      delivery_type: filters.delivery_type || undefined,
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      limit: filters.limit,
      offset: filters.offset,
    })
    orders.value = res.results
    totalCount.value = res.count
  } catch (err) {
    errorMessage.value = err instanceof Error ? err.message : 'خطا در دریافت لیست سفارش‌ها'
  } finally {
    loading.value = false
  }
}

function filterAwaitingRefund() {
  filters.payment_status = 'AWAITING_REFUND'
  filters.status = ''
  fetchOrders(true)
}

function changePage(nextPage: number) {
  filters.offset = (nextPage - 1) * filters.limit
  fetchOrders(false)
}

async function openOrderDetail(orderId: number) {
  detailLoading.value = true
  detailOrder.value = null
  detailPayments.value = []
  cancelReasonInput.value = ''
  refundForm.card_number = ''
  refundForm.tracking_code = ''
  detailDialogRef.value?.showModal()
  try {
    const [order, payments] = await Promise.all([
      backofficeApi.orders.getOrder(orderId),
      backofficeApi.payments.listOrderPayments(orderId),
    ])
    detailOrder.value = order
    detailPayments.value = payments
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت جزئیات سفارش')
    await closeDetailDialog()
  } finally {
    detailLoading.value = false
  }
}

async function closeDetailDialog() {
  await closeDialogSmoothly(detailDialogRef.value)
  detailOrder.value = null
}

async function refreshDetail(orderId: number) {
  const [order, payments] = await Promise.all([
    backofficeApi.orders.getOrder(orderId),
    backofficeApi.payments.listOrderPayments(orderId),
  ])
  detailOrder.value = order
  detailPayments.value = payments
  await fetchOrders(false)
}

async function handleStatusAction(action: 'ready' | 'complete') {
  if (!detailOrder.value) return
  actionBusy.value = true
  try {
    if (action === 'ready') {
      await backofficeApi.orders.markReady(detailOrder.value.id)
      toast.success('وضعیت سفارش به آماده تحویل تغییر یافت')
    } else {
      await backofficeApi.orders.markCompleted(detailOrder.value.id)
      toast.success('سفارش تکمیل شد')
    }
    await refreshDetail(detailOrder.value.id)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'تغییر وضعیت ناموفق بود')
  } finally {
    actionBusy.value = false
  }
}

async function handleCancelOrder() {
  if (!detailOrder.value) return
  actionBusy.value = true
  try {
    await backofficeApi.orders.cancelOrder(detailOrder.value.id, cancelReasonInput.value.trim())
    toast.success('سفارش لغو شد')
    await refreshDetail(detailOrder.value.id)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'لغو سفارش ناموفق بود')
  } finally {
    actionBusy.value = false
  }
}

async function handleRecordRefund() {
  if (!detailOrder.value) return
  actionBusy.value = true
  try {
    await backofficeApi.orders.recordRefund(detailOrder.value.id, {
      card_number: refundForm.card_number.trim(),
      tracking_code: refundForm.tracking_code.trim(),
    })
    toast.success('اطلاعات عودت وجه ثبت شد')
    await refreshDetail(detailOrder.value.id)
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ثبت عودت وجه ناموفق بود')
  } finally {
    actionBusy.value = false
  }
}

onMounted(() => {
  fetchOrders(true)
})

useHead({
  title: 'سفارش‌ها و عودت | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="سفارش‌ها و عودت وجه"
      subtitle="جستجو، بررسی تراکنش‌ها و ثبت عودت برای سفارش‌های لغوشده"
      @reset="fetchOrders(true)"
    >
      <div class="space-y-6">
        <div
          v-if="awaitingRefundInPage > 0"
          class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4"
        >
          <div class="flex items-center gap-2 text-sm font-bold text-[#A61B1B]">
            <Wallet class="h-5 w-5" />
            <span>{{ toPersianDigits(awaitingRefundInPage) }} سفارش در این صفحه در انتظار ثبت عودت وجه است.</span>
          </div>
          <button
            type="button"
            class="touch-target rounded-full bg-[#A61B1B] px-4 py-1.5 text-xs font-bold text-white hover:opacity-90"
            @click="filterAwaitingRefund"
          >
            نمایش در انتظار عودت‌ها
          </button>
        </div>

        <form
          class="grid gap-3 rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm sm:grid-cols-2 lg:grid-cols-6"
          @submit.prevent="fetchOrders(true)"
        >
          <div class="lg:col-span-2">
            <label for="ord-search" class="mb-1 block text-xs font-semibold text-[#5A5D56]">جستجو</label>
            <div class="relative">
              <input
                id="ord-search"
                v-model="filters.search"
                type="search"
                placeholder="کد سفارش، موبایل یا نام"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] py-2.5 ps-3 pe-9 text-sm"
              />
              <Search class="pointer-events-none absolute top-3 end-3 h-4 w-4 text-[#5A5D56]" />
            </div>
          </div>

          <div>
            <label for="ord-status" class="mb-1 block text-xs font-semibold text-[#5A5D56]">وضعیت سفارش</label>
            <select
              id="ord-status"
              v-model="filters.status"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm"
              @change="fetchOrders(true)"
            >
              <option value="">همه</option>
              <option value="PENDING_PAYMENT">در انتظار پرداخت</option>
              <option value="PROCESSING">در حال آماده‌سازی</option>
              <option value="READY">آماده تحویل</option>
              <option value="COMPLETED">تکمیل شده</option>
              <option value="CANCELED">لغو شده</option>
            </select>
          </div>

          <div>
            <label for="ord-pay" class="mb-1 block text-xs font-semibold text-[#5A5D56]">وضعیت پرداخت</label>
            <select
              id="ord-pay"
              v-model="filters.payment_status"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm"
              @change="fetchOrders(true)"
            >
              <option value="">همه</option>
              <option value="UNPAID">پرداخت‌نشده</option>
              <option value="PAID">پرداخت‌شده</option>
              <option value="AWAITING_REFUND">در انتظار عودت</option>
              <option value="REFUNDED">عودت شده</option>
            </select>
          </div>

          <div>
            <label for="ord-deliv" class="mb-1 block text-xs font-semibold text-[#5A5D56]">نحوه تحویل</label>
            <select
              id="ord-deliv"
              v-model="filters.delivery_type"
              class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2.5 text-sm"
              @change="fetchOrders(true)"
            >
              <option value="">همه</option>
              <option value="DELIVERY">ارسال پیک</option>
              <option value="PICKUP">تحویل حضوری</option>
            </select>
          </div>

          <div class="flex items-end gap-2">
            <button
              type="submit"
              class="touch-target w-full rounded-xl bg-[#183A2D] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#12251D]"
            >
              اعمال فیلتر
            </button>
          </div>
        </form>

        <div
          v-if="errorMessage"
          role="alert"
          class="rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4 text-sm font-medium text-[#A61B1B]"
        >
          {{ errorMessage }}
        </div>

        <div class="rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm sm:p-6">
          <div v-if="loading" class="space-y-3">
            <div v-for="i in 5" :key="i" class="h-12 animate-pulse rounded-xl bg-[#F4EFE3]" />
          </div>

          <p v-else-if="orders.length === 0" class="py-10 text-center text-sm text-[#5A5D56]">
            سفارشی با فیلترهای انتخابی یافت نشد.
          </p>

          <div v-else class="table-wrapper">
            <table class="responsive-admin-table w-full border-collapse text-sm">
              <caption class="visually-hidden">فهرست سفارش‌های ثبت‌شده در سیستم</caption>
              <thead>
                <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                  <th scope="col" class="px-3 py-3 text-start">شناسه / نوبت</th>
                  <th scope="col" class="px-3 py-3 text-start">مشتری</th>
                  <th scope="col" class="px-3 py-3 text-start">تحویل</th>
                  <th scope="col" class="px-3 py-3 text-start">مبلغ</th>
                  <th scope="col" class="px-3 py-3 text-start">وضعیت</th>
                  <th scope="col" class="px-3 py-3 text-start">پرداخت</th>
                  <th scope="col" class="px-3 py-3 text-start">تاریخ</th>
                  <th scope="col" class="px-3 py-3 text-start">عملیات</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E8E5DC]">
                <tr v-for="ord in orders" :key="ord.id" class="hover:bg-[#FAF7F2]">
                  <td data-label="شناسه" class="px-3 py-3 font-bold text-[#292B27]">
                    #{{ toPersianDigits(ord.id) }}
                    <span v-if="ord.daily_number" class="me-1 rounded-md bg-[#F4EFE3] px-1.5 py-0.5 text-xs">
                      نوبت {{ toPersianDigits(ord.daily_number) }}
                    </span>
                  </td>
                  <td data-label="مشتری" class="px-3 py-3">
                    <p class="font-semibold text-[#292B27]">{{ ord.customer_full_name || 'مشتری' }}</p>
                    <p dir="ltr" class="text-xs text-[#5A5D56]">{{ toPersianDigits(ord.customer_phone) }}</p>
                  </td>
                  <td data-label="تحویل" class="px-3 py-3 text-xs font-semibold">
                    {{ ord.delivery_type === 'DELIVERY' ? 'پیک' : 'حضوری' }}
                  </td>
                  <td data-label="مبلغ" class="px-3 py-3 font-bold text-[#183A2D]">
                    {{ formatToman(ord.total_amount) }}
                  </td>
                  <td data-label="وضعیت" class="px-3 py-3">
                    <span class="inline-block rounded-full px-2.5 py-1 text-xs font-bold" :class="statusBadgeClass(ord.status)">
                      {{ statusLabels[ord.status] }}
                    </span>
                  </td>
                  <td data-label="پرداخت" class="px-3 py-3">
                    <span class="inline-block rounded-full px-2.5 py-1 text-xs font-bold" :class="paymentBadgeClass(ord.payment_status)">
                      {{ paymentLabels[ord.payment_status] }}
                    </span>
                  </td>
                  <td data-label="تاریخ" class="px-3 py-3 text-xs text-[#5A5D56]">
                    {{ formatDateTime(ord.created_at) }}
                  </td>
                  <td data-label="عملیات" class="px-3 py-3">
                    <button
                      type="button"
                      class="touch-target inline-flex items-center gap-1 rounded-full border border-[#E8E5DC] bg-white px-3.5 py-1.5 text-xs font-bold text-[#183A2D] hover:bg-[#F4EFE3]"
                      @click="openOrderDetail(ord.id)"
                    >
                      <Eye class="h-3.5 w-3.5" />
                      <span>جزئیات</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div
            v-if="totalCount > filters.limit"
            class="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-[#E8E5DC] pt-4 text-xs"
          >
            <p class="text-[#5A5D56]">
              نمایش صفحه {{ toPersianDigits(currentPage) }} از {{ toPersianDigits(totalPages) }}
              (مجموع {{ toPersianDigits(totalCount) }} سفارش)
            </p>
            <div class="flex items-center gap-2">
              <button
                type="button"
                :disabled="currentPage <= 1"
                class="touch-target rounded-full border border-[#E8E5DC] bg-white px-4 py-1.5 font-semibold disabled:opacity-50"
                @click="changePage(currentPage - 1)"
              >
                قبلی
              </button>
              <button
                type="button"
                :disabled="currentPage >= totalPages"
                class="touch-target rounded-full border border-[#E8E5DC] bg-white px-4 py-1.5 font-semibold disabled:opacity-50"
                @click="changePage(currentPage + 1)"
              >
                بعدی
              </button>
            </div>
          </div>
        </div>
      </div>
    </BackofficeShell>

    <dialog
      ref="detailDialogRef"
      closedby="any"
      aria-labelledby="order-detail-title"
      class="modal-top-layer m-auto w-full max-w-2xl rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-[var(--shadow-lg)]"
    >
      <div class="max-h-[90vh] overflow-y-auto p-6 sm:p-8">
        <div class="mb-5 flex items-center justify-between gap-4 border-b border-[#E8E5DC] pb-4">
          <h2 id="order-detail-title" class="text-xl font-extrabold text-[#292B27]">
            جزئیات سفارش #{{ toPersianDigits(detailOrder?.id) }}
          </h2>
          <button
            type="button"
            class="touch-target rounded-full px-3 py-1.5 text-sm font-semibold text-[#5A5D56] hover:bg-[#F4EFE3]"
            @click="closeDetailDialog"
          >
            بستن
          </button>
        </div>

        <div v-if="detailLoading" class="space-y-4">
          <div class="h-24 animate-pulse rounded-2xl bg-[#F4EFE3]" />
          <div class="h-36 animate-pulse rounded-2xl bg-[#F4EFE3]" />
        </div>

        <div v-else-if="detailOrder" class="space-y-6 text-sm">
          <div class="grid gap-4 rounded-2xl bg-[#FAF7F2] p-4 sm:grid-cols-2">
            <div>
              <p class="text-xs text-[#5A5D56]">مشتری</p>
              <p class="mt-0.5 font-bold">{{ detailOrder.customer.full_name || 'مشتری' }}</p>
              <p dir="ltr" class="text-xs font-semibold text-[#5A5D56]">
                {{ toPersianDigits(detailOrder.customer.phone) }}
              </p>
            </div>
            <div>
              <p class="text-xs text-[#5A5D56]">تحویل</p>
              <p class="mt-0.5 font-bold">
                {{ detailOrder.delivery_type === 'DELIVERY' ? 'ارسال پیک' : 'تحویل حضوری' }}
              </p>
              <p v-if="detailOrder.delivery_address_snapshot" class="mt-1 text-xs leading-5 text-[#5A5D56]">
                {{ detailOrder.delivery_address_snapshot }}
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <h3 class="font-bold text-[#292B27]">اقلام سفارش</h3>
            <ul class="divide-y divide-[#E8E5DC] rounded-2xl border border-[#E8E5DC] bg-white px-4">
              <li v-for="item in detailOrder.items" :key="item.id" class="py-3">
                <div class="flex justify-between font-bold">
                  <span>{{ toPersianDigits(item.quantity) }}x {{ item.product_name_snapshot }}</span>
                  <span>{{ formatToman(item.line_total) }}</span>
                </div>
                <p v-for="addon in item.addons" :key="addon.addon_id" class="mt-0.5 ps-3 text-xs text-[#5A5D56]">
                  + {{ toPersianDigits(addon.quantity) }}x {{ addon.addon_name_snapshot }} ({{ formatToman(addon.line_total) }})
                </p>
              </li>
            </ul>
            <div class="flex flex-wrap items-center justify-between gap-2 pt-2 text-xs text-[#5A5D56]">
              <span>جمع غذاها: {{ formatToman(detailOrder.subtotal) }}</span>
              <span>بسته‌بندی: {{ formatToman(detailOrder.packaging_fee) }}</span>
              <span>هزینه ارسال: {{ formatToman(detailOrder.delivery_fee) }}</span>
              <span v-if="detailOrder.discount_amount > 0" class="font-bold text-[#1E5E22]">
                تخفیف (<bdi dir="ltr">{{ detailOrder.promo_code_snapshot }}</bdi>): - {{ formatToman(detailOrder.discount_amount) }}
              </span>
              <span class="text-sm font-extrabold text-[#183A2D]">مبلغ کل: {{ formatToman(detailOrder.total_amount) }}</span>
            </div>
          </div>

          <div
            v-if="detailOrder.cancellation_requested && detailOrder.status !== 'CANCELED'"
            role="alert"
            class="rounded-2xl border border-[#D6A84B]/50 bg-[#FFF4E5] p-4 text-xs space-y-1 text-[#9A4300]"
          >
            <p class="font-bold">درخواست لغو توسط مشتری ثبت شده است</p>
            <p v-if="detailOrder.cancellation_request_reason">
              دلیل مشتری: {{ detailOrder.cancellation_request_reason }}
            </p>
            <p v-if="detailOrder.cancellation_requested_at">
              زمان ثبت درخواست: {{ formatDateTime(detailOrder.cancellation_requested_at) }}
            </p>
          </div>

          <div v-if="detailOrder.customer_notes && detailOrder.customer_notes.length > 0" class="space-y-2">
            <h3 class="font-bold text-[#292B27]">یادداشت‌های CRM مشتری</h3>
            <ul class="space-y-2">
              <li
                v-for="(note, idx) in detailOrder.customer_notes"
                :key="`${note.created_at}-${idx}`"
                class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2.5 text-xs space-y-1"
              >
                <p class="font-medium text-[#292B27]">{{ note.text }}</p>
                <p class="text-[11px] text-[#72756E]">
                  ثبت توسط {{ note.author_name || note.author_phone || 'ادمین' }} در {{ formatDateTime(note.created_at) }}
                </p>
              </li>
            </ul>
          </div>

          <div v-if="detailPayments.length > 0" class="space-y-2">
            <h3 class="font-bold text-[#292B27]">تراکنش‌های درگاه پرداخت</h3>
            <div class="space-y-2">
              <div
                v-for="pay in detailPayments"
                :key="pay.id"
                class="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2.5 text-xs"
              >
                <span class="font-mono">Authority: {{ pay.authority }}</span>
                <span v-if="pay.ref_id" class="font-bold">کد پیگیری: {{ toPersianDigits(pay.ref_id) }}</span>
                <span class="font-bold text-[#183A2D]">{{ pay.status }}</span>
              </div>
            </div>
          </div>

          <div
            v-if="detailOrder.status === 'CANCELED' && detailOrder.cancellation_reason"
            class="rounded-2xl border border-[#A61B1B]/25 bg-[#FDE8E8] p-4 text-xs text-[#A61B1B]"
          >
            دلیل لغو: {{ detailOrder.cancellation_reason }}
          </div>

          <div
            v-if="detailOrder.payment_status === 'AWAITING_REFUND'"
            class="space-y-3 rounded-2xl border border-[#D6A84B]/40 bg-[#F8F3E8] p-4"
          >
            <h3 class="font-bold text-[#8A651C]">ثبت عودت وجه دستی (کارت به کارت)</h3>
            <form class="grid gap-3 sm:grid-cols-2" @submit.prevent="handleRecordRefund">
              <div>
                <label for="refund-card" class="mb-1 block text-xs font-semibold">شماره کارت مقصد *</label>
                <input
                  id="refund-card"
                  v-model="refundForm.card_number"
                  type="text"
                  dir="ltr"
                  required
                  placeholder="6037-9975-xxxx-xxxx"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label for="refund-trace" class="mb-1 block text-xs font-semibold">کد پیگیری انتقال *</label>
                <input
                  id="refund-trace"
                  v-model="refundForm.tracking_code"
                  type="text"
                  dir="ltr"
                  required
                  placeholder="TR-998811"
                  class="w-full rounded-xl border border-[#E8E5DC] bg-white px-3 py-2 text-sm"
                />
              </div>
              <div class="sm:col-span-2">
                <button
                  type="submit"
                  :disabled="actionBusy"
                  class="touch-target rounded-full bg-[#183A2D] px-6 py-2.5 text-xs font-bold text-white hover:bg-[#12251D]"
                >
                  ثبت نهایی عودت وجه
                </button>
              </div>
            </form>
          </div>

          <div
            v-else-if="detailOrder.payment_status === 'REFUNDED'"
            class="rounded-2xl border border-[#026AA7]/25 bg-[#E1F5FE] p-4 text-xs text-[#026AA7]"
          >
            عودت وجه به شماره کارت <span dir="ltr" class="font-mono font-bold">{{ detailOrder.refund_card_number }}</span>
            با کد پیگیری <span dir="ltr" class="font-mono font-bold">{{ detailOrder.refund_tracking_code }}</span>
            ثبت شده است.
          </div>

          <div
            v-if="detailOrder.status === 'PROCESSING' || detailOrder.status === 'READY'"
            class="space-y-3 border-t border-[#E8E5DC] pt-4"
          >
            <div class="flex flex-wrap gap-2">
              <button
                v-if="detailOrder.status === 'PROCESSING'"
                type="button"
                :disabled="actionBusy"
                class="touch-target rounded-full bg-[#183A2D] px-5 py-2 text-xs font-bold text-white"
                @click="handleStatusAction('ready')"
              >
                علامت‌گذاری به عنوان آماده تحویل
              </button>
              <button
                type="button"
                :disabled="actionBusy"
                class="touch-target rounded-full bg-[#EDF7ED] px-5 py-2 text-xs font-bold text-[#1E5E22]"
                @click="handleStatusAction('complete')"
              >
                تکمیل سفارش
              </button>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <label for="detail-cancel-reason" class="visually-hidden">دلیل لغو سفارش</label>
              <input
                id="detail-cancel-reason"
                v-model="cancelReasonInput"
                type="text"
                placeholder="دلیل لغو سفارش..."
                class="flex-1 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-xs"
              />
              <button
                type="button"
                :disabled="actionBusy"
                class="touch-target rounded-full bg-[#FDE8E8] px-4 py-2 text-xs font-bold text-[#A61B1B]"
                @click="handleCancelOrder"
              >
                لغو سفارش
              </button>
            </div>
          </div>
        </div>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
@container (width < 46rem) {
  .responsive-admin-table thead {
    display: none;
  }

  .responsive-admin-table tr {
    display: block;
    margin-bottom: 1rem;
    border: 1px solid #E8E5DC;
    border-radius: 1rem;
    padding: 0.75rem 1rem;
  }

  .responsive-admin-table td {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.375rem 0;
    border-bottom: 1px solid #F4EFE3;
  }

  .responsive-admin-table td:last-child {
    border-bottom: none;
  }

  .responsive-admin-table td::before {
    content: attr(data-label);
    font-weight: 700;
    font-size: 0.75rem;
    color: #5A5D56;
  }
}
</style>
