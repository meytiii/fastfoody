<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ImagePlus, Pencil, Plus, Search, Trash2 } from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import BackofficeShell from '~/components/backoffice/BackofficeShell.vue'
import { closeDialogSmoothly, useDialogLightDismiss } from '~/composables/useDialogControl'
import { backofficeApi } from '~/services/api'
import { useMenuStore } from '~/stores/menu'
import type {
  AddOnAdmin,
  AddonLinkInput,
  CategoryAdmin,
  ProductAdmin,
  ProductStatus,
  ProductWritePayload,
} from '~/types'

const menuStore = useMenuStore()
const { formatToman, toPersianDigits } = usePersian()

const activeTab = ref<'products' | 'categories' | 'addons'>('products')

const categories = ref<CategoryAdmin[]>([])
const addons = ref<AddOnAdmin[]>([])
const products = ref<ProductAdmin[]>([])
const loading = ref(true)

const productFilters = reactive({
  search: '',
  category_id: '' as number | '',
  status: '' as ProductStatus | '',
  is_main_dish: '' as 'true' | 'false' | '',
})

const productDialogRef = ref<HTMLDialogElement | null>(null)
const categoryDialogRef = ref<HTMLDialogElement | null>(null)
const addonDialogRef = ref<HTMLDialogElement | null>(null)

useDialogLightDismiss(productDialogRef, () => closeProductDialog())
useDialogLightDismiss(categoryDialogRef, () => closeCategoryDialog())
useDialogLightDismiss(addonDialogRef, () => closeAddonDialog())

const editingProductId = ref<number | null>(null)
const savingProduct = ref(false)
const uploadedProductImage = ref<string | undefined>(undefined)
const existingProductImageUrl = ref<string | null>(null)

const productForm = reactive({
  name: '',
  slug: '',
  category_id: 0,
  description: '',
  price: 0,
  compare_at_price: '' as number | '',
  stock_quantity: '' as number | '',
  status: 'AVAILABLE' as ProductStatus,
  is_main_dish: true,
  prep_time_minutes: 15,
  display_order: 1,
})

const selectedAddonMap = reactive<Record<number, { enabled: boolean; min_quantity: number; max_quantity: number }>>({})

const editingCategoryId = ref<number | null>(null)
const savingCategory = ref(false)
const categoryForm = reactive({
  name: '',
  slug: '',
  parent_id: '' as number | '',
  description: '',
  display_order: 1,
  is_active: true,
})

const editingAddonId = ref<number | null>(null)
const savingAddon = ref(false)
const addonForm = reactive({
  name: '',
  price: 0,
  is_available: true,
})

const statusLabels: Record<ProductStatus, string> = {
  AVAILABLE: 'موجود',
  OUT_OF_STOCK: 'ناموجود',
  HIDDEN: 'مخفی',
}

const categoryMap = computed(() => new Map(categories.value.map(c => [c.id, c])))

const availableParentCategories = computed(() =>
  categories.value.filter(c => c.id !== editingCategoryId.value)
)

async function loadAllCatalogData() {
  loading.value = true
  try {
    const [catRes, addonRes, prodRes] = await Promise.all([
      backofficeApi.catalog.listCategories(),
      backofficeApi.catalog.listAddOns(),
      backofficeApi.catalog.listProducts({
        search: productFilters.search || undefined,
        category_id: productFilters.category_id ? Number(productFilters.category_id) : undefined,
        status: productFilters.status || undefined,
        is_main_dish:
          productFilters.is_main_dish === ''
            ? undefined
            : productFilters.is_main_dish === 'true',
        limit: 100,
      }),
    ])
    categories.value = catRes.results
    addons.value = addonRes.results
    products.value = prodRes.results
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در دریافت اطلاعات کاتالوگ')
  } finally {
    loading.value = false
  }
}

async function fetchProductsOnly() {
  try {
    const res = await backofficeApi.catalog.listProducts({
      search: productFilters.search || undefined,
      category_id: productFilters.category_id ? Number(productFilters.category_id) : undefined,
      status: productFilters.status || undefined,
      is_main_dish:
        productFilters.is_main_dish === ''
          ? undefined
          : productFilters.is_main_dish === 'true',
      limit: 100,
    })
    products.value = res.results
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در فیلتر محصولات')
  }
}

