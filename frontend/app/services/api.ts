import type {
  AddOnAdmin,
  AddOnWritePayload,
  AddonLinkInput,
  CategoryAdmin,
  CategoryPublic,
  CategoryWritePayload,
  Customer360Detail,
  CustomerAddress,
  CustomerAddressPayload,
  CustomerListRow,
  CustomerNote,
  CustomerProfile,
  CustomerUpdatePayload,
  LiveOrderBackoffice,
  LuckyWheelProduct,
  LuckyWheelResponse,
  MediaAssetAdmin,
  MediaAssetKind,
  MediaAssetPublic,
  MenuCategoryPublic,
  MenuProductPublic,
  OTPRequestPayload,
  OTPRequestResponse,
  OTPVerifyPayload,
  OTPVerifyResponse,
  OrderBackofficeListParams,
  OrderCreatePayload,
  OrderDetailBackoffice,
  OrderItemAddOnSnapshot,
  OrderItemSnapshot,
  OrderListBackoffice,
  OrderRead,
  PaginatedResponse,
  PaymentBackoffice,
  PaymentPublic,
  PaymentStartResponse,
  ProductAdmin,
  ProductDetailAdmin,
  ProductDetailPublic,
  ProductSearchParams,
  ProductSuggestionPublic,
  ProductSuggestionsResponse,
  ProductSummaryPublic,
  ProductWritePayload,
  RecordRefundPayload,
  RestaurantSettings,
  RestaurantStatus,
  SiteSectionKey,
  SiteSectionsMap,
  StaffLoginPayload,
  StaffLoginResponse,
  StaffProfile,
  StorefrontMenuResponse,
  TokenRefreshResponse,
} from '~/types'
import {
  MockApiError,
  computeIsRestaurantOpen,
  delayMock,
  normalizeIranPhone,
  readMockAuthSession,
  readMockDb,
  writeMockAuthSession,
  writeMockDb,
} from './mockDatabase'
import { resolveProductAddons, type MockOrderRecord } from './mockSeed'
import {
  computeRelevanceScore,
  matchesSearchTerm,
  normalizeSearchQuery,
  suggestCorrectedTerm,
  tokenizeSearchQuery,
} from './searchEngine'

function toCategoryPublic(cat: CategoryAdmin): CategoryPublic {
  return {
    id: cat.id,
    name: cat.name,
    slug: cat.slug,
    description: cat.description,
    parent_id: cat.parent_id,
    image_url: cat.webp_image_url || cat.image_url,
  }
}

function toMenuProductPublic(p: ProductAdmin): MenuProductPublic {
  return {
    id: p.id,
    name: p.name,
    slug: p.slug,
    description: p.description,
    price: p.price,
    compare_at_price: p.compare_at_price,
    discount_percent: p.discount_percent,
    is_discounted: p.compare_at_price !== null && p.compare_at_price > p.price,
    stock_quantity: p.stock_quantity,
    is_in_stock: p.is_in_stock,
    status: p.status,
    is_main_dish: p.is_main_dish,
    prep_time_minutes: p.prep_time_minutes,
    image_url: p.webp_image_url || p.image_url,
  }
}

function toProductSummaryPublic(p: ProductAdmin): ProductSummaryPublic {
  return {
    ...toMenuProductPublic(p),
    category: toCategoryPublic(p.category),
  }
}

function toOrderRead(order: MockOrderRecord): OrderRead {
  return {
    id: order.id,
    daily_number: order.daily_number,
    status: order.status,
    payment_status: order.payment_status,
    delivery_type: order.delivery_type,
    delivery_address_snapshot: order.delivery_address_snapshot,
    delivery_recipient_name: order.delivery_recipient_name,
    delivery_recipient_phone: order.delivery_recipient_phone,
    subtotal: order.subtotal,
    delivery_fee: order.delivery_fee,
    total_amount: order.total_amount,
    prep_time_minutes: order.prep_time_minutes,
    expected_ready_at: order.expected_ready_at,
    paid_at: order.paid_at,
    notes_to_kitchen: order.notes_to_kitchen,
    expires_at: order.expires_at,
    canceled_at: order.canceled_at,
    cancellation_reason: order.cancellation_reason,
    refund_card_number: order.refund_card_number,
    refund_tracking_code: order.refund_tracking_code,
    refunded_at: order.refunded_at,
    created_at: order.created_at,
    items: order.items,
  }
}

function expireStalePendingOrders(): void {
  const db = readMockDb()
  const now = Date.now()
  let changed = false
  for (const order of db.orders) {
    if (
      order.status === 'PENDING_PAYMENT' &&
      order.expires_at &&
      new Date(order.expires_at).getTime() < now
    ) {
      order.status = 'CANCELED'
      order.canceled_at = new Date().toISOString()
      order.cancellation_reason = 'auto: payment timeout'
      changed = true
    }
  }
  if (changed) {
    writeMockDb(db)
  }
}

function requireAuthenticatedCustomer() {
  const auth = readMockAuthSession()
  if (!auth.customerId || !auth.accessToken) {
    throw new MockApiError(401, 'NOT_AUTHENTICATED', 'لطفاً ابتدا وارد حساب کاربری خود شوید.')
  }
  const db = readMockDb()
  const customer = db.customers.find(c => c.id === auth.customerId)
  if (!customer) {
    throw new MockApiError(401, 'NOT_AUTHENTICATED', 'حساب کاربری یافت نشد.')
  }
  if (customer.is_blocked) {
    throw new MockApiError(403, 'ACCOUNT_BLOCKED', 'حساب کاربری شما مسدود شده است.')
  }
  if (!customer.is_active) {
    throw new MockApiError(403, 'ACCOUNT_INACTIVE', 'حساب کاربری شما غیرفعال است.')
  }
  return { db, customer, auth }
}

function requireStaffSession() {
  const auth = readMockAuthSession()
  if (!auth.staffId || !auth.csrfToken) {
    throw new MockApiError(401, 'NOT_AUTHENTICATED', 'نشست مدیر معتبر نیست. لطفاً وارد شوید.')
  }
  const db = readMockDb()
  const staff = db.customers.find(c => c.id === auth.staffId)
  if (!staff || !staff.is_staff || !staff.is_active || staff.is_blocked) {
    throw new MockApiError(403, 'PERMISSION_DENIED', 'شما مجوز دسترسی به پنل مدیریت را ندارید.')
  }
  return { db, staff, auth }
}

function collectActiveSubtreeIds(categories: CategoryAdmin[], rootId: number): Set<number> {
  const activeByParent = new Map<number | null, number[]>()
  for (const cat of categories) {
    if (!cat.is_active) continue
    const list = activeByParent.get(cat.parent_id) ?? []
    list.push(cat.id)
    activeByParent.set(cat.parent_id, list)
  }
  const result = new Set<number>([rootId])
  const queue = [rootId]
  while (queue.length > 0) {
    const current = queue.shift()!
    for (const childId of activeByParent.get(current) ?? []) {
      if (!result.has(childId)) {
        result.add(childId)
        queue.push(childId)
      }
    }
  }
  return result
}

