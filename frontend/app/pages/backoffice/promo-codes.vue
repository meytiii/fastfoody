<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { Pencil, Plus, Search, Tag, Trash2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import { backofficeApi } from '~/services/api'
import type { PromoCodeAdmin, PromoCodeWritePayload, PromoDiscountType } from '~/types'

const { formatDateTime, formatToman, toPersianDigits } = usePersian()

const promoCodes = ref<PromoCodeAdmin[]>([])
const loading = ref(true)
const searchQuery = ref('')
const activeFilter = ref<'all' | 'active' | 'inactive'>('all')

const promoDialogRef = ref<HTMLDialogElement | null>(null)
const deleteDialogRef = ref<HTMLDialogElement | null>(null)
const editingPromoId = ref<number | null>(null)
const promoToDelete = ref<PromoCodeAdmin | null>(null)
const saving = ref(false)
const deleting = ref(false)

useDialogLightDismiss(promoDialogRef, () => {
  void closePromoDialog()
})

useDialogLightDismiss(deleteDialogRef, () => {
  void closeDeleteDialog()
})

const promoForm = reactive({
  code: '',
  discount_type: 'PERCENTAGE' as PromoDiscountType,
  discount_value: 15,
  max_discount_amount: '' as string | number,
  min_order_amount: 0,
  valid_from_local: '',
  valid_until_local: '',
  max_total_uses: '' as string | number,
  max_uses_per_customer: 1,
  first_order_only: false,
  is_active: true,
})

function isoToLocalInput(iso: string | null): string {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (val: number) => String(val).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function localInputToIso(val: string): string | null {
  const trimmed = val.trim()
  if (!trimmed) return null
  const date = new Date(trimmed)
  if (Number.isNaN(date.getTime())) return null
  return date.toISOString()
}

async function loadPromoCodes() {
  loading.value = true
  try {
    const res = await backofficeApi.promoCodes.listPromoCodes({
      search: searchQuery.value.trim() || undefined,
      is_active:
        activeFilter.value === 'all' ? undefined : activeFilter.value === 'active',
      limit: 100,
    })
    promoCodes.value = res.results
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت کدهای تخفیف')
  } finally {
    loading.value = false
  }
}

function openCreateDialog() {
  editingPromoId.value = null
  promoForm.code = ''
  promoForm.discount_type = 'PERCENTAGE'
  promoForm.discount_value = 15
  promoForm.max_discount_amount = ''
  promoForm.min_order_amount = 0
  promoForm.valid_from_local = ''
  promoForm.valid_until_local = ''
  promoForm.max_total_uses = ''
  promoForm.max_uses_per_customer = 1
  promoForm.first_order_only = false
  promoForm.is_active = true
  promoDialogRef.value?.showModal()
}

function openEditDialog(promo: PromoCodeAdmin) {
  editingPromoId.value = promo.id
  promoForm.code = promo.code
  promoForm.discount_type = promo.discount_type
  promoForm.discount_value = promo.discount_value
  promoForm.max_discount_amount = promo.max_discount_amount ?? ''
  promoForm.min_order_amount = promo.min_order_amount
  promoForm.valid_from_local = isoToLocalInput(promo.valid_from)
  promoForm.valid_until_local = isoToLocalInput(promo.valid_until)
  promoForm.max_total_uses = promo.max_total_uses ?? ''
  promoForm.max_uses_per_customer = promo.max_uses_per_customer
  promoForm.first_order_only = promo.first_order_only
  promoForm.is_active = promo.is_active
  promoDialogRef.value?.showModal()
}

async function closePromoDialog() {
  await closeDialogSmoothly(promoDialogRef.value)
}

async function savePromoCode() {
  const code = promoForm.code.trim().toUpperCase()
  if (!code) {
    toast.error('وارد کردن کد تخفیف الزامی است')
    return
  }

  const maxDiscountNum =
    promoForm.discount_type === 'PERCENTAGE' && promoForm.max_discount_amount !== ''
      ? Math.max(0, Number(promoForm.max_discount_amount))
      : null

  const maxTotalNum =
    promoForm.max_total_uses !== '' ? Math.max(1, Number(promoForm.max_total_uses)) : null

  const payload: PromoCodeWritePayload = {
    code,
    discount_type: promoForm.discount_type,
    discount_value: Math.max(1, Number(promoForm.discount_value) || 0),
    max_discount_amount: maxDiscountNum,
    min_order_amount: Math.max(0, Number(promoForm.min_order_amount) || 0),
    valid_from: localInputToIso(promoForm.valid_from_local),
    valid_until: localInputToIso(promoForm.valid_until_local),
    max_total_uses: maxTotalNum,
    max_uses_per_customer: Math.max(1, Number(promoForm.max_uses_per_customer) || 1),
    first_order_only: Boolean(promoForm.first_order_only),
    is_active: Boolean(promoForm.is_active),
  }

  saving.value = true
  try {
    if (editingPromoId.value !== null) {
      await backofficeApi.promoCodes.updatePromoCode(editingPromoId.value, payload)
      toast.success('کد تخفیف ویرایش شد')
    } else {
      await backofficeApi.promoCodes.createPromoCode(payload)
      toast.success('کد تخفیف جدید ساخته شد')
    }
    await Promise.all([closePromoDialog(), loadPromoCodes()])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره کد تخفیف ناموفق بود')
  } finally {
    saving.value = false
  }
}

async function togglePromoActive(promo: PromoCodeAdmin) {
  try {
    await backofficeApi.promoCodes.updatePromoCode(promo.id, { is_active: !promo.is_active })
    await loadPromoCodes()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در تغییر وضعیت کد تخفیف')
  }
}

function openDeleteDialog(promo: PromoCodeAdmin) {
  promoToDelete.value = promo
  deleteDialogRef.value?.showModal()
}

async function closeDeleteDialog() {
  await closeDialogSmoothly(deleteDialogRef.value)
  promoToDelete.value = null
}

async function confirmDeletePromo() {
  if (!promoToDelete.value) return
  deleting.value = true
  try {
    await backofficeApi.promoCodes.deletePromoCode(promoToDelete.value.id)
    toast.success('کد تخفیف حذف شد')
    await Promise.all([closeDeleteDialog(), loadPromoCodes()])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در حذف کد تخفیف')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  void loadPromoCodes()
})

useHead({
  title: 'مدیریت کدهای تخفیف | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="مدیریت کدهای تخفیف"
      subtitle="ساخت، زمان‌بندی، محدودیت مصرف و فعال‌سازی کدهای تخفیف"
      @reset="loadPromoCodes"
    >
      <template #header-actions>
        <button
          type="button"
          class="touch-target inline-flex items-center gap-2 rounded-full bg-[#183A2D] px-5 py-2.5 text-xs font-bold text-white hover:bg-[#12251D]"
          @click="openCreateDialog"
        >
          <Plus class="h-4 w-4" />
          <span>کد تخفیف جدید</span>
        </button>
      </template>

      <div class="space-y-6">
        <form
          class="flex flex-wrap items-end gap-3 rounded-3xl border border-[#E8E5DC] bg-white p-5 shadow-sm"
          @submit.prevent="loadPromoCodes"
        >
          <div class="flex-1 min-w-[200px]">
            <label for="promo-search" class="mb-1 block text-xs font-semibold text-[#5A5D56]">
              جستجوی کد
            </label>
            <div class="relative">
              <Search class="pointer-events-none absolute top-1/2 start-3 h-4 w-4 -translate-y-1/2 text-[#5A5D56]" />
              <input
                id="promo-search"
                v-model="searchQuery"
                type="search"
                dir="ltr"
                placeholder="WELCOME20"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] py-2.5 ps-9 pe-3 text-sm uppercase"
              />
            </div>
          </div>

          <div>
            <label for="promo-status-filter" class="mb-1 block text-xs font-semibold text-[#5A5D56]">
              وضعیت
            </label>
            <select
              id="promo-status-filter"
              v-model="activeFilter"
              class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2.5 text-sm"
              @change="loadPromoCodes"
            >
              <option value="all">همه کدها</option>
              <option value="active">فعال</option>
              <option value="inactive">غیرفعال</option>
            </select>
          </div>

          <button
            type="submit"
            class="touch-target rounded-full bg-[#183A2D] px-6 py-2.5 text-xs font-bold text-white hover:bg-[#12251D]"
          >
            جستجو
          </button>
        </form>

        <div v-if="loading" class="space-y-3">
          <div v-for="n in 3" :key="n" class="h-16 animate-pulse rounded-2xl bg-[#E8E5DC]" />
        </div>

        <div
          v-else-if="promoCodes.length === 0"
          class="rounded-3xl border border-[#E8E5DC] bg-white p-12 text-center"
        >
          <Tag class="mx-auto mb-3 h-9 w-9 text-[#5A5D56]" />
          <p class="font-bold text-[#292B27]">کد تخفیفی یافت نشد</p>
          <p class="mt-1 text-xs text-[#5A5D56]">با دکمه «کد تخفیف جدید» اولین کد را ایجاد کنید.</p>
        </div>

        <div v-else class="rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm">
          <div class="table-wrapper">
            <table class="responsive-admin-table w-full border-collapse text-sm">
              <caption class="visually-hidden">فهرست کدهای تخفیف</caption>
              <thead>
                <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                  <th scope="col" class="px-3 py-3 text-start">کد تخفیف</th>
                  <th scope="col" class="px-3 py-3 text-start">مقدار تخفیف</th>
                  <th scope="col" class="px-3 py-3 text-start">شرایط و سقف</th>
                  <th scope="col" class="px-3 py-3 text-start">مصرف</th>
                  <th scope="col" class="px-3 py-3 text-start">بازه اعتبار</th>
                  <th scope="col" class="px-3 py-3 text-start">وضعیت</th>
                  <th scope="col" class="px-3 py-3 text-start">عملیات</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[#E8E5DC]">
                <tr v-for="promo in promoCodes" :key="promo.id" class="hover:bg-[#FAF7F2]">
                  <td data-label="کد تخفیف" class="px-3 py-3">
                    <span dir="ltr" class="inline-block rounded-lg bg-[#F4EFE3] px-2.5 py-1 font-mono text-xs font-extrabold text-[#183A2D]">
                      {{ promo.code }}
                    </span>
                    <span
                      v-if="promo.first_order_only"
                      class="mt-1 block text-[11px] font-semibold text-[#8A651C]"
                    >
                      ویژه سفارش اول
                    </span>
                  </td>
                  <td data-label="مقدار تخفیف" class="px-3 py-3">
                    <p class="font-bold text-[#292B27]">
                      {{
                        promo.discount_type === 'PERCENTAGE'
                          ? `${toPersianDigits(promo.discount_value)} درصد`
                          : formatToman(promo.discount_value)
                      }}
                    </p>
                    <p
                      v-if="promo.discount_type === 'PERCENTAGE' && promo.max_discount_amount"
                      class="text-xs text-[#5A5D56]"
                    >
                      سقف: {{ formatToman(promo.max_discount_amount) }}
                    </p>
                  </td>
                  <td data-label="شرایط و سقف" class="px-3 py-3 text-xs text-[#5A5D56]">
                    <p>حداقل سبد: {{ formatToman(promo.min_order_amount) }}</p>
                    <p>هر مشتری: {{ toPersianDigits(promo.max_uses_per_customer) }} بار</p>
                  </td>
                  <td data-label="مصرف" class="px-3 py-3 text-xs font-bold text-[#292B27]">
                    {{ toPersianDigits(promo.usage_count) }}
                    <span class="font-normal text-[#5A5D56]">
                      / {{ promo.max_total_uses ? toPersianDigits(promo.max_total_uses) : 'نامحدود' }}
                    </span>
                  </td>
                  <td data-label="بازه اعتبار" class="px-3 py-3 text-xs text-[#5A5D56]">
                    <p v-if="promo.valid_from">از {{ formatDateTime(promo.valid_from) }}</p>
                    <p v-if="promo.valid_until">تا {{ formatDateTime(promo.valid_until) }}</p>
                    <p v-if="!promo.valid_from && !promo.valid_until">بدون محدودیت زمانی</p>
                  </td>
                  <td data-label="وضعیت" class="px-3 py-3">
                    <button
                      type="button"
                      class="touch-target rounded-full px-3 py-1 text-xs font-bold"
                      :class="promo.is_active ? 'bg-[#EDF7ED] text-[#1E5E22]' : 'bg-[#FDE8E8] text-[#A61B1B]'"
                      @click="togglePromoActive(promo)"
                    >
                      {{ promo.is_active ? 'فعال' : 'غیرفعال' }}
                    </button>
                  </td>
                  <td data-label="عملیات" class="px-3 py-3">
                    <div class="flex flex-wrap gap-1.5">
                      <button
                        type="button"
                        class="touch-target inline-flex items-center gap-1 rounded-full border border-[#E8E5DC] bg-white px-3 py-1.5 text-xs font-semibold hover:bg-[#F4EFE3]"
                        @click="openEditDialog(promo)"
                      >
                        <Pencil class="h-3.5 w-3.5" />
                        <span>ویرایش</span>
                      </button>
                      <button
                        type="button"
                        class="touch-target inline-flex items-center gap-1 rounded-full bg-[#FDE8E8] px-3 py-1.5 text-xs font-semibold text-[#A61B1B] hover:bg-[#A61B1B] hover:text-white"
                        @click="openDeleteDialog(promo)"
                      >
                        <Trash2 class="h-3.5 w-3.5" />
                        <span>حذف</span>
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </BackofficeShell>

    <dialog
      ref="promoDialogRef"
      closedby="any"
      aria-labelledby="promo-dialog-title"
      class="modal-top-layer m-auto w-full max-w-xl rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-[var(--shadow-lg)]"
    >
      <div class="max-h-[90vh] overflow-y-auto p-6 sm:p-8">
        <h2 id="promo-dialog-title" class="mb-5 text-xl font-extrabold">
          {{ editingPromoId !== null ? 'ویرایش کد تخفیف' : 'ایجاد کد تخفیف جدید' }}
        </h2>

        <form class="space-y-4 text-sm" @submit.prevent="savePromoCode">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label for="pf-code" class="mb-1 block font-semibold">کد تخفیف *</label>
              <input
                id="pf-code"
                v-model="promoForm.code"
                type="text"
                dir="ltr"
                required
                placeholder="WELCOME20"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5 font-mono uppercase"
              />
            </div>

            <div>
              <label for="pf-type" class="mb-1 block font-semibold">نوع تخفیف *</label>
              <select
                id="pf-type"
                v-model="promoForm.discount_type"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              >
                <option value="PERCENTAGE">درصدی</option>
                <option value="FIXED">مبلغ ثابت (تومان)</option>
              </select>
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label for="pf-value" class="mb-1 block font-semibold">
                {{ promoForm.discount_type === 'PERCENTAGE' ? 'درصد تخفیف (۱ تا ۱۰۰) *' : 'مبلغ تخفیف (تومان) *' }}
              </label>
              <input
                id="pf-value"
                v-model.number="promoForm.discount_value"
                type="number"
                :min="1"
                :max="promoForm.discount_type === 'PERCENTAGE' ? 100 : undefined"
                dir="ltr"
                required
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>

            <div v-if="promoForm.discount_type === 'PERCENTAGE'">
              <label for="pf-max-discount" class="mb-1 block font-semibold">سقف تخفیف (تومان، اختیاری)</label>
              <input
                id="pf-max-discount"
                v-model="promoForm.max_discount_amount"
                type="number"
                min="0"
                dir="ltr"
                placeholder="مثلاً 100000"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-3">
            <div>
              <label for="pf-min-order" class="mb-1 block font-semibold">حداقل سبد خرید (تومان)</label>
              <input
                id="pf-min-order"
                v-model.number="promoForm.min_order_amount"
                type="number"
                min="0"
                dir="ltr"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>

            <div>
              <label for="pf-max-total" class="mb-1 block font-semibold">سقف کل مصرف</label>
              <input
                id="pf-max-total"
                v-model="promoForm.max_total_uses"
                type="number"
                min="1"
                dir="ltr"
                placeholder="نامحدود"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>

            <div>
              <label for="pf-max-customer" class="mb-1 block font-semibold">سقف هر مشتری</label>
              <input
                id="pf-max-customer"
                v-model.number="promoForm.max_uses_per_customer"
                type="number"
                min="1"
                dir="ltr"
                required
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>
          </div>

          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label for="pf-valid-from" class="mb-1 block font-semibold">شروع اعتبار (اختیاری)</label>
              <input
                id="pf-valid-from"
                v-model="promoForm.valid_from_local"
                type="datetime-local"
                dir="ltr"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>

            <div>
              <label for="pf-valid-until" class="mb-1 block font-semibold">پایان اعتبار (اختیاری)</label>
              <input
                id="pf-valid-until"
                v-model="promoForm.valid_until_local"
                type="datetime-local"
                dir="ltr"
                class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5"
              />
            </div>
          </div>

          <div class="flex flex-wrap gap-5 pt-1">
            <label class="flex items-center gap-2 font-semibold">
              <input v-model="promoForm.first_order_only" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
              <span>فقط برای اولین سفارش مشتری</span>
            </label>
            <label class="flex items-center gap-2 font-semibold">
              <input v-model="promoForm.is_active" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
              <span>کد فعال است</span>
            </label>
          </div>

          <div class="flex justify-end gap-2 pt-3">
            <button
              type="button"
              class="touch-target rounded-full border border-[#E8E5DC] px-5 py-2.5 font-semibold"
              @click="closePromoDialog"
            >
              انصراف
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="touch-target rounded-full bg-[#183A2D] px-7 py-2.5 font-bold text-white disabled:opacity-60"
            >
              {{ saving ? 'در حال ذخیره...' : 'ذخیره کد تخفیف' }}
            </button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog
      ref="deleteDialogRef"
      closedby="any"
      aria-labelledby="delete-promo-title"
      class="modal-top-layer m-auto w-full max-w-md rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-[var(--shadow-lg)]"
    >
      <div class="p-6 sm:p-7">
        <h2 id="delete-promo-title" class="text-lg font-extrabold">
          حذف کد تخفیف
        </h2>
        <p class="mt-2 text-xs leading-6 text-[#5A5D56]">
          آیا از حذف کد تخفیف <bdi dir="ltr" class="font-mono font-bold">{{ promoToDelete?.code }}</bdi> مطمئن هستید؟
        </p>
        <div class="mt-5 flex justify-end gap-2">
          <button
            type="button"
            class="touch-target rounded-full border border-[#E8E5DC] bg-white px-5 py-2 text-xs font-semibold"
            @click="closeDeleteDialog"
          >
            انصراف
          </button>
          <button
            type="button"
            :disabled="deleting"
            class="touch-target rounded-full bg-[#A61B1B] px-6 py-2 text-xs font-bold text-white hover:opacity-90 disabled:opacity-60"
            @click="confirmDeletePromo"
          >
            {{ deleting ? 'در حال حذف...' : 'تأیید حذف' }}
          </button>
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