function generateSlug(source: string): string {
  return source
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u0600-\u06ff\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

function resetAddonSelectionMap() {
  for (const addon of addons.value) {
    selectedAddonMap[addon.id] = {
      enabled: false,
      min_quantity: 0,
      max_quantity: 2,
    }
  }
}

function openCreateProduct() {
  editingProductId.value = null
  uploadedProductImage.value = undefined
  existingProductImageUrl.value = null
  productForm.name = ''
  productForm.slug = ''
  productForm.category_id = categories.value[0]?.id ?? 0
  productForm.description = ''
  productForm.price = 150000
  productForm.compare_at_price = ''
  productForm.stock_quantity = ''
  productForm.status = 'AVAILABLE'
  productForm.is_main_dish = true
  productForm.prep_time_minutes = 15
  productForm.display_order = products.value.length + 1
  resetAddonSelectionMap()
  productDialogRef.value?.showModal()
}

async function openEditProduct(prod: ProductAdmin) {
  try {
    const detail = await backofficeApi.catalog.getProduct(prod.id)
    editingProductId.value = detail.id
    uploadedProductImage.value = undefined
    existingProductImageUrl.value = detail.image_url
    productForm.name = detail.name
    productForm.slug = detail.slug
    productForm.category_id = detail.category.id
    productForm.description = detail.description
    productForm.price = detail.price
    productForm.compare_at_price = detail.compare_at_price ?? ''
    productForm.stock_quantity = detail.stock_quantity ?? ''
    productForm.status = detail.status
    productForm.is_main_dish = detail.is_main_dish
    productForm.prep_time_minutes = detail.prep_time_minutes
    productForm.display_order = detail.display_order
    resetAddonSelectionMap()
    for (const link of detail.addons) {
      selectedAddonMap[link.addon_id] = {
        enabled: true,
        min_quantity: link.min_quantity,
        max_quantity: link.max_quantity,
      }
    }
    productDialogRef.value?.showModal()
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در بارگذاری محصول')
  }
}

async function closeProductDialog() {
  await closeDialogSmoothly(productDialogRef.value)
}

function handleProductImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 10 * 1024 * 1024) {
    toast.error('حجم تصویر نباید بیشتر از ۱۰ مگابایت باشد')
    input.value = ''
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    if (typeof reader.result === 'string') {
      uploadedProductImage.value = reader.result
    }
  }
  reader.readAsDataURL(file)
}