function buildPublicProductList(params: ProductSearchParams = {}): ProductAdmin[] {
  const db = readMockDb()
  const activeCategoryIds = new Set(db.categories.filter(c => c.is_active).map(c => c.id))

  let items = db.products.filter(
    p => p.status !== 'HIDDEN' && activeCategoryIds.has(p.category.id)
  )

  if (params.category || params.category_id) {
    const targetCat = db.categories.find(
      c =>
        c.is_active &&
        (params.category ? c.slug === params.category : true) &&
        (params.category_id !== undefined ? c.id === params.category_id : true)
    )
    if (!targetCat) {
      throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی مورد نظر یافت نشد.')
    }
    const includeSub = params.include_subcategories ?? true
    const allowedIds = includeSub
      ? collectActiveSubtreeIds(db.categories, targetCat.id)
      : new Set([targetCat.id])
    items = items.filter(p => allowedIds.has(p.category.id))
  }

  if (params.min_price !== undefined && params.max_price !== undefined && params.min_price > params.max_price) {
    throw new MockApiError(400, 'VALIDATION_ERROR', 'بازه قیمت نامعتبر است.', {
      max_price: 'بیشترین قیمت نباید کمتر از کمترین قیمت باشد.',
    })
  }

  if (params.min_price !== undefined) {
    items = items.filter(p => p.price >= params.min_price!)
  }
  if (params.max_price !== undefined) {
    items = items.filter(p => p.price <= params.max_price!)
  }
  if (params.available !== undefined) {
    items = items.filter(p =>
      params.available ? p.status === 'AVAILABLE' : p.status === 'OUT_OF_STOCK'
    )
  }
  if (params.in_stock !== undefined) {
    items = items.filter(p => p.is_in_stock === params.in_stock)
  }
  if (params.discount !== undefined) {
    items = items.filter(p => {
      const discounted = p.compare_at_price !== null && p.compare_at_price > p.price
      return params.discount ? discounted : !discounted
    })
  }
  if (params.is_main_dish !== undefined) {
    items = items.filter(p => p.is_main_dish === params.is_main_dish)
  }

  const normalizedQ = normalizeSearchQuery(params.q)
  if (normalizedQ) {
    items = items.filter(p =>
      matchesSearchTerm(
        {
          name: p.name,
          slug: p.slug,
          description: p.description,
          categoryName: p.category.name,
        },
        normalizedQ
      )
    )
  }

  const salesByProductName = new Map<string, number>()
  for (const order of db.orders) {
    if (
      order.payment_status === 'PAID' &&
      (order.status === 'PROCESSING' || order.status === 'READY' || order.status === 'COMPLETED')
    ) {
      for (const line of order.items) {
        salesByProductName.set(
          line.product_name_snapshot,
          (salesByProductName.get(line.product_name_snapshot) ?? 0) + line.quantity
        )
      }
    }
  }

  const effectiveSort =
    params.sort ?? (normalizedQ ? 'relevance' : 'default')

  items = [...items].sort((a, b) => {
    if (effectiveSort === 'relevance' && normalizedQ) {
      const scoreA = computeRelevanceScore(
        { name: a.name, slug: a.slug, description: a.description, categoryName: a.category.name },
        normalizedQ
      )
      const scoreB = computeRelevanceScore(
        { name: b.name, slug: b.slug, description: b.description, categoryName: b.category.name },
        normalizedQ
      )
      if (scoreB !== scoreA) return scoreB - scoreA
    } else if (effectiveSort === 'popularity') {
      const salesA = salesByProductName.get(a.name) ?? 0
      const salesB = salesByProductName.get(b.name) ?? 0
      if (salesB !== salesA) return salesB - salesA
    } else if (effectiveSort === 'price_asc') {
      if (a.price !== b.price) return a.price - b.price
    } else if (effectiveSort === 'price_desc') {
      if (b.price !== a.price) return b.price - a.price
    } else if (effectiveSort === 'newest') {
      return b.created_at.localeCompare(a.created_at) || b.id - a.id
    } else if (effectiveSort === 'oldest') {
      return a.created_at.localeCompare(b.created_at) || a.id - b.id
    }

    if (a.display_order !== b.display_order) return a.display_order - b.display_order
    const nameCmp = a.name.localeCompare(b.name, 'fa')
    if (nameCmp !== 0) return nameCmp
    return a.id - b.id
  })

  return items
}

function paginateSlice<T>(items: T[], limit = 20, offset = 0): PaginatedResponse<T> {
  const safeLimit = Math.max(1, limit)
  const safeOffset = Math.max(0, offset)
  const results = items.slice(safeOffset, safeOffset + safeLimit)
  const nextOffset = safeOffset + safeLimit < items.length ? safeOffset + safeLimit : null
  const prevOffset = safeOffset > 0 ? Math.max(0, safeOffset - safeLimit) : null
  return {
    count: items.length,
    next: nextOffset !== null ? `?limit=${safeLimit}&offset=${nextOffset}` : null,
    previous: prevOffset !== null ? `?limit=${safeLimit}&offset=${prevOffset}` : null,
    results,
  }
}

function assignDailyNumber(db: ReturnType<typeof readMockDb>, order: MockOrderRecord): void {
  const today = new Date().toISOString().slice(0, 10)
  const nextNumber = (db.dailyCounter[today] ?? 0) + 1
  db.dailyCounter[today] = nextNumber
  order.daily_number = nextNumber
  order.daily_number_date = today
}

function syncProductDerivedFields(product: ProductAdmin): ProductAdmin {
  const isDiscounted = product.compare_at_price !== null && product.compare_at_price > product.price
  product.discount_percent = isDiscounted
    ? Math.round(((product.compare_at_price! - product.price) * 100) / product.compare_at_price!)
    : 0
  product.is_in_stock =
    product.status === 'AVAILABLE' &&
    (product.stock_quantity === null || product.stock_quantity > 0)
  return product
}

