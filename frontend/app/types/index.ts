export interface ApiErrorDetail {
  code: string
  message: string
  details: Record<string, unknown> | null
}

export interface ApiErrorEnvelope {
  success: false
  error: ApiErrorDetail
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CustomerProfile {
  id: number
  phone: string
  full_name: string
  is_blocked: boolean
  date_joined: string
  created_at: string
}

export interface OTPRequestPayload {
  phone: string
}

export interface OTPRequestResponse {
  message: string
  expires_in: number
  dev_code?: string
}

export interface OTPVerifyPayload {
  phone: string
  code: string
}

export interface OTPVerifyResponse {
  user: CustomerProfile
  access: string
  refresh: string
}

export interface TokenRefreshResponse {
  access: string
  refresh: string
}

export interface CustomerAddress {
  id: number
  title: string
  address_text: string
  recipient_name: string
  recipient_phone: string
  is_out_of_zone: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

export interface CustomerAddressPayload {
  title?: string
  address_text: string
  recipient_name?: string
  recipient_phone?: string
  is_out_of_zone?: boolean
  is_default?: boolean
  replace_address_id?: number
}

export interface StaffProfile {
  id: number
  phone: string
  full_name: string
  is_staff: boolean
  is_superuser: boolean
  date_joined: string
}

export interface StaffLoginPayload {
  phone: string
  password: string
}

export interface StaffLoginResponse {
  user: StaffProfile
  csrf_token: string
}

export interface CustomerListRow {
  id: number
  phone: string
  full_name: string
  is_blocked: boolean
  is_active: boolean
  date_joined: string
  created_at: string
}

export interface CustomerAddressBackoffice {
  id: number
  title: string
  address_text: string
  recipient_name: string
  recipient_phone: string
  is_out_of_zone: boolean
  is_default: boolean
  created_at: string
}

export interface CustomerNote {
  id: number
  text: string
  author_phone: string | null
  created_at: string
}

export interface Customer360Detail {
  id: number
  phone: string
  full_name: string
  is_blocked: boolean
  is_active: boolean
  date_joined: string
  created_at: string
  addresses: CustomerAddressBackoffice[]
  notes: CustomerNote[]
  orders_count: number
  completed_orders_count: number
  lifetime_value: number
  last_order_at: string | null
}

export interface CustomerUpdatePayload {
  full_name?: string
  is_blocked?: boolean
  is_active?: boolean
}

export interface RestaurantStatus {
  is_open: boolean
  is_temporarily_closed: boolean
  open_time: string
  close_time: string
  in_zone_delivery_fee: number
  out_zone_delivery_fee: number
  min_delivery_order_amount: number
  packaging_fee: number
  prep_time_buffer_minutes: number
}

export interface RestaurantSettings {
  open_time: string
  close_time: string
  is_temporarily_closed: boolean
  in_zone_delivery_fee: number
  out_zone_delivery_fee: number
  min_delivery_order_amount: number
  packaging_fee: number
  prep_time_buffer_minutes: number
  updated_at: string
}

export type SiteSectionKey =
  | 'hero'
  | 'header'
  | 'footer'
  | 'announcement'
  | 'lucky_wheel'
  | 'about_us'

export interface SocialLinkItem {
  label: string
  url: string
}

export interface HeroSectionContent {
  title: string
  subtitle: string
  cta_text: string
  cta_link: string
  background_image_url: string
}

export interface HeaderSectionContent {
  logo_url: string
  restaurant_name: string
  tagline: string
  phone: string
  social_links: SocialLinkItem[]
}

export interface FooterSectionContent {
  copyright_text: string
  address: string
  phone: string
  working_hours_text: string
  social_links: SocialLinkItem[]
}

export interface AnnouncementSectionContent {
  text: string
  is_active: boolean
  link: string
}

export interface LuckyWheelSectionContent {
  title: string
  subtitle: string
  is_active: boolean
}

export interface AboutUsSectionContent {
  title: string
  body: string
  image_url: string
}

export interface SiteSectionsMap {
  hero: HeroSectionContent
  header: HeaderSectionContent
  footer: FooterSectionContent
  announcement: AnnouncementSectionContent
  lucky_wheel: LuckyWheelSectionContent
  about_us: AboutUsSectionContent
}

export type MediaAssetKind = 'logo' | 'banner' | 'gallery'

export interface MediaAssetPublic {
  kind: MediaAssetKind
  title: string
  alt_text: string
  url: string | null
}

export interface MediaAssetAdmin {
  id: number
  kind: MediaAssetKind
  title: string
  alt_text: string
  file: string
  webp_file: string | null
  created_at: string
}

export type ProductStatus = 'AVAILABLE' | 'OUT_OF_STOCK' | 'HIDDEN'

export interface CategoryPublic {
  id: number
  name: string
  slug: string
  description: string
  image_url: string | null
}

export interface MenuProductPublic {
  id: number
  name: string
  slug: string
  description: string
  price: number
  compare_at_price: number | null
  discount_percent: number
  is_discounted: boolean
  status: ProductStatus
  is_main_dish: boolean
  prep_time_minutes: number
  image_url: string | null
}

export interface MenuCategoryPublic {
  id: number
  name: string
  slug: string
  description: string
  image_url: string | null
  products: MenuProductPublic[]
}

export interface StorefrontMenuResponse {
  categories: MenuCategoryPublic[]
}

export interface ProductAddOnPublic {
  addon_id: number
  name: string
  price: number
  min_quantity: number
  max_quantity: number
}

export interface ProductSummaryPublic {
  id: number
  name: string
  slug: string
  description: string
  price: number
  compare_at_price: number | null
  discount_percent: number
  is_discounted: boolean
  status: ProductStatus
  is_main_dish: boolean
  prep_time_minutes: number
  image_url: string | null
  category: CategoryPublic
}

export interface ProductDetailPublic extends ProductSummaryPublic {
  addons: ProductAddOnPublic[]
}

export interface ProductSuggestionPublic {
  id: number
  name: string
  slug: string
  price: number
  compare_at_price: number | null
  discount_percent: number
  status: ProductStatus
  image_url: string | null
}

export interface ProductSuggestionsResponse {
  results: ProductSuggestionPublic[]
  did_you_mean: string | null
}

export interface LuckyWheelProduct {
  id: number
  name: string
  slug: string
  price: number
  category_id: number
  image_url: string | null
}

export interface LuckyWheelResponse {
  products: LuckyWheelProduct[]
}

export interface UpsellProductPublic {
  id: number
  name: string
  slug: string
  price: number
  compare_at_price: number | null
  discount_percent: number
  status: ProductStatus
  image_url: string | null
  category_id: number
}

export interface UpsellResponse {
  products: UpsellProductPublic[]
}

export type ProductSortChoice =
  | 'relevance'
  | 'popularity'
  | 'default'
  | 'newest'
  | 'oldest'
  | 'price_asc'
  | 'price_desc'

export interface ProductSearchParams {
  q?: string
  category?: string
  category_id?: number
  min_price?: number
  max_price?: number
  available?: boolean
  discount?: boolean
  is_main_dish?: boolean
  sort?: ProductSortChoice
  limit?: number
  offset?: number
}

export interface ProductListResponse extends PaginatedResponse<ProductSummaryPublic> {
  did_you_mean?: string | null
}

export interface CategoryAdmin {
  id: number
  name: string
  slug: string
  description: string
  image_url: string | null
  webp_image_url: string | null
  display_order: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CategoryWritePayload {
  name: string
  slug: string
  description?: string
  display_order?: number
  is_active?: boolean
}

export interface AddOnAdmin {
  id: number
  name: string
  price: number
  is_available: boolean
  created_at: string
  updated_at: string
}

export interface AddOnWritePayload {
  name: string
  price: number
  is_available?: boolean
}

export interface AddonLinkInput {
  addon_id: number
  min_quantity: number
  max_quantity: number
}

export interface ProductAddOnAdmin {
  addon_id: number
  name: string
  price: number
  is_available: boolean
  min_quantity: number
  max_quantity: number
}

export interface ProductAdmin {
  id: number
  category: CategoryAdmin
  name: string
  slug: string
  description: string
  image_url: string | null
  webp_image_url: string | null
  price: number
  compare_at_price: number | null
  discount_percent: number
  status: ProductStatus
  is_main_dish: boolean
  prep_time_minutes: number
  display_order: number
  created_at: string
  updated_at: string
}

export interface ProductDetailAdmin extends ProductAdmin {
  addons: ProductAddOnAdmin[]
}

export interface ProductWritePayload {
  name: string
  slug: string
  category_id: number
  description?: string
  price: number
  compare_at_price?: number | null
  status?: ProductStatus
  is_main_dish?: boolean
  prep_time_minutes?: number
  display_order?: number
  addons?: AddonLinkInput[]
}

export type OrderStatus =
  | 'PENDING_PAYMENT'
  | 'PROCESSING'
  | 'READY'
  | 'COMPLETED'
  | 'CANCELED'

export type PaymentStatus =
  | 'UNPAID'
  | 'PAID'
  | 'AWAITING_REFUND'
  | 'REFUNDED'

export type DeliveryType = 'PICKUP' | 'DELIVERY'

export interface OrderItemAddOnSnapshot {
  addon_id: number
  addon_name_snapshot: string
  unit_price_snapshot: number
  quantity: number
  line_total: number
}

export interface OrderItemSnapshot {
  id: number
  product_name_snapshot: string
  unit_price_snapshot: number
  quantity: number
  addons_total: number
  line_total: number
  addons: OrderItemAddOnSnapshot[]
}

export interface OrderRead {
  id: number
  daily_number: number | null
  status: OrderStatus
  payment_status: PaymentStatus
  delivery_type: DeliveryType
  delivery_address_snapshot: string
  delivery_recipient_name: string
  delivery_recipient_phone: string
  subtotal: number
  delivery_fee: number
  packaging_fee: number
  promo_code_snapshot: string
  discount_amount: number
  total_amount: number
  prep_time_minutes: number
  expected_ready_at: string | null
  paid_at: string | null
  notes_to_kitchen: string
  expires_at: string | null
  canceled_at: string | null
  cancellation_reason: string
  cancellation_requested: boolean
  cancellation_request_reason: string
  cancellation_requested_at: string | null
  refund_card_number?: string
  refund_tracking_code?: string
  refunded_at?: string | null
  created_at: string
  items: OrderItemSnapshot[]
}

export interface OrderCreateAddonPayload {
  addon_id: number
  quantity: number
}

export interface OrderCreateItemPayload {
  product_id: number
  quantity: number
  addons?: OrderCreateAddonPayload[]
}

export interface OrderCreatePayload {
  delivery_type: DeliveryType
  address_id?: number | null
  notes_to_kitchen?: string
  promo_code?: string | null
  items: OrderCreateItemPayload[]
}

export type PromoDiscountType = 'PERCENTAGE' | 'FIXED'

export interface ValidatePromoPayload {
  code: string
  subtotal: number
}

export interface ValidatePromoResponse {
  code: string
  discount_type: PromoDiscountType
  discount_value: number
  discount_amount: number
  subtotal: number
  discounted_subtotal: number
}

export interface PromoCodeAdmin {
  id: number
  code: string
  discount_type: PromoDiscountType
  discount_value: number
  max_discount_amount: number | null
  min_order_amount: number
  valid_from: string | null
  valid_until: string | null
  max_total_uses: number | null
  max_uses_per_customer: number
  first_order_only: boolean
  is_active: boolean
  usage_count: number
  created_at: string
  updated_at: string
}

export interface PromoCodeWritePayload {
  code: string
  discount_type: PromoDiscountType
  discount_value: number
  max_discount_amount?: number | null
  min_order_amount?: number
  valid_from?: string | null
  valid_until?: string | null
  max_total_uses?: number | null
  max_uses_per_customer?: number
  first_order_only?: boolean
  is_active?: boolean
}

export interface ReorderAddOn {
  addon_id: number
  name: string
  quantity: number
  unit_price: number
  line_total: number
}

export interface ReorderItem {
  product_id: number
  name: string
  quantity: number
  unit_price: number
  addons: ReorderAddOn[]
  line_total: number
}

export interface ReorderResponse {
  items: ReorderItem[]
  warnings: string[]
}

export interface CustomerNoteSnapshot {
  text: string
  author_phone: string | null
  author_name: string | null
  created_at: string
}

export interface OrderCustomerSnapshot {
  id: number
  phone: string
  full_name: string
}

export interface OrderListBackoffice {
  id: number
  daily_number: number | null
  status: OrderStatus
  payment_status: PaymentStatus
  delivery_type: DeliveryType
  customer_phone: string
  customer_full_name: string
  total_amount: number
  prep_time_minutes: number
  expected_ready_at: string | null
  is_printed: boolean
  created_at: string
  paid_at: string | null
}

export interface OrderDetailBackoffice {
  id: number
  daily_number: number | null
  daily_number_date: string | null
  status: OrderStatus
  payment_status: PaymentStatus
  delivery_type: DeliveryType
  delivery_address_snapshot: string
  delivery_recipient_name: string
  delivery_recipient_phone: string
  customer: OrderCustomerSnapshot
  subtotal: number
  delivery_fee: number
  packaging_fee: number
  promo_code_snapshot: string
  discount_amount: number
  total_amount: number
  prep_time_minutes: number
  expected_ready_at: string | null
  paid_at: string | null
  is_printed: boolean
  printed_at: string | null
  notes_to_kitchen: string
  expires_at: string | null
  canceled_at: string | null
  canceled_by_id: number | null
  cancellation_reason: string
  cancellation_requested: boolean
  cancellation_request_reason: string
  cancellation_requested_at: string | null
  refund_card_number: string
  refund_tracking_code: string
  refunded_at: string | null
  created_at: string
  items: OrderItemSnapshot[]
  customer_notes: CustomerNoteSnapshot[]
}

export interface LiveOrderBackoffice {
  id: number
  daily_number: number | null
  status: OrderStatus
  delivery_type: DeliveryType
  customer_phone: string
  delivery_address_snapshot: string
  total_amount: number
  prep_time_minutes: number
  expected_ready_at: string | null
  paid_at: string | null
  is_printed: boolean
  printed_at: string | null
  notes_to_kitchen: string
  cancellation_requested: boolean
  cancellation_request_reason: string
  cancellation_requested_at: string | null
  created_at: string
  items: OrderItemSnapshot[]
  customer_notes: CustomerNoteSnapshot[]
}

export type AnalyticsPeriod = 'today' | '7d' | '30d' | 'custom'

export interface SalesAnalyticsParams {
  period?: AnalyticsPeriod
  date_from?: string
  date_to?: string
}

export interface TopProductStat {
  product_id: number
  product_name: string
  quantity: number
  revenue: number
}

export interface LeastSellingProductStat {
  id: number
  name: string
  quantity_sold: number
}

export interface PeakHourStat {
  hour: number
  order_count: number
  revenue: number
}

export interface DailyTrendStat {
  date: string
  order_count: number
  revenue: number
}

export interface SalesAnalyticsResponse {
  period: AnalyticsPeriod
  date_from: string
  date_to: string
  gross_sales: number
  refunded_count: number
  refunded_amount: number
  net_sales: number
  paid_orders_count: number
  average_order_value: number
  total_delivery_fees: number
  total_packaging_fees: number
  total_discounts: number
  top_products: TopProductStat[]
  least_selling_products: LeastSellingProductStat[]
  peak_hours: PeakHourStat[]
  daily_trend: DailyTrendStat[]
}

export interface OrderStreamEvent {
  event_type: string
  order_id: number
  daily_number: number | null
  status: OrderStatus
  payment_status: PaymentStatus
  expected_ready_at: string | null
  cancellation_requested: boolean
  timestamp: string
}

export interface OrderBackofficeListParams {
  status?: OrderStatus | ''
  payment_status?: PaymentStatus | ''
  delivery_type?: DeliveryType | ''
  search?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export interface RecordRefundPayload {
  card_number: string
  tracking_code: string
}

export type PaymentGatewayStatus = 'PENDING' | 'SUCCEEDED' | 'FAILED' | 'CANCELED'

export interface PaymentStartResponse {
  payment_url: string
  authority: string
  amount: number
}

export interface PaymentPublic {
  id: number
  amount: number
  status: PaymentGatewayStatus
  ref_id: string
  verified_at: string | null
  created_at: string
}

export interface PaymentBackoffice {
  id: number
  order_id: number
  customer_phone: string
  amount: number
  status: PaymentGatewayStatus
  authority: string
  ref_id: string
  gateway_response_code: string
  verified_at: string | null
  failed_at: string | null
  created_at: string
}

export interface CartItemAddOn {
  addon_id: number
  name: string
  price: number
  quantity: number
  min_quantity: number
  max_quantity: number
}

export interface CartProductSnapshot {
  id: number
  slug: string
  name: string
  price: number
  compare_at_price: number | null
  prep_time_minutes: number
  image_url: string | null
  status: ProductStatus
  category_id: number
}

export interface CartItem {
  id: string
  productId: number
  product: CartProductSnapshot
  quantity: number
  selectedAddons: CartItemAddOn[]
  unitPrice: number
  addonsTotal: number
  totalPrice: number
}