async function saveProduct() {
  if (!productForm.name.trim() || !productForm.category_id) {
    toast.error('نام محصول و دسته‌بندی الزامی است')
    return
  }
  const slugVal = productForm.slug.trim() || generateSlug(productForm.name) || `item-${Date.now()}`
  const addonLinks: AddonLinkInput[] = []
  for (const addon of addons.value) {
    const sel = selectedAddonMap[addon.id]
    if (sel?.enabled) {
      addonLinks.push({
        addon_id: addon.id,
        min_quantity: Math.max(0, Number(sel.min_quantity) || 0),
        max_quantity: Math.max(1, Number(sel.max_quantity) || 1),
      })
    }
  }

  const payload: ProductWritePayload = {
    name: productForm.name.trim(),
    slug: slugVal,
    category_id: Number(productForm.category_id),
    description: productForm.description.trim(),
    price: Number(productForm.price),
    compare_at_price: productForm.compare_at_price === '' ? null : Number(productForm.compare_at_price),
    stock_quantity: productForm.stock_quantity === '' ? null : Number(productForm.stock_quantity),
    status: productForm.status,
    is_main_dish: productForm.is_main_dish,
    prep_time_minutes: Number(productForm.prep_time_minutes) || 0,
    display_order: Number(productForm.display_order) || 0,
    addons: addonLinks,
  }

  savingProduct.value = true
  try {
    if (editingProductId.value !== null) {
      await backofficeApi.catalog.updateProduct(
        editingProductId.value,
        payload,
        uploadedProductImage.value
      )
      await backofficeApi.catalog.setProductAddons(editingProductId.value, addonLinks)
      toast.success('محصول با موفقیت ویرایش شد')
    } else {
      await backofficeApi.catalog.createProduct(payload, uploadedProductImage.value)
      toast.success('محصول جدید ایجاد شد')
    }
    await Promise.all([closeProductDialog(), loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره محصول ناموفق بود')
  } finally {
    savingProduct.value = false
  }
}

async function deleteProduct(prod: ProductAdmin) {
  try {
    await backofficeApi.catalog.deleteProduct(prod.id)
    toast.success(`محصول «${prod.name}» حذف شد`)
    await Promise.all([loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'خطا در حذف محصول')
  }
}

function openCreateCategory() {
  editingCategoryId.value = null
  categoryForm.name = ''
  categoryForm.slug = ''
  categoryForm.parent_id = ''
  categoryForm.description = ''
  categoryForm.display_order = categories.value.length + 1
  categoryForm.is_active = true
  categoryDialogRef.value?.showModal()
}

function openEditCategory(cat: CategoryAdmin) {
  editingCategoryId.value = cat.id
  categoryForm.name = cat.name
  categoryForm.slug = cat.slug
  categoryForm.parent_id = cat.parent_id ?? ''
  categoryForm.description = cat.description
  categoryForm.display_order = cat.display_order
  categoryForm.is_active = cat.is_active
  categoryDialogRef.value?.showModal()
}

async function closeCategoryDialog() {
  await closeDialogSmoothly(categoryDialogRef.value)
}

async function saveCategory() {
  if (!categoryForm.name.trim()) {
    toast.error('نام دسته‌بندی الزامی است')
    return
  }
  const slugVal = categoryForm.slug.trim() || generateSlug(categoryForm.name) || `cat-${Date.now()}`
  const payload = {
    name: categoryForm.name.trim(),
    slug: slugVal,
    parent_id: categoryForm.parent_id === '' ? null : Number(categoryForm.parent_id),
    description: categoryForm.description.trim(),
    display_order: Number(categoryForm.display_order) || 0,
    is_active: categoryForm.is_active,
  }
  savingCategory.value = true
  try {
    if (editingCategoryId.value !== null) {
      await backofficeApi.catalog.updateCategory(editingCategoryId.value, payload)
      toast.success('دسته‌بندی ویرایش شد')
    } else {
      await backofficeApi.catalog.createCategory(payload)
      toast.success('دسته‌بندی جدید ثبت شد')
    }
    await Promise.all([closeCategoryDialog(), loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره دسته‌بندی ناموفق بود')
  } finally {
    savingCategory.value = false
  }
}

async function toggleCategoryActive(cat: CategoryAdmin) {
  try {
    await backofficeApi.catalog.updateCategory(cat.id, { is_active: !cat.is_active })
    await Promise.all([loadAllCatalogData(), menuStore.fetchMenu(true)])
    toast.success('وضعیت دسته‌بندی تغییر کرد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'تغییر وضعیت ناموفق بود')
  }
}

async function deleteCategory(cat: CategoryAdmin) {
  try {
    await backofficeApi.catalog.deleteCategory(cat.id)
    toast.success(`دسته‌بندی «${cat.name}» حذف شد`)
    await Promise.all([loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'حذف دسته‌بندی ناموفق بود')
  }
}

function openCreateAddon() {
  editingAddonId.value = null
  addonForm.name = ''
  addonForm.price = 25000
  addonForm.is_available = true
  addonDialogRef.value?.showModal()
}

function openEditAddon(addon: AddOnAdmin) {
  editingAddonId.value = addon.id
  addonForm.name = addon.name
  addonForm.price = addon.price
  addonForm.is_available = addon.is_available
  addonDialogRef.value?.showModal()
}

async function closeAddonDialog() {
  await closeDialogSmoothly(addonDialogRef.value)
}

async function saveAddon() {
  if (!addonForm.name.trim()) {
    toast.error('نام افزودنی الزامی است')
    return
  }
  savingAddon.value = true
  try {
    const payload = {
      name: addonForm.name.trim(),
      price: Number(addonForm.price) || 0,
      is_available: addonForm.is_available,
    }
    if (editingAddonId.value !== null) {
      await backofficeApi.catalog.updateAddOn(editingAddonId.value, payload)
      toast.success('افزودنی ویرایش شد')
    } else {
      await backofficeApi.catalog.createAddOn(payload)
      toast.success('افزودنی جدید ثبت شد')
    }
    await Promise.all([closeAddonDialog(), loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'ذخیره افزودنی ناموفق بود')
  } finally {
    savingAddon.value = false
  }
}

async function toggleAddonKillSwitch(addon: AddOnAdmin) {
  try {
    await backofficeApi.catalog.updateAddOn(addon.id, { is_available: !addon.is_available })
    await Promise.all([loadAllCatalogData(), menuStore.fetchMenu(true)])
    toast.success(addon.is_available ? 'افزودنی موقتاً غیرفعال شد' : 'افزودنی دوباره فعال شد')
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'تغییر وضعیت ناموفق بود')
  }
}

async function deleteAddon(addon: AddOnAdmin) {
  try {
    await backofficeApi.catalog.deleteAddOn(addon.id)
    toast.success('افزودنی حذف شد')
    await Promise.all([loadAllCatalogData(), menuStore.fetchMenu(true)])
  } catch (err) {
    toast.error(err instanceof Error ? err.message : 'حذف افزودنی ناموفق بود')
  }
}

onMounted(() => {
  loadAllCatalogData()
})

useHead({
  title: 'مدیریت کاتالوگ و موجودی | پنل مدیریت فست‌فودی',
})
</script>

<template>
  <div>
    <BackofficeShell
      title="کاتالوگ، انبار و افزودنی‌ها"
      subtitle="مدیریت محصولات، تخفیف‌ها، موجودی انبار و کلید توقف سریع افزودنی‌ها"
      @reset="loadAllCatalogData"
    >
      <div class="space-y-6">
        <div role="tablist" aria-label="بخش‌های کاتالوگ" class="flex flex-wrap gap-2">
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'products'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold transition-colors"
            :class="
              activeTab === 'products'
                ? 'bg-[#183A2D] text-white'
                : 'border border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            @click="activeTab = 'products'"
          >
            محصولات ({{ toPersianDigits(products.length) }})
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'categories'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold transition-colors"
            :class="
              activeTab === 'categories'
                ? 'bg-[#183A2D] text-white'
                : 'border border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            @click="activeTab = 'categories'"
          >
            دسته‌بندی‌ها ({{ toPersianDigits(categories.length) }})
          </button>
          <button
            type="button"
            role="tab"
            :aria-selected="activeTab === 'addons'"
            class="touch-target rounded-full px-5 py-2.5 text-sm font-bold transition-colors"
            :class="
              activeTab === 'addons'
                ? 'bg-[#183A2D] text-white'
                : 'border border-[#E8E5DC] bg-white text-[#292B27] hover:bg-[#F4EFE3]'
            "
            @click="activeTab = 'addons'"
          >
            افزودنی‌ها ({{ toPersianDigits(addons.length) }})
          </button>
        </div>

        <section v-if="activeTab === 'products'" class="space-y-4">
          <div class="flex flex-wrap items-end justify-between gap-3 rounded-3xl border border-[#E8E5DC] bg-white p-4">
            <form class="flex flex-1 flex-wrap items-end gap-3" @submit.prevent="fetchProductsOnly">
              <div class="min-w-48 flex-1">
                <label for="cat-prod-search" class="mb-1 block text-xs font-semibold text-[#5A5D56]">جستجوی محصول</label>
                <div class="relative">
                  <input
                    id="cat-prod-search"
                    v-model="productFilters.search"
                    type="search"
                    placeholder="نام یا نامک"
                    class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] py-2 ps-3 pe-9 text-sm"
                  />
                  <Search class="pointer-events-none absolute top-2.5 end-3 h-4 w-4 text-[#5A5D56]" />
                </div>
              </div>
              <div>
                <label for="cat-prod-category" class="mb-1 block text-xs font-semibold text-[#5A5D56]">دسته‌بندی</label>
                <select
                  id="cat-prod-category"
                  v-model="productFilters.category_id"
                  class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-sm"
                  @change="fetchProductsOnly"
                >
                  <option value="">همه</option>
                  <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                    {{ cat.name }}
                  </option>
                </select>
              </div>
              <div>
                <label for="cat-prod-status" class="mb-1 block text-xs font-semibold text-[#5A5D56]">وضعیت</label>
                <select
                  id="cat-prod-status"
                  v-model="productFilters.status"
                  class="rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3 py-2 text-sm"
                  @change="fetchProductsOnly"
                >
                  <option value="">همه</option>
                  <option value="AVAILABLE">موجود</option>
                  <option value="OUT_OF_STOCK">ناموجود</option>
                  <option value="HIDDEN">مخفی</option>
                </select>
              </div>
              <button
                type="submit"
                class="touch-target rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-4 py-2 text-sm font-semibold hover:bg-[#F4EFE3]"
              >
                جستجو
              </button>
            </form>

            <button
              type="button"
              class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#183A2D] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#12251D]"
              @click="openCreateProduct"
            >
              <Plus class="h-4 w-4" />
              <span>محصول جدید</span>
            </button>
          </div>

          <div class="rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm">
            <div v-if="loading" class="h-40 animate-pulse rounded-2xl bg-[#F4EFE3]" />
            <div v-else class="table-wrapper">
              <table class="responsive-admin-table w-full border-collapse text-sm">
                <caption class="visually-hidden">فهرست محصولات کاتالوگ</caption>
                <thead>
                  <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                    <th scope="col" class="px-3 py-3 text-start">محصول</th>
                    <th scope="col" class="px-3 py-3 text-start">دسته</th>
                    <th scope="col" class="px-3 py-3 text-start">قیمت</th>
                    <th scope="col" class="px-3 py-3 text-start">موجودی</th>
                    <th scope="col" class="px-3 py-3 text-start">وضعیت</th>
                    <th scope="col" class="px-3 py-3 text-start">عملیات</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E8E5DC]">
                  <tr v-for="prod in products" :key="prod.id" class="hover:bg-[#FAF7F2]">
                    <td data-label="محصول" class="px-3 py-3">
                      <div class="flex items-center gap-3">
                        <img
                          v-if="prod.image_url"
                          :src="prod.image_url"
                          :alt="prod.name"
                          class="h-11 w-11 rounded-xl border border-[#E8E5DC] object-cover"
                        />
                        <div>
                          <p class="font-bold text-[#292B27]">{{ prod.name }}</p>
                          <p dir="ltr" class="text-xs text-[#72756E]">{{ prod.slug }}</p>
                        </div>
                      </div>
                    </td>
                    <td data-label="دسته" class="px-3 py-3 text-xs font-semibold">
                      {{ prod.category.name }}
                    </td>
                    <td data-label="قیمت" class="px-3 py-3">
                      <p class="font-bold text-[#183A2D]">{{ formatToman(prod.price) }}</p>
                      <p v-if="prod.compare_at_price" class="text-xs text-[#72756E] line-through">
                        {{ formatToman(prod.compare_at_price) }}
                      </p>
                    </td>
                    <td data-label="موجودی" class="px-3 py-3 text-xs font-semibold">
                      {{ prod.stock_quantity === null ? 'نامحدود' : toPersianDigits(prod.stock_quantity) }}
                    </td>
                    <td data-label="وضعیت" class="px-3 py-3">
                      <span
                        class="inline-block rounded-full px-2.5 py-1 text-xs font-bold"
                        :class="
                          prod.status === 'AVAILABLE'
                            ? 'bg-[#EDF7ED] text-[#1E5E22]'
                            : prod.status === 'OUT_OF_STOCK'
                              ? 'bg-[#FDE8E8] text-[#A61B1B]'
                              : 'bg-[#F4EFE3] text-[#5A5D56]'
                        "
                      >
                        {{ statusLabels[prod.status] }}
                      </span>
                    </td>
                    <td data-label="عملیات" class="px-3 py-3">
                      <div class="flex flex-wrap items-center gap-1.5">
                        <button
                          type="button"
                          class="touch-target inline-flex items-center gap-1 rounded-full border border-[#E8E5DC] bg-white px-3 py-1.5 text-xs font-semibold hover:bg-[#F4EFE3]"
                          @click="openEditProduct(prod)"
                        >
                          <Pencil class="h-3.5 w-3.5" />
                          <span>ویرایش</span>
                        </button>
                        <button
                          type="button"
                          class="touch-target inline-flex items-center gap-1 rounded-full bg-[#FDE8E8] px-3 py-1.5 text-xs font-semibold text-[#A61B1B] hover:bg-[#A61B1B] hover:text-white"
                          @click="deleteProduct(prod)"
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
        </section>

        <section v-else-if="activeTab === 'categories'" class="space-y-4">
          <div class="flex justify-end">
            <button
              type="button"
              class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#183A2D] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#12251D]"
              @click="openCreateCategory"
            >
              <Plus class="h-4 w-4" />
              <span>دسته‌بندی جدید</span>
            </button>
          </div>

          <div class="rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm">
            <div class="table-wrapper">
              <table class="responsive-admin-table w-full border-collapse text-sm">
                <caption class="visually-hidden">فهرست دسته‌بندی‌های منو</caption>
                <thead>
                  <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                    <th scope="col" class="px-3 py-3 text-start">ترتیب</th>
                    <th scope="col" class="px-3 py-3 text-start">عنوان</th>
                    <th scope="col" class="px-3 py-3 text-start">دسته والد</th>
                    <th scope="col" class="px-3 py-3 text-start">وضعیت</th>
                    <th scope="col" class="px-3 py-3 text-start">عملیات</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E8E5DC]">
                  <tr v-for="cat in categories" :key="cat.id" class="hover:bg-[#FAF7F2]">
                    <td data-label="ترتیب" class="px-3 py-3 font-bold">{{ toPersianDigits(cat.display_order) }}</td>
                    <td data-label="عنوان" class="px-3 py-3">
                      <p class="font-bold text-[#292B27]">{{ cat.name }}</p>
                      <p dir="ltr" class="text-xs text-[#72756E]">{{ cat.slug }}</p>
                    </td>
                    <td data-label="دسته والد" class="px-3 py-3 text-xs text-[#5A5D56]">
                      {{ cat.parent_id ? categoryMap.get(cat.parent_id)?.name || 'والد' : 'دسته اصلی' }}
                    </td>
                    <td data-label="وضعیت" class="px-3 py-3">
                      <button
                        type="button"
                        class="touch-target rounded-full px-3 py-1 text-xs font-bold"
                        :class="cat.is_active ? 'bg-[#EDF7ED] text-[#1E5E22]' : 'bg-[#FDE8E8] text-[#A61B1B]'"
                        @click="toggleCategoryActive(cat)"
                      >
                        {{ cat.is_active ? 'فعال' : 'غیرفعال' }}
                      </button>
                    </td>
                    <td data-label="عملیات" class="px-3 py-3">
                      <div class="flex flex-wrap gap-1.5">
                        <button
                          type="button"
                          class="touch-target rounded-full border border-[#E8E5DC] bg-white px-3 py-1.5 text-xs font-semibold hover:bg-[#F4EFE3]"
                          @click="openEditCategory(cat)"
                        >
                          ویرایش
                        </button>
                        <button
                          type="button"
                          class="touch-target rounded-full bg-[#FDE8E8] px-3 py-1.5 text-xs font-semibold text-[#A61B1B]"
                          @click="deleteCategory(cat)"
                        >
                          حذف
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>

        <section v-else class="space-y-4">
          <div class="flex justify-end">
            <button
              type="button"
              class="touch-target inline-flex items-center gap-1.5 rounded-full bg-[#183A2D] px-5 py-2.5 text-sm font-bold text-white hover:bg-[#12251D]"
              @click="openCreateAddon"
            >
              <Plus class="h-4 w-4" />
              <span>افزودنی جدید</span>
            </button>
          </div>

          <div class="rounded-3xl border border-[#E8E5DC] bg-white p-4 shadow-sm">
            <div class="table-wrapper">
              <table class="responsive-admin-table w-full border-collapse text-sm">
                <caption class="visually-hidden">فهرست افزودنی‌های غذا</caption>
                <thead>
                  <tr class="border-b border-[#E8E5DC] text-start text-xs font-bold text-[#5A5D56]">
                    <th scope="col" class="px-3 py-3 text-start">نام افزودنی</th>
                    <th scope="col" class="px-3 py-3 text-start">قیمت</th>
                    <th scope="col" class="px-3 py-3 text-start">توقف اضطراری (موجودی)</th>
                    <th scope="col" class="px-3 py-3 text-start">عملیات</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E8E5DC]">
                  <tr v-for="addon in addons" :key="addon.id" class="hover:bg-[#FAF7F2]">
                    <td data-label="نام" class="px-3 py-3 font-bold text-[#292B27]">{{ addon.name }}</td>
                    <td data-label="قیمت" class="px-3 py-3 font-bold text-[#183A2D]">{{ formatToman(addon.price) }}</td>
                    <td data-label="وضعیت" class="px-3 py-3">
                      <button
                        type="button"
                        class="touch-target rounded-full px-4 py-1.5 text-xs font-bold"
                        :class="addon.is_available ? 'bg-[#EDF7ED] text-[#1E5E22]' : 'bg-[#FDE8E8] text-[#A61B1B]'"
                        @click="toggleAddonKillSwitch(addon)"
                      >
                        {{ addon.is_available ? 'موجود (فعال)' : 'توقف موقت (ناموجود)' }}
                      </button>
                    </td>
                    <td data-label="عملیات" class="px-3 py-3">
                      <div class="flex flex-wrap gap-1.5">
                        <button
                          type="button"
                          class="touch-target rounded-full border border-[#E8E5DC] bg-white px-3 py-1.5 text-xs font-semibold hover:bg-[#F4EFE3]"
                          @click="openEditAddon(addon)"
                        >
                          ویرایش
                        </button>
                        <button
                          type="button"
                          class="touch-target rounded-full bg-[#FDE8E8] px-3 py-1.5 text-xs font-semibold text-[#A61B1B]"
                          @click="deleteAddon(addon)"
                        >
                          حذف
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </BackofficeShell>

    <dialog
      ref="productDialogRef"
      closedby="any"
      aria-labelledby="prod-dialog-title"
      class="modal-top-layer m-auto w-full max-w-2xl rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-xl"
    >
      <div class="max-h-[90vh] overflow-y-auto p-6 sm:p-8">
        <div class="mb-5 flex items-center justify-between gap-4 border-b border-[#E8E5DC] pb-4">
          <h2 id="prod-dialog-title" class="text-xl font-extrabold">
            {{ editingProductId !== null ? 'ویرایش محصول' : 'ایجاد محصول جدید' }}
          </h2>
          <button
            type="button"
            class="touch-target rounded-full px-3 py-1.5 text-sm font-semibold text-[#5A5D56]"
            @click="closeProductDialog"
          >
            بستن
          </button>
        </div>

        <form class="space-y-4 text-sm" @submit.prevent="saveProduct">
          <div class="grid gap-4 sm:grid-cols-2">
            <div>
              <label for="pf-name" class="mb-1 block font-semibold">نام محصول *</label>
              <input id="pf-name" v-model="productForm.name" type="text" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
            <div>
              <label for="pf-slug" class="mb-1 block font-semibold">نامک (Slug)</label>
              <input id="pf-slug" v-model="productForm.slug" type="text" dir="ltr" placeholder="auto-from-name" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
            <div>
              <label for="pf-cat" class="mb-1 block font-semibold">دسته‌بندی *</label>
              <select id="pf-cat" v-model.number="productForm.category_id" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5">
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>
            <div>
              <label for="pf-status" class="mb-1 block font-semibold">وضعیت فروش</label>
              <select id="pf-status" v-model="productForm.status" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5">
                <option value="AVAILABLE">موجود</option>
                <option value="OUT_OF_STOCK">ناموجود</option>
                <option value="HIDDEN">مخفی</option>
              </select>
            </div>
            <div>
              <label for="pf-price" class="mb-1 block font-semibold">قیمت فروش (تومان) *</label>
              <input id="pf-price" v-model.number="productForm.price" type="number" min="0" dir="ltr" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
            <div>
              <label for="pf-compare" class="mb-1 block font-semibold">قیمت قبل از تخفیف (اختیاری)</label>
              <input id="pf-compare" v-model="productForm.compare_at_price" type="number" min="0" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
            <div>
              <label for="pf-stock" class="mb-1 block font-semibold">موجودی انبار (خالی = نامحدود)</label>
              <input id="pf-stock" v-model="productForm.stock_quantity" type="number" min="0" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
            <div>
              <label for="pf-prep" class="mb-1 block font-semibold">زمان آماده‌سازی (دقیقه)</label>
              <input id="pf-prep" v-model.number="productForm.prep_time_minutes" type="number" min="0" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
            </div>
          </div>

          <div>
            <label for="pf-desc" class="mb-1 block font-semibold">توضیحات</label>
            <textarea id="pf-desc" v-model="productForm.description" rows="2" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>

          <div class="flex flex-wrap items-center gap-4">
            <label class="flex items-center gap-2 font-semibold">
              <input v-model="productForm.is_main_dish" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
              <span>جزو غذاهای اصلی است (پیش‌نیاز نوشیدنی/پیشنهادی)</span>
            </label>
            <div>
              <label for="pf-order" class="me-2 font-semibold">ترتیب نمایش:</label>
              <input id="pf-order" v-model.number="productForm.display_order" type="number" dir="ltr" class="w-20 rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-2.5 py-1 text-center" />
            </div>
          </div>

          <div class="rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2] p-4">
            <label for="pf-img" class="mb-2 flex items-center gap-2 font-bold">
              <ImagePlus class="h-4 w-4" />
              <span>تصویر محصول (حداکثر ۱۰ مگابایت)</span>
            </label>
            <input id="pf-img" type="file" accept="image/*" class="text-xs" @change="handleProductImageUpload" />
            <img
              v-if="uploadedProductImage || existingProductImageUrl"
              :src="uploadedProductImage || existingProductImageUrl || ''"
              alt="پیش‌نمایش تصویر محصول"
              class="mt-3 h-24 w-36 rounded-xl border border-[#E8E5DC] object-cover"
            />
          </div>

          <div v-if="addons.length > 0" class="rounded-2xl border border-[#E8E5DC] bg-[#FAF7F2] p-4">
            <p class="mb-3 font-bold">افزودنی‌های مجاز برای این محصول</p>
            <div class="space-y-2">
              <template v-for="addon in addons" :key="addon.id">
                <div
                  v-if="selectedAddonMap[addon.id]"
                  class="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#E8E5DC] bg-white px-3 py-2"
                >
                  <label class="flex items-center gap-2 font-semibold">
                    <input
                      v-model="selectedAddonMap[addon.id]!.enabled"
                      type="checkbox"
                      class="h-4 w-4 accent-[#183A2D]"
                    />
                    <span>{{ addon.name }} ({{ formatToman(addon.price) }})</span>
                  </label>
                  <div v-if="selectedAddonMap[addon.id]!.enabled" class="flex items-center gap-2 text-xs">
                    <label :for="`min-${addon.id}`">کمینه:</label>
                    <input
                      :id="`min-${addon.id}`"
                      v-model.number="selectedAddonMap[addon.id]!.min_quantity"
                      type="number"
                      min="0"
                      dir="ltr"
                      class="w-14 rounded-lg border border-[#E8E5DC] px-2 py-1 text-center"
                    />
                    <label :for="`max-${addon.id}`">بیشینه:</label>
                    <input
                      :id="`max-${addon.id}`"
                      v-model.number="selectedAddonMap[addon.id]!.max_quantity"
                      type="number"
                      min="1"
                      dir="ltr"
                      class="w-14 rounded-lg border border-[#E8E5DC] px-2 py-1 text-center"
                    />
                  </div>
                </div>
              </template>
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="touch-target rounded-full border border-[#E8E5DC] px-5 py-2.5 font-semibold" @click="closeProductDialog">
              انصراف
            </button>
            <button type="submit" :disabled="savingProduct" class="touch-target rounded-full bg-[#183A2D] px-7 py-2.5 font-bold text-white">
              {{ savingProduct ? 'در حال ذخیره...' : 'ذخیره محصول' }}
            </button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog
      ref="categoryDialogRef"
      closedby="any"
      aria-labelledby="cat-dialog-title"
      class="modal-top-layer m-auto w-full max-w-md rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-xl"
    >
      <div class="p-6 sm:p-7">
        <h2 id="cat-dialog-title" class="mb-4 text-xl font-extrabold">
          {{ editingCategoryId !== null ? 'ویرایش دسته‌بندی' : 'دسته‌بندی جدید' }}
        </h2>
        <form class="space-y-4 text-sm" @submit.prevent="saveCategory">
          <div>
            <label for="cf-name" class="mb-1 block font-semibold">نام دسته‌بندی *</label>
            <input id="cf-name" v-model="categoryForm.name" type="text" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>
          <div>
            <label for="cf-slug" class="mb-1 block font-semibold">نامک (Slug)</label>
            <input id="cf-slug" v-model="categoryForm.slug" type="text" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>
          <div>
            <label for="cf-parent" class="mb-1 block font-semibold">دسته والد (اختیاری)</label>
            <select id="cf-parent" v-model="categoryForm.parent_id" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5">
              <option value="">بدون والد (دسته اصلی)</option>
              <option v-for="c in availableParentCategories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label for="cf-order" class="mb-1 block font-semibold">ترتیب نمایش</label>
            <input id="cf-order" v-model.number="categoryForm.display_order" type="number" dir="ltr" class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>
          <label class="flex items-center gap-2 font-semibold">
            <input v-model="categoryForm.is_active" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
            <span>دسته‌بندی فعال است</span>
          </label>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="touch-target rounded-full border border-[#E8E5DC] px-5 py-2" @click="closeCategoryDialog">
              انصراف
            </button>
            <button type="submit" :disabled="savingCategory" class="touch-target rounded-full bg-[#183A2D] px-6 py-2 font-bold text-white">
              ذخیره
            </button>
          </div>
        </form>
      </div>
    </dialog>

    <dialog
      ref="addonDialogRef"
      closedby="any"
      aria-labelledby="addon-dialog-title"
      class="modal-top-layer m-auto w-full max-w-md rounded-3xl border border-[#E8E5DC] bg-white p-0 text-[#292B27] shadow-xl"
    >
      <div class="p-6 sm:p-7">
        <h2 id="addon-dialog-title" class="mb-4 text-xl font-extrabold">
          {{ editingAddonId !== null ? 'ویرایش افزودنی' : 'افزودنی جدید' }}
        </h2>
        <form class="space-y-4 text-sm" @submit.prevent="saveAddon">
          <div>
            <label for="af-name" class="mb-1 block font-semibold">نام افزودنی *</label>
            <input id="af-name" v-model="addonForm.name" type="text" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>
          <div>
            <label for="af-price" class="mb-1 block font-semibold">قیمت (تومان) *</label>
            <input id="af-price" v-model.number="addonForm.price" type="number" min="0" dir="ltr" required class="w-full rounded-xl border border-[#E8E5DC] bg-[#FAF7F2] px-3.5 py-2.5" />
          </div>
          <label class="flex items-center gap-2 font-semibold">
            <input v-model="addonForm.is_available" type="checkbox" class="h-4 w-4 accent-[#183A2D]" />
            <span>در دسترس و قابل سفارش</span>
          </label>
          <div class="flex justify-end gap-2 pt-2">
            <button type="button" class="touch-target rounded-full border border-[#E8E5DC] px-5 py-2" @click="closeAddonDialog">
              انصراف
            </button>
            <button type="submit" :disabled="savingAddon" class="touch-target rounded-full bg-[#183A2D] px-6 py-2 font-bold text-white">
              ذخیره
            </button>
          </div>
        </form>
      </div>
    </dialog>
  </div>
</template>

<style scoped>
@container (width < 42rem) {
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