export const storefrontApi = {
  auth: {
    async requestOtp(payload: OTPRequestPayload): Promise<OTPRequestResponse> {
      await delayMock(120)
      const normalized = normalizeIranPhone(payload.phone)
      const code = String(Math.floor(100000 + Math.random() * 900000))
      const auth = readMockAuthSession()
      auth.pendingOtps[normalized] = {
        code,
        expiresAt: Date.now() + 120_000,
      }
      writeMockAuthSession(auth)
      return {
        message: 'کد تایید ارسال شد.',
        expires_in: 120,
        dev_code: code,
      }
    },

    async verifyOtp(payload: OTPVerifyPayload): Promise<OTPVerifyResponse> {
      await delayMock(140)
      const normalized = normalizeIranPhone(payload.phone)
      const auth = readMockAuthSession()
      const record = auth.pendingOtps[normalized]
      if (!record || record.expiresAt < Date.now()) {
        throw new MockApiError(400, 'OTP_EXPIRED', 'کد تایید منقضی شده یا وجود ندارد.')
      }
      if (record.code !== (payload.code || '').trim()) {
        throw new MockApiError(400, 'OTP_INVALID', 'کد تایید وارد شده نادرست است.')
      }
      delete auth.pendingOtps[normalized]

      const db = readMockDb()
      let customer = db.customers.find(c => c.phone === normalized)
      if (!customer) {
        const nowIso = new Date().toISOString()
        customer = {
          id: db.nextIds.customer++,
          phone: normalized,
          full_name: '',
          is_blocked: false,
          is_active: true,
          is_staff: false,
          is_superuser: false,
          date_joined: nowIso,
          created_at: nowIso,
        }
        db.customers.push(customer)
        writeMockDb(db)
      }

      if (customer.is_blocked) {
        throw new MockApiError(403, 'ACCOUNT_BLOCKED', 'حساب کاربری شما مسدود شده است.')
      }
      if (!customer.is_active) {
        throw new MockApiError(403, 'ACCOUNT_INACTIVE', 'حساب کاربری شما غیرفعال است.')
      }

      const access = `mock.jwt.access.${customer.id}.${Date.now()}`
      const refresh = `mock.jwt.refresh.${customer.id}.${Date.now()}`
      auth.customerId = customer.id
      auth.accessToken = access
      auth.refreshToken = refresh
      writeMockAuthSession(auth)

      return {
        user: {
          id: customer.id,
          phone: customer.phone,
          full_name: customer.full_name,
          is_blocked: customer.is_blocked,
          date_joined: customer.date_joined,
          created_at: customer.created_at,
        },
        access,
        refresh,
      }
    },

    async refreshToken(refresh: string): Promise<TokenRefreshResponse> {
      await delayMock(80)
      const auth = readMockAuthSession()
      if (
        !refresh ||
        auth.blacklistedRefreshTokens.includes(refresh) ||
        auth.refreshToken !== refresh ||
        !auth.customerId
      ) {
        throw new MockApiError(401, 'TOKEN_INVALID', 'توکن نشست نامعتبر یا منقضی شده است.')
      }
      auth.blacklistedRefreshTokens.push(refresh)
      const nextAccess = `mock.jwt.access.${auth.customerId}.${Date.now()}`
      const nextRefresh = `mock.jwt.refresh.${auth.customerId}.${Date.now()}`
      auth.accessToken = nextAccess
      auth.refreshToken = nextRefresh
      writeMockAuthSession(auth)
      return { access: nextAccess, refresh: nextRefresh }
    },

    async logout(): Promise<void> {
      await delayMock(60)
      const auth = readMockAuthSession()
      if (auth.refreshToken) {
        auth.blacklistedRefreshTokens.push(auth.refreshToken)
      }
      auth.customerId = null
      auth.accessToken = null
      auth.refreshToken = null
      writeMockAuthSession(auth)
    },

    async me(): Promise<CustomerProfile> {
      await delayMock(60)
      const { customer } = requireAuthenticatedCustomer()
      return {
        id: customer.id,
        phone: customer.phone,
        full_name: customer.full_name,
        is_blocked: customer.is_blocked,
        date_joined: customer.date_joined,
        created_at: customer.created_at,
      }
    },

    async listAddresses(): Promise<CustomerAddress[]> {
      await delayMock(70)
      const { db, customer } = requireAuthenticatedCustomer()
      return db.addresses
        .filter(a => a.customer_id === customer.id)
        .sort((a, b) => Number(b.is_default) - Number(a.is_default) || b.id - a.id)
        .map(({ customer_id: _cid, ...rest }) => rest)
    },

    async createAddress(payload: CustomerAddressPayload): Promise<CustomerAddress> {
      await delayMock(90)
      const { db, customer } = requireAuthenticatedCustomer()
      const cleaned = (payload.address_text || '').trim()
      if (!cleaned) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'آدرس نمی‌تواند خالی باشد.', {
          address_text: 'آدرس نمی‌تواند خالی باشد.',
        })
      }
      const nowIso = new Date().toISOString()
      const makeDefault = Boolean(payload.is_default) || !db.addresses.some(a => a.customer_id === customer.id)
      if (makeDefault) {
        for (const row of db.addresses) {
          if (row.customer_id === customer.id && row.is_default) {
            row.is_default = false
            row.updated_at = nowIso
          }
        }
      }
      const created: CustomerAddress & { customer_id: number } = {
        id: db.nextIds.address++,
        customer_id: customer.id,
        title: (payload.title || '').trim(),
        address_text: cleaned,
        recipient_name: (payload.recipient_name || customer.full_name || '').trim(),
        recipient_phone: (payload.recipient_phone || customer.phone || '').trim(),
        is_out_of_zone: Boolean(payload.is_out_of_zone),
        is_default: makeDefault,
        created_at: nowIso,
        updated_at: nowIso,
      }
      db.addresses.push(created)
      writeMockDb(db)
      const { customer_id: _cid, ...address } = created
      return address
    },

    async updateAddress(id: number, payload: Partial<CustomerAddressPayload>): Promise<CustomerAddress> {
      await delayMock(90)
      const { db, customer } = requireAuthenticatedCustomer()
      const row = db.addresses.find(a => a.id === id && a.customer_id === customer.id)
      if (!row) {
        throw new MockApiError(404, 'ADDRESS_NOT_FOUND', 'آدرس یافت نشد.')
      }
      const nowIso = new Date().toISOString()
      if (payload.address_text !== undefined) {
        const cleaned = payload.address_text.trim()
        if (!cleaned) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'آدرس نمی‌تواند خالی باشد.', {
            address_text: 'آدرس نمی‌تواند خالی باشد.',
          })
        }
        row.address_text = cleaned
      }
      if (payload.title !== undefined) row.title = payload.title.trim()
      if (payload.recipient_name !== undefined) row.recipient_name = payload.recipient_name.trim()
      if (payload.recipient_phone !== undefined) row.recipient_phone = payload.recipient_phone.trim()
      if (payload.is_out_of_zone !== undefined) row.is_out_of_zone = payload.is_out_of_zone
      if (payload.is_default === true) {
        for (const other of db.addresses) {
          if (other.customer_id === customer.id && other.id !== row.id) {
            other.is_default = false
            other.updated_at = nowIso
          }
        }
        row.is_default = true
      } else if (payload.is_default === false) {
        row.is_default = false
      }
      row.updated_at = nowIso
      writeMockDb(db)
      const { customer_id: _cid, ...address } = row
      return address
    },

    async deleteAddress(id: number): Promise<void> {
      await delayMock(70)
      const { db, customer } = requireAuthenticatedCustomer()
      const idx = db.addresses.findIndex(a => a.id === id && a.customer_id === customer.id)
      if (idx === -1) {
        throw new MockApiError(404, 'ADDRESS_NOT_FOUND', 'آدرس یافت نشد.')
      }
      db.addresses.splice(idx, 1)
      writeMockDb(db)
    },
  },

  catalog: {
    async getMenu(): Promise<StorefrontMenuResponse> {
      await delayMock(70)
      const db = readMockDb()
      const activeCats = [...db.categories]
        .filter(c => c.is_active)
        .sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name, 'fa'))

      const categories: MenuCategoryPublic[] = activeCats.map(cat => {
        const catProducts = db.products
          .filter(p => p.category.id === cat.id && p.status !== 'HIDDEN')
          .sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name, 'fa'))
          .map(toMenuProductPublic)
        return {
          ...toCategoryPublic(cat),
          products: catProducts,
        }
      })
      return { categories }
    },

    async getProducts(params: ProductSearchParams = {}): Promise<PaginatedResponse<ProductSummaryPublic>> {
      await delayMock(80)
      const items = buildPublicProductList(params).map(toProductSummaryPublic)
      return paginateSlice(items, params.limit ?? 20, params.offset ?? 0)
    },

    async getSuggestions(q = '', limit = 5): Promise<ProductSuggestionsResponse> {
      await delayMock(70)
      const normalized = normalizeSearchQuery(q)
      if (!normalized) {
        return { results: [], did_you_mean: null }
      }
      const clampedLimit = Math.min(Math.max(1, limit), 10)
      const db = readMockDb()
      const activeCatIds = new Set(db.categories.filter(c => c.is_active).map(c => c.id))
      const publicProducts = db.products.filter(
        p => p.status !== 'HIDDEN' && activeCatIds.has(p.category.id)
      )

      let matches = buildPublicProductList({ q: normalized, sort: 'relevance' })
      let didYouMean: string | null = null

      if (matches.length === 0) {
        const vocab = Array.from(
          new Set(
            publicProducts.flatMap(p =>
              tokenizeSearchQuery(normalizeSearchQuery(p.name))
            )
          )
        )
        const corrected = suggestCorrectedTerm(normalized, vocab)
        if (corrected) {
          const correctedMatches = buildPublicProductList({ q: corrected, sort: 'relevance' })
          if (correctedMatches.length > 0) {
            matches = correctedMatches
            didYouMean = corrected
          }
        }
      }

      const results: ProductSuggestionPublic[] = matches.slice(0, clampedLimit).map(p => ({
        id: p.id,
        name: p.name,
        slug: p.slug,
        price: p.price,
        compare_at_price: p.compare_at_price,
        discount_percent: p.discount_percent,
        is_in_stock: p.is_in_stock,
        status: p.status,
        image_url: p.webp_image_url || p.image_url,
      }))

      return { results, did_you_mean: didYouMean }
    },

    async getProductBySlug(slug: string): Promise<ProductDetailPublic> {
      await delayMock(70)
      const db = readMockDb()
      const product = db.products.find(
        p => p.slug === slug && p.status !== 'HIDDEN' && p.category.is_active
      )
      if (!product) {
        throw new MockApiError(404, 'PRODUCT_NOT_FOUND', 'محصول مورد نظر یافت نشد.')
      }
      const addons = resolveProductAddons(product.id, db.productAddons, db.addons, false).map(
        ({ addon_id, name, price, min_quantity, max_quantity }) => ({
          addon_id,
          name,
          price,
          min_quantity,
          max_quantity,
        })
      )
      return {
        ...toProductSummaryPublic(product),
        addons,
      }
    },

    async getLuckyWheel(categorySlug?: string): Promise<LuckyWheelResponse> {
      await delayMock(70)
      const db = readMockDb()
      if (categorySlug) {
        const cat = db.categories.find(c => c.slug === categorySlug && c.is_active)
        if (!cat) {
          throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی مورد نظر یافت نشد.')
        }
      }
      const products: LuckyWheelProduct[] = db.products
        .filter(
          p =>
            p.status === 'AVAILABLE' &&
            p.is_main_dish &&
            p.category.is_active &&
            (!categorySlug || p.category.slug === categorySlug)
        )
        .map(p => ({
          id: p.id,
          name: p.name,
          slug: p.slug,
          price: p.price,
          category_id: p.category.id,
          image_url: p.webp_image_url || p.image_url,
        }))
      return { products }
    },
  },

  cms: {
    async getRestaurantStatus(): Promise<RestaurantStatus> {
      await delayMock(50)
      const db = readMockDb()
      const s = db.restaurantSettings
      return {
        is_open: computeIsRestaurantOpen(s.open_time, s.close_time, s.is_temporarily_closed),
        is_temporarily_closed: s.is_temporarily_closed,
        open_time: s.open_time,
        close_time: s.close_time,
        in_zone_delivery_fee: s.in_zone_delivery_fee,
        out_zone_delivery_fee: s.out_zone_delivery_fee,
        prep_time_buffer_minutes: s.prep_time_buffer_minutes,
      }
    },

    async getSiteSections(): Promise<SiteSectionsMap> {
      await delayMock(50)
      const db = readMockDb()
      return structuredClone(db.siteSections)
    },

    async getSiteSection<K extends SiteSectionKey>(
      key: K
    ): Promise<{ key: K; content: SiteSectionsMap[K] }> {
      await delayMock(50)
      const db = readMockDb()
      return {
        key,
        content: structuredClone(db.siteSections[key]),
      }
    },

    async getMediaAssets(kind?: MediaAssetKind): Promise<MediaAssetPublic[]> {
      await delayMock(50)
      const db = readMockDb()
      return db.mediaAssets
        .filter(m => !kind || m.kind === kind)
        .map(m => ({
          kind: m.kind,
          title: m.title,
          alt_text: m.alt_text,
          url: m.webp_file || m.file || null,
        }))
    },
  },

  orders: {
    async listOrders(limit = 20, offset = 0): Promise<PaginatedResponse<OrderRead>> {
      expireStalePendingOrders()
      await delayMock(90)
      const { db, customer } = requireAuthenticatedCustomer()
      const rows = db.orders
        .filter(o => o.customer_id === customer.id)
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .map(toOrderRead)
      return paginateSlice(rows, limit, offset)
    },

    async getOrder(orderId: number): Promise<OrderRead> {
      expireStalePendingOrders()
      await delayMock(70)
      const { db, customer } = requireAuthenticatedCustomer()
      const order = db.orders.find(o => o.id === orderId && o.customer_id === customer.id)
      if (!order) {
        throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش مورد نظر یافت نشد.')
      }
      return toOrderRead(order)
    },

    async createOrder(payload: OrderCreatePayload): Promise<OrderRead> {
      expireStalePendingOrders()
      await delayMock(140)
      const { db, customer } = requireAuthenticatedCustomer()
      const settings = db.restaurantSettings
      const isOpen = computeIsRestaurantOpen(
        settings.open_time,
        settings.close_time,
        settings.is_temporarily_closed
      )
      if (!isOpen) {
        throw new MockApiError(409, 'RESTAURANT_CLOSED', 'رستوران در حال حاضر خارج از ساعت کاری یا موقتاً بسته است.')
      }

      if (payload.delivery_type !== 'PICKUP' && payload.delivery_type !== 'DELIVERY') {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'نوع تحویل نامعتبر است.', {
          delivery_type: 'نوع تحویل نامعتبر است.',
        })
      }

      if (!payload.items || payload.items.length === 0) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'سبد خرید خالی است.', {
          items: 'حداقل یک آیتم لازم است.',
        })
      }

      let resolvedAddress: (CustomerAddress & { customer_id: number }) | null = null
      if (payload.delivery_type === 'DELIVERY') {
        if (!payload.address_id) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'برای ارسال، انتخاب آدرس الزامی است.', {
            address_id: 'این فیلد برای سفارش ارسالی الزامی است.',
          })
        }
        resolvedAddress =
          db.addresses.find(a => a.id === payload.address_id && a.customer_id === customer.id) ?? null
        if (!resolvedAddress) {
          throw new MockApiError(404, 'ADDRESS_NOT_FOUND', 'آدرس یافت نشد.')
        }
      }

      const deliveryFee =
        payload.delivery_type === 'DELIVERY' && resolvedAddress
          ? resolvedAddress.is_out_of_zone
            ? settings.out_zone_delivery_fee
            : settings.in_zone_delivery_fee
          : 0

      let maxPrep = 0
      let subtotal = 0
      const builtItems: OrderItemSnapshot[] = []

      for (const rawItem of payload.items) {
        const product = db.products.find(p => p.id === rawItem.product_id)
        if (!product || product.status === 'HIDDEN') {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'محصول انتخاب‌شده در دسترس نیست.', {
            product_id: rawItem.product_id,
          })
        }
        if (product.status !== 'AVAILABLE' || !product.is_in_stock) {
          throw new MockApiError(
            422,
            'VALIDATION_ERROR',
            `محصول «${product.name}» در حال حاضر موجود نیست.`,
            { product_id: product.id, status: product.status }
          )
        }
        if (!product.category.is_active) {
          throw new MockApiError(
            422,
            'VALIDATION_ERROR',
            `دسته‌بندی محصول «${product.name}» غیرفعال است.`,
            { product_id: product.id }
          )
        }
        if (rawItem.quantity <= 0) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'تعداد محصول باید بزرگ‌تر از صفر باشد.')
        }

        maxPrep = Math.max(maxPrep, product.prep_time_minutes)
        const productLinks = resolveProductAddons(product.id, db.productAddons, db.addons, true)
        const linkMap = new Map(productLinks.map(l => [l.addon_id, l]))

        let addonsTotal = 0
        const builtAddons: OrderItemAddOnSnapshot[] = []

        for (const rawAddon of rawItem.addons ?? []) {
          const link = linkMap.get(rawAddon.addon_id)
          if (!link) {
            throw new MockApiError(
              422,
              'VALIDATION_ERROR',
              `افزودنی برای محصول «${product.name}» تعریف نشده است.`
            )
          }
          if (!link.is_available) {
            throw new MockApiError(
              422,
              'VALIDATION_ERROR',
              `افزودنی «${link.name}» در حال حاضر موجود نیست.`
            )
          }
          if (rawAddon.quantity < 0 || rawAddon.quantity > link.max_quantity) {
            throw new MockApiError(
              422,
              'VALIDATION_ERROR',
              `تعداد افزودنی «${link.name}» نامعتبر است.`
            )
          }
          if (rawAddon.quantity === 0) continue

          const addonLine = rawAddon.quantity * link.price
          addonsTotal += addonLine
          builtAddons.push({
            addon_id: link.addon_id,
            addon_name_snapshot: link.name,
            unit_price_snapshot: link.price,
            quantity: rawAddon.quantity,
            line_total: addonLine,
          })
        }

        const lineTotal = product.price * rawItem.quantity + addonsTotal
        subtotal += lineTotal
        builtItems.push({
          id: db.nextIds.orderItem++,
          product_name_snapshot: product.name,
          unit_price_snapshot: product.price,
          quantity: rawItem.quantity,
          addons_total: addonsTotal,
          line_total: lineTotal,
          addons: builtAddons,
        })
      }

      const now = new Date()
      const expiresAt = new Date(now.getTime() + 15 * 60_000).toISOString()
      const prepTimeMinutes = maxPrep + settings.prep_time_buffer_minutes

      const createdOrder: MockOrderRecord = {
        id: db.nextIds.order++,
        customer_id: customer.id,
        daily_number: null,
        daily_number_date: null,
        status: 'PENDING_PAYMENT',
        payment_status: 'UNPAID',
        delivery_type: payload.delivery_type,
        delivery_address_snapshot: resolvedAddress ? resolvedAddress.address_text : '',
        delivery_recipient_name: resolvedAddress
          ? resolvedAddress.recipient_name || customer.full_name
          : customer.full_name,
        delivery_recipient_phone: resolvedAddress
          ? resolvedAddress.recipient_phone || customer.phone
          : customer.phone,
        customer: {
          id: customer.id,
          phone: customer.phone,
          full_name: customer.full_name,
        },
        subtotal,
        delivery_fee: deliveryFee,
        total_amount: subtotal + deliveryFee,
        prep_time_minutes: prepTimeMinutes,
        expected_ready_at: null,
        paid_at: null,
        is_printed: false,
        printed_at: null,
        notes_to_kitchen: (payload.notes_to_kitchen || '').trim(),
        expires_at: expiresAt,
        canceled_at: null,
        canceled_by_id: null,
        cancellation_reason: '',
        refund_card_number: '',
        refund_tracking_code: '',
        refunded_at: null,
        created_at: now.toISOString(),
        items: builtItems,
      }

      db.orders.unshift(createdOrder)
      writeMockDb(db)
      return toOrderRead(createdOrder)
    },
  },

  payments: {
    async requestPayment(orderId: number): Promise<PaymentStartResponse> {
      expireStalePendingOrders()
      await delayMock(120)
      const { db, customer } = requireAuthenticatedCustomer()
      const order = db.orders.find(o => o.id === orderId && o.customer_id === customer.id)
      if (!order) {
        throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      }
      if (order.status !== 'PENDING_PAYMENT' || order.payment_status !== 'UNPAID') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'این سفارش در وضعیت قابل پرداخت نیست.')
      }
      if (order.expires_at && new Date(order.expires_at).getTime() < Date.now()) {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'مهلت ۱۵ دقیقه‌ای پرداخت این سفارش به پایان رسیده است.')
      }

      const isOpen = computeIsRestaurantOpen(
        db.restaurantSettings.open_time,
        db.restaurantSettings.close_time,
        db.restaurantSettings.is_temporarily_closed
      )
      if (!isOpen) {
        throw new MockApiError(409, 'RESTAURANT_CLOSED', 'رستوران در حال حاضر بسته است.')
      }

      const authority = `MOCK-ZP-${order.id}-${Date.now().toString(36).toUpperCase()}`
      db.payments.push({
        id: db.nextIds.payment++,
        order_id: order.id,
        customer_phone: customer.phone,
        amount: order.total_amount,
        status: 'PENDING',
        authority,
        ref_id: '',
        gateway_response_code: '',
        verified_at: null,
        failed_at: null,
        created_at: new Date().toISOString(),
      })
      writeMockDb(db)

      return {
        payment_url: `/payment/gateway?authority=${encodeURIComponent(authority)}&order_id=${order.id}`,
        authority,
        amount: order.total_amount,
      }
    },

    async retryPayment(orderId: number): Promise<PaymentStartResponse> {
      return storefrontApi.payments.requestPayment(orderId)
    },

    async verifyMockCallback(authority: string, status: 'OK' | 'NOK'): Promise<{
      status: 'success' | 'failed'
      authority: string
      orderId: number
    }> {
      expireStalePendingOrders()
      await delayMock(180)
      const db = readMockDb()
      const payment = db.payments.find(p => p.authority === authority)
      if (!payment) {
        throw new MockApiError(404, 'PAYMENT_NOT_FOUND', 'تراکنش یافت نشد.')
      }
      if (payment.status === 'SUCCEEDED') {
        return { status: 'success', authority: payment.authority, orderId: payment.order_id }
      }
      if (payment.status === 'FAILED' || payment.status === 'CANCELED') {
        return { status: 'failed', authority: payment.authority, orderId: payment.order_id }
      }

      const order = db.orders.find(o => o.id === payment.order_id)
      if (!order || order.status !== 'PENDING_PAYMENT') {
        payment.status = 'FAILED'
        payment.failed_at = new Date().toISOString()
        payment.gateway_response_code = '409'
        writeMockDb(db)
        return { status: 'failed', authority: payment.authority, orderId: payment.order_id }
      }

      if (status !== 'OK') {
        payment.status = 'FAILED'
        payment.failed_at = new Date().toISOString()
        payment.gateway_response_code = '-11'
        writeMockDb(db)
        return { status: 'failed', authority: payment.authority, orderId: payment.order_id }
      }

      const now = new Date()
      payment.status = 'SUCCEEDED'
      payment.ref_id = String(Math.floor(700000000 + Math.random() * 299999999))
      payment.gateway_response_code = '100'
      payment.verified_at = now.toISOString()

      order.paid_at = now.toISOString()
      order.status = 'PROCESSING'
      order.payment_status = 'PAID'
      order.expected_ready_at = new Date(
        now.getTime() + order.prep_time_minutes * 60_000
      ).toISOString()
      order.is_printed = false
      assignDailyNumber(db, order)

      writeMockDb(db)
      return { status: 'success', authority: payment.authority, orderId: payment.order_id }
    },

    async getPaymentStatus(authority: string): Promise<{ payment: PaymentPublic; order_id: number }> {
      await delayMock(70)
      const { db, customer } = requireAuthenticatedCustomer()
      const payment = db.payments.find(p => p.authority === authority)
      if (!payment) {
        throw new MockApiError(404, 'PAYMENT_NOT_FOUND', 'تراکنش مورد نظر یافت نشد.')
      }
      const order = db.orders.find(o => o.id === payment.order_id)
      if (!order || order.customer_id !== customer.id) {
        throw new MockApiError(403, 'PERMISSION_DENIED', 'این تراکنش متعلق به شما نیست.')
      }
      return {
        order_id: order.id,
        payment: {
          id: payment.id,
          amount: payment.amount,
          status: payment.status,
          ref_id: payment.ref_id,
          verified_at: payment.verified_at,
          created_at: payment.created_at,
        },
      }
    },
  },
}

export const backofficeApi = {
  auth: {
    async login(payload: StaffLoginPayload): Promise<StaffLoginResponse> {
      await delayMock(140)
      let normalized: string
      try {
        normalized = normalizeIranPhone(payload.phone)
      } catch {
        throw new MockApiError(401, 'INVALID_CREDENTIALS', 'شماره موبایل یا رمز عبور نادرست است.')
      }
      const db = readMockDb()
      const user = db.customers.find(c => c.phone === normalized)
      if (!user) {
        throw new MockApiError(401, 'INVALID_CREDENTIALS', 'شماره موبایل یا رمز عبور نادرست است.')
      }
      if (user.is_blocked) {
        throw new MockApiError(403, 'ACCOUNT_BLOCKED', 'حساب کاربری مسدود شده است.')
      }
      if (!user.is_active) {
        throw new MockApiError(403, 'ACCOUNT_INACTIVE', 'حساب کاربری غیرفعال است.')
      }
      if (!user.is_staff) {
        throw new MockApiError(403, 'NOT_STAFF', 'این حساب دسترسی پنل مدیریت ندارد.')
      }
      if (user.password !== payload.password) {
        throw new MockApiError(401, 'INVALID_CREDENTIALS', 'شماره موبایل یا رمز عبور نادرست است.')
      }

      const csrfToken = `mock-csrf-${Date.now()}`
      const auth = readMockAuthSession()
      auth.staffId = user.id
      auth.csrfToken = csrfToken
      writeMockAuthSession(auth)

      return {
        user: {
          id: user.id,
          phone: user.phone,
          full_name: user.full_name,
          is_staff: user.is_staff,
          is_superuser: user.is_superuser,
          date_joined: user.date_joined,
        },
        csrf_token: csrfToken,
      }
    },

    async logout(): Promise<void> {
      await delayMock(60)
      const auth = readMockAuthSession()
      auth.staffId = null
      auth.csrfToken = null
      writeMockAuthSession(auth)
    },

    async me(): Promise<StaffProfile> {
      await delayMock(50)
      const { staff } = requireStaffSession()
      return {
        id: staff.id,
        phone: staff.phone,
        full_name: staff.full_name,
        is_staff: staff.is_staff,
        is_superuser: staff.is_superuser,
        date_joined: staff.date_joined,
      }
    },
  },

  orders: {
    async getLiveOrders(): Promise<LiveOrderBackoffice[]> {
      expireStalePendingOrders()
      await delayMock(80)
      const { db } = requireStaffSession()
      return db.orders
        .filter(o => o.status === 'PROCESSING' || o.status === 'READY')
        .sort((a, b) =>
          (a.expected_ready_at || a.created_at).localeCompare(b.expected_ready_at || b.created_at)
        )
        .map(o => ({
          id: o.id,
          daily_number: o.daily_number,
          status: o.status,
          delivery_type: o.delivery_type,
          customer_phone: o.customer.phone,
          delivery_address_snapshot: o.delivery_address_snapshot,
          total_amount: o.total_amount,
          prep_time_minutes: o.prep_time_minutes,
          expected_ready_at: o.expected_ready_at,
          paid_at: o.paid_at,
          is_printed: o.is_printed,
          printed_at: o.printed_at,
          notes_to_kitchen: o.notes_to_kitchen,
          created_at: o.created_at,
          items: o.items,
        }))
    },

    async listOrders(params: OrderBackofficeListParams = {}): Promise<PaginatedResponse<OrderListBackoffice>> {
      expireStalePendingOrders()
      await delayMock(80)
      const { db } = requireStaffSession()
      let rows = [...db.orders]
      if (params.status) {
        rows = rows.filter(o => o.status === params.status)
      }
      if (params.payment_status) {
        rows = rows.filter(o => o.payment_status === params.payment_status)
      }
      if (params.delivery_type) {
        rows = rows.filter(o => o.delivery_type === params.delivery_type)
      }
      if (params.search?.trim()) {
        const q = params.search.trim().toLowerCase()
        rows = rows.filter(
          o =>
            String(o.id).includes(q) ||
            String(o.daily_number ?? '').includes(q) ||
            o.customer.phone.includes(q) ||
            o.customer.full_name.toLowerCase().includes(q)
        )
      }
      if (params.date_from) {
        rows = rows.filter(o => o.created_at.slice(0, 10) >= params.date_from!)
      }
      if (params.date_to) {
        rows = rows.filter(o => o.created_at.slice(0, 10) <= params.date_to!)
      }
      rows.sort((a, b) => b.created_at.localeCompare(a.created_at))

      const mapped: OrderListBackoffice[] = rows.map(o => ({
        id: o.id,
        daily_number: o.daily_number,
        status: o.status,
        payment_status: o.payment_status,
        delivery_type: o.delivery_type,
        customer_phone: o.customer.phone,
        customer_full_name: o.customer.full_name,
        total_amount: o.total_amount,
        prep_time_minutes: o.prep_time_minutes,
        expected_ready_at: o.expected_ready_at,
        is_printed: o.is_printed,
        created_at: o.created_at,
        paid_at: o.paid_at,
      }))

      return paginateSlice(mapped, params.limit ?? 20, params.offset ?? 0)
    },

    async getOrder(orderId: number): Promise<OrderDetailBackoffice> {
      expireStalePendingOrders()
      await delayMock(70)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) {
        throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      }
      return structuredClone(order)
    },

    async markPrinted(orderId: number): Promise<OrderDetailBackoffice> {
      await delayMock(70)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (!order.is_printed) {
        order.is_printed = true
        order.printed_at = new Date().toISOString()
        writeMockDb(db)
      }
      return structuredClone(order)
    },

    async markReady(orderId: number): Promise<OrderDetailBackoffice> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (order.status !== 'PROCESSING') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'فقط سفارش در حال آماده‌سازی می‌تواند آماده شود.')
      }
      order.status = 'READY'
      writeMockDb(db)
      return structuredClone(order)
    },

    async markCompleted(orderId: number): Promise<OrderDetailBackoffice> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (order.status !== 'READY') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'فقط سفارش آماده تحویل می‌تواند تکمیل شود.')
      }
      order.status = 'COMPLETED'
      writeMockDb(db)
      return structuredClone(order)
    },

    async updatePrepTime(orderId: number, prepTimeMinutes: number): Promise<OrderDetailBackoffice> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (order.status !== 'PROCESSING' && order.status !== 'READY') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'زمان آماده‌سازی فقط برای سفارش فعال قابل تغییر است.')
      }
      if (prepTimeMinutes < 1) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'زمان آماده‌سازی باید حداقل ۱ دقیقه باشد.')
      }
      order.prep_time_minutes = prepTimeMinutes
      const anchor = order.paid_at ? new Date(order.paid_at) : new Date(order.created_at)
      order.expected_ready_at = new Date(anchor.getTime() + prepTimeMinutes * 60_000).toISOString()
      writeMockDb(db)
      return structuredClone(order)
    },

    async cancelOrder(orderId: number, reason = ''): Promise<OrderDetailBackoffice> {
      await delayMock(90)
      const { db, staff } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (order.status === 'COMPLETED' || order.status === 'CANCELED') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'سفارش تکمیل‌شده یا لغوشده قابل لغو مجدد نیست.')
      }
      order.status = 'CANCELED'
      order.canceled_at = new Date().toISOString()
      order.canceled_by_id = staff.id
      order.cancellation_reason = reason.trim()
      if (order.payment_status === 'PAID') {
        order.payment_status = 'AWAITING_REFUND'
      }
      writeMockDb(db)
      return structuredClone(order)
    },

    async recordRefund(orderId: number, payload: RecordRefundPayload): Promise<OrderDetailBackoffice> {
      await delayMock(100)
      const { db } = requireStaffSession()
      const order = db.orders.find(o => o.id === orderId)
      if (!order) throw new MockApiError(404, 'ORDER_NOT_FOUND', 'سفارش یافت نشد.')
      if (order.payment_status !== 'AWAITING_REFUND') {
        throw new MockApiError(409, 'INVALID_ORDER_STATE', 'این سفارش در انتظار عودت وجه نیست.')
      }
      if (!payload.card_number.trim() || !payload.tracking_code.trim()) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'شماره کارت و کد پیگیری الزامی هستند.')
      }
      order.payment_status = 'REFUNDED'
      order.refund_card_number = payload.card_number.trim()
      order.refund_tracking_code = payload.tracking_code.trim()
      order.refunded_at = new Date().toISOString()
      writeMockDb(db)
      return structuredClone(order)
    },
  },

  payments: {
    async listOrderPayments(orderId: number): Promise<PaymentBackoffice[]> {
      await delayMock(60)
      const { db } = requireStaffSession()
      return db.payments
        .filter(p => p.order_id === orderId)
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
    },
  },

  crm: {
    async listCustomers(params: { search?: string; is_blocked?: boolean; limit?: number; offset?: number } = {}): Promise<PaginatedResponse<CustomerListRow>> {
      await delayMock(70)
      const { db } = requireStaffSession()
      let rows = db.customers.filter(c => !c.is_staff)
      if (params.is_blocked !== undefined) {
        rows = rows.filter(c => c.is_blocked === params.is_blocked)
      }
      if (params.search?.trim()) {
        const q = params.search.trim().toLowerCase()
        rows = rows.filter(
          c => c.phone.includes(q) || c.full_name.toLowerCase().includes(q)
        )
      }
      const mapped: CustomerListRow[] = rows.map(c => ({
        id: c.id,
        phone: c.phone,
        full_name: c.full_name,
        is_blocked: c.is_blocked,
        is_active: c.is_active,
        date_joined: c.date_joined,
        created_at: c.created_at,
      }))
      return paginateSlice(mapped, params.limit ?? 20, params.offset ?? 0)
    },

    async getCustomer360(customerId: number): Promise<Customer360Detail> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const c = db.customers.find(row => row.id === customerId)
      if (!c) throw new MockApiError(404, 'CUSTOMER_NOT_FOUND', 'مشتری یافت نشد.')
      const addresses = db.addresses
        .filter(a => a.customer_id === c.id)
        .map(({ customer_id: _cid, ...rest }) => rest)
      const notes = db.customerNotes
        .filter(n => n.customer_id === c.id)
        .sort((a, b) => b.created_at.localeCompare(a.created_at))
        .map(({ customer_id: _cid, ...rest }) => rest)
      const custOrders = db.orders.filter(o => o.customer_id === c.id)
      const completed = custOrders.filter(o => o.status === 'COMPLETED')
      const ltv = custOrders
        .filter(o => o.payment_status === 'PAID')
        .reduce((sum, o) => sum + o.total_amount, 0)
      const lastOrderAt =
        custOrders.length > 0
          ? custOrders.map(o => o.created_at).sort().reverse()[0] ?? null
          : null

      return {
        id: c.id,
        phone: c.phone,
        full_name: c.full_name,
        is_blocked: c.is_blocked,
        is_active: c.is_active,
        date_joined: c.date_joined,
        created_at: c.created_at,
        addresses,
        notes,
        orders_count: custOrders.length,
        completed_orders_count: completed.length,
        lifetime_value: ltv,
        last_order_at: lastOrderAt,
      }
    },

    async updateCustomer(customerId: number, payload: CustomerUpdatePayload): Promise<CustomerListRow> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const c = db.customers.find(row => row.id === customerId)
      if (!c) throw new MockApiError(404, 'CUSTOMER_NOT_FOUND', 'مشتری یافت نشد.')
      if (payload.full_name !== undefined) c.full_name = payload.full_name.trim()
      if (payload.is_blocked !== undefined) c.is_blocked = payload.is_blocked
      if (payload.is_active !== undefined) c.is_active = payload.is_active
      writeMockDb(db)
      return {
        id: c.id,
        phone: c.phone,
        full_name: c.full_name,
        is_blocked: c.is_blocked,
        is_active: c.is_active,
        date_joined: c.date_joined,
        created_at: c.created_at,
      }
    },

    async createCustomerNote(customerId: number, text: string): Promise<CustomerNote> {
      await delayMock(70)
      const { db, staff } = requireStaffSession()
      const c = db.customers.find(row => row.id === customerId)
      if (!c) throw new MockApiError(404, 'CUSTOMER_NOT_FOUND', 'مشتری یافت نشد.')
      const cleaned = text.trim()
      if (!cleaned) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'متن یادداشت خالی است.')
      }
      const note = {
        id: db.nextIds.note++,
        customer_id: c.id,
        text: cleaned,
        author_phone: staff.phone,
        created_at: new Date().toISOString(),
      }
      db.customerNotes.unshift(note)
      writeMockDb(db)
      const { customer_id: _cid, ...publicNote } = note
      return publicNote
    },

    async deleteCustomerNote(customerId: number, noteId: number): Promise<void> {
      await delayMock(60)
      const { db } = requireStaffSession()
      const idx = db.customerNotes.findIndex(n => n.id === noteId && n.customer_id === customerId)
      if (idx === -1) throw new MockApiError(404, 'NOTE_NOT_FOUND', 'یادداشت یافت نشد.')
      db.customerNotes.splice(idx, 1)
      writeMockDb(db)
    },
  },

  catalog: {
    async listCategories(isActive?: boolean): Promise<PaginatedResponse<CategoryAdmin>> {
      await delayMock(60)
      const { db } = requireStaffSession()
      let rows = [...db.categories]
      if (isActive !== undefined) rows = rows.filter(c => c.is_active === isActive)
      rows.sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name, 'fa'))
      return paginateSlice(rows, 100, 0)
    },

    async createCategory(payload: CategoryWritePayload): Promise<CategoryAdmin> {
      await delayMock(90)
      const { db } = requireStaffSession()
      if (db.categories.some(c => c.slug === payload.slug)) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'این نامک (slug) قبلاً ثبت شده است.')
      }
      const nowIso = new Date().toISOString()
      const created: CategoryAdmin = {
        id: db.nextIds.category++,
        parent_id: payload.parent_id ?? null,
        name: payload.name.trim(),
        slug: payload.slug.trim(),
        description: (payload.description || '').trim(),
        image_url: '/svg/food.svg',
        webp_image_url: null,
        display_order: payload.display_order ?? 0,
        is_active: payload.is_active ?? true,
        created_at: nowIso,
        updated_at: nowIso,
      }
      db.categories.push(created)
      writeMockDb(db)
      return structuredClone(created)
    },

    async updateCategory(id: number, payload: Partial<CategoryWritePayload>): Promise<CategoryAdmin> {
      await delayMock(90)
      const { db } = requireStaffSession()
      const cat = db.categories.find(c => c.id === id)
      if (!cat) throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی یافت نشد.')
      if (payload.parent_id !== undefined && payload.parent_id !== null) {
        if (payload.parent_id === id) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'دسته‌بندی نمی‌تواند والد خودش باشد.')
        }
        let cursor: number | null = payload.parent_id
        while (cursor !== null) {
          if (cursor === id) {
            throw new MockApiError(422, 'VALIDATION_ERROR', 'ساختار سلسله‌مراتبی حلقوی مجاز نیست.')
          }
          const parent = db.categories.find(c => c.id === cursor)
          cursor = parent ? parent.parent_id : null
        }
      }
      if (payload.name !== undefined) cat.name = payload.name.trim()
      if (payload.slug !== undefined) {
        if (db.categories.some(c => c.slug === payload.slug && c.id !== id)) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'این نامک (slug) تکراری است.')
        }
        cat.slug = payload.slug.trim()
      }
      if (payload.parent_id !== undefined) cat.parent_id = payload.parent_id
      if (payload.description !== undefined) cat.description = payload.description.trim()
      if (payload.display_order !== undefined) cat.display_order = payload.display_order
      if (payload.is_active !== undefined) cat.is_active = payload.is_active
      cat.updated_at = new Date().toISOString()

      for (const p of db.products) {
        if (p.category.id === cat.id) {
          p.category = structuredClone(cat)
        }
      }
      writeMockDb(db)
      return structuredClone(cat)
    },

    async deleteCategory(id: number): Promise<void> {
      await delayMock(70)
      const { db } = requireStaffSession()
      if (db.products.some(p => p.category.id === id)) {
        throw new MockApiError(409, 'CATEGORY_HAS_PRODUCTS', 'این دسته‌بندی دارای محصول فعال است و قابل حذف نیست.')
      }
      if (db.categories.some(c => c.parent_id === id)) {
        throw new MockApiError(409, 'CATEGORY_HAS_CHILDREN', 'این دسته‌بندی دارای زیردسته است.')
      }
      const idx = db.categories.findIndex(c => c.id === id)
      if (idx === -1) throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی یافت نشد.')
      db.categories.splice(idx, 1)
      writeMockDb(db)
    },

    async listAddOns(isAvailable?: boolean): Promise<PaginatedResponse<AddOnAdmin>> {
      await delayMock(60)
      const { db } = requireStaffSession()
      let rows = [...db.addons]
      if (isAvailable !== undefined) rows = rows.filter(a => a.is_available === isAvailable)
      rows.sort((a, b) => a.name.localeCompare(b.name, 'fa'))
      return paginateSlice(rows, 100, 0)
    },

    async createAddOn(payload: AddOnWritePayload): Promise<AddOnAdmin> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const nowIso = new Date().toISOString()
      const created: AddOnAdmin = {
        id: db.nextIds.addon++,
        name: payload.name.trim(),
        price: Math.max(0, Math.round(payload.price)),
        is_available: payload.is_available ?? true,
        created_at: nowIso,
        updated_at: nowIso,
      }
      db.addons.push(created)
      writeMockDb(db)
      return structuredClone(created)
    },

    async updateAddOn(id: number, payload: Partial<AddOnWritePayload>): Promise<AddOnAdmin> {
      await delayMock(80)
      const { db } = requireStaffSession()
      const addon = db.addons.find(a => a.id === id)
      if (!addon) throw new MockApiError(404, 'ADDON_NOT_FOUND', 'افزودنی یافت نشد.')
      if (payload.name !== undefined) addon.name = payload.name.trim()
      if (payload.price !== undefined) addon.price = Math.max(0, Math.round(payload.price))
      if (payload.is_available !== undefined) addon.is_available = payload.is_available
      addon.updated_at = new Date().toISOString()
      writeMockDb(db)
      return structuredClone(addon)
    },

    async deleteAddOn(id: number): Promise<void> {
      await delayMock(70)
      const { db } = requireStaffSession()
      const idx = db.addons.findIndex(a => a.id === id)
      if (idx === -1) throw new MockApiError(404, 'ADDON_NOT_FOUND', 'افزودنی یافت نشد.')
      db.addons.splice(idx, 1)
      db.productAddons = db.productAddons.filter(link => link.addon_id !== id)
      writeMockDb(db)
    },

    async listProducts(params: {
      category_id?: number
      status?: string
      is_main_dish?: boolean
      search?: string
      limit?: number
      offset?: number
    } = {}): Promise<PaginatedResponse<ProductAdmin>> {
      await delayMock(80)
      const { db } = requireStaffSession()
      let rows = [...db.products]
      if (params.category_id) rows = rows.filter(p => p.category.id === params.category_id)
      if (params.status) rows = rows.filter(p => p.status === params.status)
      if (params.is_main_dish !== undefined) rows = rows.filter(p => p.is_main_dish === params.is_main_dish)
      if (params.search?.trim()) {
        const q = params.search.trim().toLowerCase()
        rows = rows.filter(
          p => p.name.toLowerCase().includes(q) || p.slug.toLowerCase().includes(q)
        )
      }
      rows.sort((a, b) => a.display_order - b.display_order || a.name.localeCompare(b.name, 'fa'))
      return paginateSlice(rows, params.limit ?? 50, params.offset ?? 0)
    },

    async getProduct(id: number): Promise<ProductDetailAdmin> {
      await delayMock(60)
      const { db } = requireStaffSession()
      const product = db.products.find(p => p.id === id)
      if (!product) throw new MockApiError(404, 'PRODUCT_NOT_FOUND', 'محصول یافت نشد.')
      return {
        ...structuredClone(product),
        addons: resolveProductAddons(product.id, db.productAddons, db.addons, true),
      }
    },

    async createProduct(payload: ProductWritePayload, imageDataUrl?: string): Promise<ProductDetailAdmin> {
      await delayMock(100)
      const { db } = requireStaffSession()
      const category = db.categories.find(c => c.id === payload.category_id)
      if (!category) throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی یافت نشد.')
      if (db.products.some(p => p.slug === payload.slug)) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'این نامک محصول قبلاً ثبت شده است.')
      }
      if (
        payload.compare_at_price !== undefined &&
        payload.compare_at_price !== null &&
        payload.compare_at_price <= payload.price
      ) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'قیمت قبل از تخفیف باید بیشتر از قیمت فروش باشد.')
      }

      const nowIso = new Date().toISOString()
      const created: ProductAdmin = syncProductDerivedFields({
        id: db.nextIds.product++,
        category: structuredClone(category),
        name: payload.name.trim(),
        slug: payload.slug.trim(),
        description: (payload.description || '').trim(),
        image_url: imageDataUrl || '/img/placeholder.webp',
        webp_image_url: imageDataUrl || '/img/placeholder.webp',
        price: Math.max(0, Math.round(payload.price)),
        compare_at_price: payload.compare_at_price ?? null,
        discount_percent: 0,
        stock_quantity: payload.stock_quantity ?? null,
        is_in_stock: true,
        status: payload.status ?? 'AVAILABLE',
        is_main_dish: payload.is_main_dish ?? true,
        prep_time_minutes: payload.prep_time_minutes ?? 0,
        display_order: payload.display_order ?? 0,
        created_at: nowIso,
        updated_at: nowIso,
      })

      db.products.push(created)

      if (payload.addons) {
        for (const link of payload.addons) {
          if (link.min_quantity > link.max_quantity) {
            throw new MockApiError(422, 'VALIDATION_ERROR', 'بیشینه افزودنی نباید کمتر از کمینه باشد.')
          }
          db.productAddons.push({
            id: db.nextIds.productAddon++,
            product_id: created.id,
            addon_id: link.addon_id,
            min_quantity: link.min_quantity,
            max_quantity: link.max_quantity,
          })
        }
      }

      writeMockDb(db)
      return backofficeApi.catalog.getProduct(created.id)
    },

    async updateProduct(
      id: number,
      payload: Partial<ProductWritePayload>,
      imageDataUrl?: string
    ): Promise<ProductDetailAdmin> {
      await delayMock(100)
      const { db } = requireStaffSession()
      const product = db.products.find(p => p.id === id)
      if (!product) throw new MockApiError(404, 'PRODUCT_NOT_FOUND', 'محصول یافت نشد.')

      const nextPrice = payload.price ?? product.price
      const nextCompare =
        payload.compare_at_price !== undefined ? payload.compare_at_price : product.compare_at_price
      if (nextCompare !== null && nextCompare !== undefined && nextCompare <= nextPrice) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'قیمت قبل از تخفیف باید بیشتر از قیمت فروش باشد.')
      }

      if (payload.category_id !== undefined) {
        const category = db.categories.find(c => c.id === payload.category_id)
        if (!category) throw new MockApiError(404, 'CATEGORY_NOT_FOUND', 'دسته‌بندی یافت نشد.')
        product.category = structuredClone(category)
      }
      if (payload.name !== undefined) product.name = payload.name.trim()
      if (payload.slug !== undefined) {
        if (db.products.some(p => p.slug === payload.slug && p.id !== id)) {
          throw new MockApiError(422, 'VALIDATION_ERROR', 'این نامک محصول قبلاً ثبت شده است.')
        }
        product.slug = payload.slug.trim()
      }
      if (payload.description !== undefined) product.description = payload.description.trim()
      if (payload.price !== undefined) product.price = Math.max(0, Math.round(payload.price))
      if (payload.compare_at_price !== undefined) product.compare_at_price = payload.compare_at_price
      if (payload.stock_quantity !== undefined) product.stock_quantity = payload.stock_quantity
      if (payload.status !== undefined) product.status = payload.status
      if (payload.is_main_dish !== undefined) product.is_main_dish = payload.is_main_dish
      if (payload.prep_time_minutes !== undefined) product.prep_time_minutes = payload.prep_time_minutes
      if (payload.display_order !== undefined) product.display_order = payload.display_order
      if (imageDataUrl) {
        product.image_url = imageDataUrl
        product.webp_image_url = imageDataUrl
      }

      syncProductDerivedFields(product)
      product.updated_at = new Date().toISOString()

      if (payload.addons !== undefined) {
        db.productAddons = db.productAddons.filter(l => l.product_id !== id)
        for (const link of payload.addons) {
          if (link.min_quantity > link.max_quantity) {
            throw new MockApiError(422, 'VALIDATION_ERROR', 'بیشینه افزودنی نباید کمتر از کمینه باشد.')
          }
          db.productAddons.push({
            id: db.nextIds.productAddon++,
            product_id: id,
            addon_id: link.addon_id,
            min_quantity: link.min_quantity,
            max_quantity: link.max_quantity,
          })
        }
      }

      writeMockDb(db)
      return backofficeApi.catalog.getProduct(id)
    },

    async setProductAddons(id: number, addons: AddonLinkInput[]): Promise<ProductDetailAdmin> {
      return backofficeApi.catalog.updateProduct(id, { addons })
    },

    async deleteProduct(id: number): Promise<void> {
      await delayMock(70)
      const { db } = requireStaffSession()
      const idx = db.products.findIndex(p => p.id === id)
      if (idx === -1) throw new MockApiError(404, 'PRODUCT_NOT_FOUND', 'محصول یافت نشد.')
      db.products.splice(idx, 1)
      db.productAddons = db.productAddons.filter(l => l.product_id !== id)
      writeMockDb(db)
    },
  },

  cms: {
    async getRestaurantSettings(): Promise<RestaurantSettings> {
      await delayMock(60)
      const { db } = requireStaffSession()
      return structuredClone(db.restaurantSettings)
    },

    async updateRestaurantSettings(payload: Partial<RestaurantSettings>): Promise<RestaurantSettings> {
      await delayMock(90)
      const { db } = requireStaffSession()
      const nextOpen = payload.open_time ?? db.restaurantSettings.open_time
      const nextClose = payload.close_time ?? db.restaurantSettings.close_time
      if (nextOpen === nextClose) {
        throw new MockApiError(422, 'VALIDATION_ERROR', 'زمان باز و بسته شدن نمی‌تواند یکسان باشد.')
      }
      db.restaurantSettings = {
        ...db.restaurantSettings,
        ...payload,
        updated_at: new Date().toISOString(),
      }
      writeMockDb(db)
      return structuredClone(db.restaurantSettings)
    },

    async getAllSiteSections(): Promise<SiteSectionsMap> {
      await delayMock(60)
      const { db } = requireStaffSession()
      return structuredClone(db.siteSections)
    },

    async updateSiteSection<K extends SiteSectionKey>(
      key: K,
      content: SiteSectionsMap[K]
    ): Promise<{ key: K; content: SiteSectionsMap[K] }> {
      await delayMock(90)
      const { db } = requireStaffSession()
      db.siteSections[key] = structuredClone(content)
      writeMockDb(db)
      return { key, content: structuredClone(content) }
    },

    async listMediaAssets(kind?: MediaAssetKind): Promise<MediaAssetAdmin[]> {
      await delayMock(60)
      const { db } = requireStaffSession()
      return db.mediaAssets
        .filter(m => !kind || m.kind === kind)
        .map(m => structuredClone(m))
    },

    async createMediaAsset(payload: {
      kind: MediaAssetKind
      fileUrl: string
      title?: string
      alt_text?: string
    }): Promise<MediaAssetAdmin> {
      await delayMock(100)
      const { db } = requireStaffSession()
      const created: MediaAssetAdmin = {
        id: db.nextIds.media++,
        kind: payload.kind,
        title: (payload.title || '').trim(),
        alt_text: (payload.alt_text || '').trim(),
        file: payload.fileUrl,
        webp_file: payload.fileUrl,
        created_at: new Date().toISOString(),
      }
      db.mediaAssets.unshift(created)
      writeMockDb(db)
      return structuredClone(created)
    },

    async updateMediaAsset(
      id: number,
      payload: { title?: string; alt_text?: string }
    ): Promise<MediaAssetAdmin> {
      await delayMock(70)
      const { db } = requireStaffSession()
      const asset = db.mediaAssets.find(m => m.id === id)
      if (!asset) throw new MockApiError(404, 'MEDIA_NOT_FOUND', 'فایل رسانه‌ای یافت نشد.')
      if (payload.title !== undefined) asset.title = payload.title.trim()
      if (payload.alt_text !== undefined) asset.alt_text = payload.alt_text.trim()
      writeMockDb(db)
      return structuredClone(asset)
    },

    async deleteMediaAsset(id: number): Promise<void> {
      await delayMock(60)
      const { db } = requireStaffSession()
      const idx = db.mediaAssets.findIndex(m => m.id === id)
      if (idx === -1) throw new MockApiError(404, 'MEDIA_NOT_FOUND', 'فایل رسانه‌ای یافت نشد.')
      db.mediaAssets.splice(idx, 1)
      writeMockDb(db)
    },
  },
}
