import type {
  AddOnAdmin,
  CategoryAdmin,
  CustomerAddress,
  CustomerNote,
  CustomerProfile,
  MediaAssetAdmin,
  OrderDetailBackoffice,
  PaymentBackoffice,
  ProductAddOnAdmin,
  ProductAdmin,
  RestaurantSettings,
  SiteSectionsMap,
  StaffProfile,
} from '~/types'

export interface MockProductAddOnRow {
  id: number
  product_id: number
  addon_id: number
  min_quantity: number
  max_quantity: number
}

export interface MockOrderRecord extends OrderDetailBackoffice {
  customer_id: number
}

export interface MockCustomerRecord extends CustomerProfile {
  is_active: boolean
  is_staff: boolean
  is_superuser: boolean
  password?: string
}

export interface MockDatabaseState {
  restaurantSettings: RestaurantSettings
  siteSections: SiteSectionsMap
  mediaAssets: MediaAssetAdmin[]
  categories: CategoryAdmin[]
  addons: AddOnAdmin[]
  products: ProductAdmin[]
  productAddons: MockProductAddOnRow[]
  customers: MockCustomerRecord[]
  addresses: Array<CustomerAddress & { customer_id: number }>
  customerNotes: Array<CustomerNote & { customer_id: number }>
  orders: MockOrderRecord[]
  payments: PaymentBackoffice[]
  dailyCounter: Record<string, number>
  nextIds: {
    category: number
    addon: number
    product: number
    productAddon: number
    customer: number
    address: number
    note: number
    order: number
    orderItem: number
    payment: number
    media: number
  }
}

function isoOffsetMinutes(offsetMinutes: number): string {
  return new Date(Date.now() + offsetMinutes * 60_000).toISOString()
}

export function getInitialMockDatabase(): MockDatabaseState {
  const nowIso = new Date().toISOString()
  const todayDate = new Date().toISOString().slice(0, 10)

  const categories: CategoryAdmin[] = [
    {
      id: 1,
      parent_id: null,
      name: 'برگرهای دست‌ساز',
      slug: 'burgers',
      description: 'گوشت تازه گوساله با نان بریوش روزانه',
      image_url: '/svg/sandwich.svg',
      webp_image_url: null,
      display_order: 1,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 2,
      parent_id: null,
      name: 'پیتزا ناپلی',
      slug: 'pizzas',
      description: 'خمیر تخمیر طولانی ۴۸ ساعته در تنور سنگی',
      image_url: '/svg/pizza.svg',
      webp_image_url: null,
      display_order: 2,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 3,
      parent_id: 2,
      name: 'پیتزاهای تند و ویژه',
      slug: 'spicy-pizzas',
      description: 'ترکیب عسل تند، چیلی تازه و گوشت تنوری',
      image_url: '/svg/color_pizza.svg',
      webp_image_url: null,
      display_order: 3,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 4,
      parent_id: null,
      name: 'پاستا تازه',
      slug: 'pasta',
      description: 'رشته‌های دست‌ساز روزانه با سس‌های اصیل ایتالیایی',
      image_url: '/svg/food.svg',
      webp_image_url: null,
      display_order: 4,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 5,
      parent_id: null,
      name: 'سالادهای ارگانیک',
      slug: 'salads',
      description: 'سبزیجات مزرعه با سس‌های دست‌ساز بدون نگه‌دارنده',
      image_url: '/svg/food.svg',
      webp_image_url: null,
      display_order: 5,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 6,
      parent_id: null,
      name: 'نوشیدنی‌های طبیعی',
      slug: 'drinks',
      description: 'نوشیدنی‌های خنک و تخمیری طبیعی',
      image_url: '/svg/drinks.svg',
      webp_image_url: null,
      display_order: 6,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 7,
      parent_id: null,
      name: 'دسرهای فصلی',
      slug: 'desserts',
      description: 'شیرینی‌های گرم اسکاندیناوی پخت صبح',
      image_url: '/svg/dessert.svg',
      webp_image_url: null,
      display_order: 7,
      is_active: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
  ]

  const categoryById = Object.fromEntries(categories.map(c => [c.id, c]))

  const addons: AddOnAdmin[] = [
    {
      id: 1,
      name: 'پنیر گودا دودی اضافه',
      price: 35000,
      is_available: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 2,
      name: 'بیکن گوساله ترد',
      price: 55000,
      is_available: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 3,
      name: 'هالوپینو کبابی',
      price: 20000,
      is_available: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 4,
      name: 'پنیر موزارلا بوفالا اضافه',
      price: 60000,
      is_available: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 5,
      name: 'سس هات‌هانی دست‌ساز',
      price: 28000,
      is_available: true,
      created_at: nowIso,
      updated_at: nowIso,
    },
    {
      id: 6,
      name: 'دیپ ترافل سفید (ناموجود موقت)',
      price: 45000,
      is_available: false,
      created_at: nowIso,
      updated_at: nowIso,
    },
  ]

  const makeProduct = (
    id: number,
    categoryId: number,
    name: string,
    slug: string,
    description: string,
    price: number,
    compareAtPrice: number | null,
    stockQuantity: number | null,
    status: ProductAdmin['status'],
    isMainDish: boolean,
    prepTimeMinutes: number,
    displayOrder: number
  ): ProductAdmin => {
    const isDiscounted = compareAtPrice !== null && compareAtPrice > price
    const discountPercent = isDiscounted
      ? Math.round(((compareAtPrice! - price) * 100) / compareAtPrice!)
      : 0
    const isInStock =
      status === 'AVAILABLE' && (stockQuantity === null || stockQuantity > 0)

    return {
      id,
      category: categoryById[categoryId]!,
      name,
      slug,
      description,
      image_url: '/img/placeholder.webp',
      webp_image_url: '/img/placeholder.webp',
      price,
      compare_at_price: compareAtPrice,
      discount_percent: discountPercent,
      stock_quantity: stockQuantity,
      is_in_stock: isInStock,
      status,
      is_main_dish: isMainDish,
      prep_time_minutes: prepTimeMinutes,
      display_order: displayOrder,
      created_at: isoOffsetMinutes(-id * 120),
      updated_at: nowIso,
    }
  }

  const products: ProductAdmin[] = [
    makeProduct(
      1,
      1,
      'اسموکی فورست برگر (تک‌نفره ۱۸۰ گرم)',
      'smoky-forest-burger-single',
      'گوشت راسته گوساله تازه، پنیر گودای دودی دست‌ساز، قارچ وحشی تفت‌داده با کره گیاهی و نان بریوش کنجدی.',
      365000,
      410000,
      18,
      'AVAILABLE',
      true,
      20,
      1
    ),
    makeProduct(
      2,
      1,
      'اسموکی فورست برگر (دبل ۳۶۰ گرم)',
      'smoky-forest-burger-double',
      'دو لایه گوشت راسته گوساله تازه، دو ورق پنیر گودای دودی، قارچ وحشی تفت‌داده و نان بریوش برشته.',
      485000,
      540000,
      10,
      'AVAILABLE',
      true,
      24,
      2
    ),
    makeProduct(
      3,
      1,
      'ترافل بیف کینگ',
      'truffle-beef-king',
      'گوشت خالص گوساله رزماری، پیاز کاراملی با شکر قهوه‌ای و پنیر بلوچیز طبیعی در نان سیب‌زمینی نرم.',
      385000,
      null,
      null,
      'AVAILABLE',
      true,
      22,
      3
    ),
    makeProduct(
      4,
      1,
      'چیکن کریسپی اسکاندیناوی',
      'nordic-crispy-chicken',
      'سینه مرغ سوخاری ترد مزه‌دارشده با دوغ کفیر و پاپریکا، کلم قرمز متبل، خیارشور خانگی و سس شوید.',
      295000,
      null,
      4,
      'AVAILABLE',
      true,
      18,
      4
    ),
    makeProduct(
      5,
      2,
      'پیتزا مارگریتا بوفالا ناپلی (متوسط ۲۸ سانتی)',
      'margherita-bufala-medium',
      'خمیر تخمیر ۴۸ ساعته، سس گوجه سن‌مارزانو، پنیر موزارلا بوفالای تازه، ریحان تازه و روغن زیتون فرابکر.',
      310000,
      350000,
      null,
      'AVAILABLE',
      true,
      15,
      5
    ),
    makeProduct(
      6,
      2,
      'پیتزا مارگریتا بوفالا ناپلی (بزرگ ۳۴ سانتی)',
      'margherita-bufala-large',
      'نسخه دونفره با خمیر تخمیر ۴۸ ساعته، سس گوجه سن‌مارزانو، پنیر موزارلا بوفالا و برگ ریحان تازه.',
      405000,
      null,
      null,
      'AVAILABLE',
      true,
      17,
      6
    ),
    makeProduct(
      7,
      3,
      'پیتزا پپرونی هات‌هانی',
      'pepperoni-hot-honey',
      'پپرونی تند تنوری ترد، چیلی تازه، عسل گون تزریق‌شده با چیپوتله و پنیر موزارلا روی خمیر ناپلی.',
      355000,
      395000,
      12,
      'AVAILABLE',
      true,
      16,
      7
    ),
    makeProduct(
      8,
      2,
      'پیتزا روست‌بیف پستو',
      'roast-beef-pesto',
      'گوشت ریش‌ریش گوساله آرام‌پز، سس پستوی گردو و ریحان، پارمزان ۲۴ ماهه و زیتون کالاماتا.',
      395000,
      null,
      0,
      'OUT_OF_STOCK',
      true,
      18,
      8
    ),
    makeProduct(
      9,
      4,
      'تالیتله ترافل و قارچ وحشی',
      'tagliatelle-truffle-mushroom',
      'رشته‌های تالیتله تازه تهیه شده روزانه، سس کره و مریم‌گلی، قارچ قهوه‌ای و پنیر گرانا پادانو.',
      325000,
      null,
      null,
      'AVAILABLE',
      true,
      16,
      9
    ),
    makeProduct(
      10,
      5,
      'سالاد سالمون نروژی و کینوا',
      'nordic-salmon-quinoa-bowl',
      'تکه‌های سالمون دودی ملایم، کینوای سه‌رنگ، آووکادو، ادامامه، کاهو محلی و سس دیژون عسل.',
      345000,
      null,
      null,
      'AVAILABLE',
      false,
      10,
      10
    ),
    makeProduct(
      11,
      5,
      'سالاد سزار با فیله مرغ هیزمی',
      'caesar-grilled-chicken',
      'مغز کاهو رومانو خنک، فیله مرغ گریل‌شده با لیمو و زعفران، کروتان نان چاودار و سس سزار دست‌ساز.',
      265000,
      290000,
      null,
      'AVAILABLE',
      false,
      10,
      11
    ),
    makeProduct(
      12,
      6,
      'کولر لیمو ترش و نعناع کوهی',
      'citrus-mint-cooler',
      'عصاره لیموترش سنگی تازه، نعناع کوهی کوبیده شده، شربت نیشکر ارگانیک و سودای خنک.',
      85000,
      null,
      null,
      'AVAILABLE',
      false,
      4,
      12
    ),
    makeProduct(
      13,
      6,
      'کامبوچای توت‌های وحشی',
      'wild-berry-kombucha',
      'نوشیدنی تخمیر شده پروبیوتیک طبیعی با تمشک جنگلی، زغال‌اخته و چای سبز.',
      95000,
      null,
      null,
      'AVAILABLE',
      false,
      3,
      13
    ),
    makeProduct(
      14,
      7,
      'سینامون بان هل و دارچین اسکاندیناوی',
      'cardamom-cinnamon-bun',
      'رول نان سوئدی پخته‌شده با کره حیوانی معطر، هل سبز ساییده، دارچین سیلان و شکر مرواریدی.',
      125000,
      null,
      9,
      'AVAILABLE',
      false,
      5,
      14
    ),
    makeProduct(
      15,
      1,
      'برگر آزمایشی فصلی (پنهان)',
      'seasonal-test-burger',
      'آیتم ویژه آزمایشی که در پنل مدیریت دیده می‌شود و در منوی مشتریان پنهان است.',
      420000,
      null,
      null,
      'HIDDEN',
      false,
      20,
      15
    ),
  ]

  const productAddons: MockProductAddOnRow[] = [
    { id: 1, product_id: 1, addon_id: 1, min_quantity: 0, max_quantity: 3 },
    { id: 2, product_id: 1, addon_id: 2, min_quantity: 0, max_quantity: 2 },
    { id: 3, product_id: 1, addon_id: 3, min_quantity: 0, max_quantity: 4 },
    { id: 4, product_id: 1, addon_id: 6, min_quantity: 0, max_quantity: 2 },
    { id: 5, product_id: 2, addon_id: 1, min_quantity: 0, max_quantity: 4 },
    { id: 6, product_id: 2, addon_id: 2, min_quantity: 0, max_quantity: 3 },
    { id: 7, product_id: 3, addon_id: 1, min_quantity: 0, max_quantity: 3 },
    { id: 8, product_id: 3, addon_id: 2, min_quantity: 0, max_quantity: 2 },
    { id: 9, product_id: 4, addon_id: 3, min_quantity: 0, max_quantity: 3 },
    { id: 10, product_id: 5, addon_id: 4, min_quantity: 0, max_quantity: 2 },
    { id: 11, product_id: 5, addon_id: 5, min_quantity: 0, max_quantity: 3 },
    { id: 12, product_id: 6, addon_id: 4, min_quantity: 0, max_quantity: 3 },
    { id: 13, product_id: 7, addon_id: 4, min_quantity: 0, max_quantity: 2 },
    { id: 14, product_id: 7, addon_id: 5, min_quantity: 0, max_quantity: 3 },
    { id: 15, product_id: 7, addon_id: 3, min_quantity: 0, max_quantity: 3 },
  ]

  const customers: MockCustomerRecord[] = [
    {
      id: 1,
      phone: '09123456789',
      full_name: 'مدیر رستوران فست‌فودی',
      is_blocked: false,
      is_active: true,
      is_staff: true,
      is_superuser: true,
      password: 'Test@1234',
      date_joined: isoOffsetMinutes(-14400),
      created_at: isoOffsetMinutes(-14400),
    },
    {
      id: 2,
      phone: '09120000000',
      full_name: 'سارا محمدی',
      is_blocked: false,
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: isoOffsetMinutes(-4320),
      created_at: isoOffsetMinutes(-4320),
    },
    {
      id: 3,
      phone: '09121112233',
      full_name: 'امیرحسین رضایی',
      is_blocked: false,
      is_active: true,
      is_staff: false,
      is_superuser: false,
      date_joined: isoOffsetMinutes(-2880),
      created_at: isoOffsetMinutes(-2880),
    },
  ]

  const addresses: Array<CustomerAddress & { customer_id: number }> = [
    {
      id: 1,
      customer_id: 2,
      title: 'منزل',
      address_text: 'تهران، خیابان ولیعصر، بالاتر از پارک ساعی، کوچه دهم، پلاک ۱۴، واحد ۳',
      recipient_name: 'سارا محمدی',
      recipient_phone: '09120000000',
      is_out_of_zone: false,
      is_default: true,
      created_at: isoOffsetMinutes(-4000),
      updated_at: isoOffsetMinutes(-4000),
    },
    {
      id: 2,
      customer_id: 2,
      title: 'محل کار',
      address_text: 'تهران، سعادت‌آباد، بلوار دریا، پلاک ۶۲، طبقه ۴',
      recipient_name: 'سارا محمدی',
      recipient_phone: '09120000000',
      is_out_of_zone: true,
      is_default: false,
      created_at: isoOffsetMinutes(-2000),
      updated_at: isoOffsetMinutes(-2000),
    },
    {
      id: 3,
      customer_id: 3,
      title: 'خانه',
      address_text: 'تهران، جردن، خیابان ناهید شرقی، پلاک ۱۸',
      recipient_name: 'امیرحسین رضایی',
      recipient_phone: '09121112233',
      is_out_of_zone: false,
      is_default: true,
      created_at: isoOffsetMinutes(-1800),
      updated_at: isoOffsetMinutes(-1800),
    },
  ]

  const customerNotes: Array<CustomerNote & { customer_id: number }> = [
    {
      id: 1,
      customer_id: 2,
      text: 'ترجیح می‌دهد سس هات‌هانی در ظرف جداگانه ارسال شود.',
      author_phone: '09123456789',
      created_at: isoOffsetMinutes(-1200),
    },
  ]

  const orders: MockOrderRecord[] = [
    {
      id: 101,
      customer_id: 2,
      daily_number: 1,
      daily_number_date: todayDate,
      status: 'PROCESSING',
      payment_status: 'PAID',
      delivery_type: 'DELIVERY',
      delivery_address_snapshot:
        'تهران، خیابان ولیعصر، بالاتر از پارک ساعی، کوچه دهم، پلاک ۱۴، واحد ۳',
      delivery_recipient_name: 'سارا محمدی',
      delivery_recipient_phone: '09120000000',
      customer: { id: 2, phone: '09120000000', full_name: 'سارا محمدی' },
      subtotal: 485000,
      delivery_fee: 50000,
      total_amount: 535000,
      prep_time_minutes: 25,
      expected_ready_at: isoOffsetMinutes(17),
      paid_at: isoOffsetMinutes(-8),
      is_printed: false,
      printed_at: null,
      notes_to_kitchen: 'پیاز اضافه نشود، لطفا فیش همراه بسته‌بندی باشد.',
      expires_at: isoOffsetMinutes(7),
      canceled_at: null,
      canceled_by_id: null,
      cancellation_reason: '',
      refund_card_number: '',
      refund_tracking_code: '',
      refunded_at: null,
      created_at: isoOffsetMinutes(-9),
      items: [
        {
          id: 1,
          product_name_snapshot: 'اسموکی فورست برگر (تک‌نفره ۱۸۰ گرم)',
          unit_price_snapshot: 365000,
          quantity: 1,
          addons_total: 35000,
          line_total: 400000,
          addons: [
            {
              addon_id: 1,
              addon_name_snapshot: 'پنیر گودا دودی اضافه',
              unit_price_snapshot: 35000,
              quantity: 1,
              line_total: 35000,
            },
          ],
        },
        {
          id: 2,
          product_name_snapshot: 'کولر لیمو ترش و نعناع کوهی',
          unit_price_snapshot: 85000,
          quantity: 1,
          addons_total: 0,
          line_total: 85000,
          addons: [],
        },
      ],
    },
    {
      id: 102,
      customer_id: 3,
      daily_number: 2,
      daily_number_date: todayDate,
      status: 'READY',
      payment_status: 'PAID',
      delivery_type: 'PICKUP',
      delivery_address_snapshot: '',
      delivery_recipient_name: 'امیرحسین رضایی',
      delivery_recipient_phone: '09121112233',
      customer: { id: 3, phone: '09121112233', full_name: 'امیرحسین رضایی' },
      subtotal: 383000,
      delivery_fee: 0,
      total_amount: 383000,
      prep_time_minutes: 21,
      expected_ready_at: isoOffsetMinutes(2),
      paid_at: isoOffsetMinutes(-19),
      is_printed: true,
      printed_at: isoOffsetMinutes(-18),
      notes_to_kitchen: 'تحویل حضوری در پیشخوان',
      expires_at: isoOffsetMinutes(-5),
      canceled_at: null,
      canceled_by_id: null,
      cancellation_reason: '',
      refund_card_number: '',
      refund_tracking_code: '',
      refunded_at: null,
      created_at: isoOffsetMinutes(-20),
      items: [
        {
          id: 3,
          product_name_snapshot: 'پیتزا پپرونی هات‌هانی',
          unit_price_snapshot: 355000,
          quantity: 1,
          addons_total: 28000,
          line_total: 383000,
          addons: [
            {
              addon_id: 5,
              addon_name_snapshot: 'سس هات‌هانی دست‌ساز',
              unit_price_snapshot: 28000,
              quantity: 1,
              line_total: 28000,
            },
          ],
        },
      ],
    },
    {
      id: 103,
      customer_id: 2,
      daily_number: 3,
      daily_number_date: todayDate,
      status: 'COMPLETED',
      payment_status: 'PAID',
      delivery_type: 'DELIVERY',
      delivery_address_snapshot:
        'تهران، خیابان ولیعصر، بالاتر از پارک ساعی، کوچه دهم، پلاک ۱۴، واحد ۳',
      delivery_recipient_name: 'سارا محمدی',
      delivery_recipient_phone: '09120000000',
      customer: { id: 2, phone: '09120000000', full_name: 'سارا محمدی' },
      subtotal: 655000,
      delivery_fee: 50000,
      total_amount: 705000,
      prep_time_minutes: 20,
      expected_ready_at: isoOffsetMinutes(-90),
      paid_at: isoOffsetMinutes(-110),
      is_printed: true,
      printed_at: isoOffsetMinutes(-109),
      notes_to_kitchen: '',
      expires_at: isoOffsetMinutes(-95),
      canceled_at: null,
      canceled_by_id: null,
      cancellation_reason: '',
      refund_card_number: '',
      refund_tracking_code: '',
      refunded_at: null,
      created_at: isoOffsetMinutes(-112),
      items: [
        {
          id: 4,
          product_name_snapshot: 'پیتزا مارگریتا بوفالا ناپلی (متوسط ۲۸ سانتی)',
          unit_price_snapshot: 310000,
          quantity: 1,
          addons_total: 0,
          line_total: 310000,
          addons: [],
        },
        {
          id: 5,
          product_name_snapshot: 'سالاد سالمون نروژی و کینوا',
          unit_price_snapshot: 345000,
          quantity: 1,
          addons_total: 0,
          line_total: 345000,
          addons: [],
        },
      ],
    },
    {
      id: 104,
      customer_id: 3,
      daily_number: 4,
      daily_number_date: todayDate,
      status: 'CANCELED',
      payment_status: 'AWAITING_REFUND',
      delivery_type: 'DELIVERY',
      delivery_address_snapshot: 'تهران، جردن، خیابان ناهید شرقی، پلاک ۱۸',
      delivery_recipient_name: 'امیرحسین رضایی',
      delivery_recipient_phone: '09121112233',
      customer: { id: 3, phone: '09121112233', full_name: 'امیرحسین رضایی' },
      subtotal: 295000,
      delivery_fee: 50000,
      total_amount: 345000,
      prep_time_minutes: 23,
      expected_ready_at: isoOffsetMinutes(-30),
      paid_at: isoOffsetMinutes(-55),
      is_printed: true,
      printed_at: isoOffsetMinutes(-54),
      notes_to_kitchen: '',
      expires_at: isoOffsetMinutes(-40),
      canceled_at: isoOffsetMinutes(-48),
      canceled_by_id: 1,
      cancellation_reason: 'درخواست لغو توسط مشتری پیش از آماده‌سازی',
      refund_card_number: '',
      refund_tracking_code: '',
      refunded_at: null,
      created_at: isoOffsetMinutes(-56),
      items: [
        {
          id: 6,
          product_name_snapshot: 'چیکن کریسپی اسکاندیناوی',
          unit_price_snapshot: 295000,
          quantity: 1,
          addons_total: 0,
          line_total: 295000,
          addons: [],
        },
      ],
    },
  ]

  const payments: PaymentBackoffice[] = [
    {
      id: 1,
      order_id: 101,
      customer_phone: '09120000000',
      amount: 535000,
      status: 'SUCCEEDED',
      authority: 'MOCK-AUTH-000101',
      ref_id: '784129501',
      gateway_response_code: '100',
      verified_at: isoOffsetMinutes(-8),
      failed_at: null,
      created_at: isoOffsetMinutes(-9),
    },
    {
      id: 2,
      order_id: 102,
      customer_phone: '09121112233',
      amount: 383000,
      status: 'SUCCEEDED',
      authority: 'MOCK-AUTH-000102',
      ref_id: '784129502',
      gateway_response_code: '100',
      verified_at: isoOffsetMinutes(-19),
      failed_at: null,
      created_at: isoOffsetMinutes(-20),
    },
    {
      id: 3,
      order_id: 103,
      customer_phone: '09120000000',
      amount: 705000,
      status: 'SUCCEEDED',
      authority: 'MOCK-AUTH-000103',
      ref_id: '784129503',
      gateway_response_code: '100',
      verified_at: isoOffsetMinutes(-110),
      failed_at: null,
      created_at: isoOffsetMinutes(-111),
    },
    {
      id: 4,
      order_id: 104,
      customer_phone: '09121112233',
      amount: 345000,
      status: 'SUCCEEDED',
      authority: 'MOCK-AUTH-000104',
      ref_id: '784129504',
      gateway_response_code: '100',
      verified_at: isoOffsetMinutes(-55),
      failed_at: null,
      created_at: isoOffsetMinutes(-56),
    },
  ]

  const siteSections: SiteSectionsMap = {
    hero: {
      title: 'فست‌فودی؛ ضیافت طعم‌های دست‌ساز',
      subtitle:
        'در فست‌فودی، پیتزای تنوری ناپلی و برگرهای دست‌ساز با خمیر تخمیر طبیعی ۴۸ ساعته، پنیر تازه و سس‌های روز بدون مواد افزودنی آماده می‌شوند. طعمی خالص از دل آتش و نان تازه.',
      cta_text: 'مشاهده منو',
      cta_link: '/menu',
      background_image_url: '/img/homepage.webp',
    },
    header: {
      logo_url: '/svg/chef.svg',
      restaurant_name: 'فست‌فودی',
      tagline: 'طعم اصیل و ارگانیک',
      phone: '۰۲۱-۲۲۰۰۵۵۸۸',
      social_links: [],
    },
    footer: {
      copyright_text: 'تمامی حقوق برای آشپزخانه فست‌فودی محفوظ است.',
      address: 'تهران، خیابان ولیعصر، نرسیده به پارک وی، پلاک ۱۲۴',
      phone: '۰۲۱-۲۲۰۰۵۵۸۸',
      working_hours_text: 'همه‌روزه مطابق ساعت کاری اعلام‌شده با ارسال گرم درون و برون محدوده',
      social_links: [
        { label: 'اینستاگرام', url: 'https://instagram.com' },
        { label: 'تلگرام', url: 'https://t.me' },
      ],
    },
    announcement: {
      text: 'خمیر پیتزاهای ناپلی امروز با تخمیر ۴۸ ساعته آماده سرو است. گردونه شانس را امتحان کنید.',
      is_active: true,
      link: '/lucky-wheel',
    },
    lucky_wheel: {
      title: 'گردونه انتخاب غذای امروز',
      subtitle:
        'اگر بین گزینه‌های منوی اصلی مردد هستید، دسته‌بندی دلخواه را انتخاب کنید و چرخش را بزنید.',
      is_active: true,
    },
    about_us: {
      title: 'درباره آشپزخانه فست‌فودی',
      body: 'ما در فست‌فودی آشپزی روزانه را جایگزین مواد آماده و صنعتی کرده‌ایم. خمیر پیتزای ناپلی به مدت ۴۸ ساعت در دمای کنترل‌شده استراحت می‌کند، گوشت راسته گوساله هر صبح چرخ می‌شود و تمامی سس‌ها و دیپ‌ها در آشپزخانه خود مجموعه تهیه می‌شوند.',
      image_url: '/img/homepage.webp',
    },
  }

  const mediaAssets: MediaAssetAdmin[] = [
    {
      id: 1,
      kind: 'logo',
      title: 'لوگوی اصلی فست‌فودی',
      alt_text: 'لوگوی آشپزخانه فست‌فودی',
      file: '/svg/chef.svg',
      webp_file: null,
      created_at: nowIso,
    },
    {
      id: 2,
      kind: 'banner',
      title: 'بنر صفحه اصلی',
      alt_text: 'میز غذاهای دست‌ساز فست‌فودی',
      file: '/img/homepage.webp',
      webp_file: '/img/homepage.webp',
      created_at: nowIso,
    },
    {
      id: 3,
      kind: 'gallery',
      title: 'بشقاب سرو ویژه',
      alt_text: 'بشقاب برگر و پیتزای تنوری',
      file: '/img/placeholder.webp',
      webp_file: '/img/placeholder.webp',
      created_at: nowIso,
    },
  ]

  return {
    restaurantSettings: {
      open_time: '00:00',
      close_time: '23:59',
      is_temporarily_closed: false,
      in_zone_delivery_fee: 50000,
      out_zone_delivery_fee: 100000,
      prep_time_buffer_minutes: 5,
      updated_at: nowIso,
    },
    siteSections,
    mediaAssets,
    categories,
    addons,
    products,
    productAddons,
    customers,
    addresses,
    customerNotes,
    orders,
    payments,
    dailyCounter: { [todayDate]: 4 },
    nextIds: {
      category: 8,
      addon: 7,
      product: 16,
      productAddon: 16,
      customer: 4,
      address: 4,
      note: 2,
      order: 105,
      orderItem: 7,
      payment: 5,
      media: 4,
    },
  }
}

export function resolveProductAddons(
  productId: number,
  productAddons: MockProductAddOnRow[],
  addons: AddOnAdmin[],
  includeUnavailable: boolean
): ProductAddOnAdmin[] {
  const addonById = new Map(addons.map(a => [a.id, a]))
  return productAddons
    .filter(link => link.product_id === productId)
    .map(link => {
      const addon = addonById.get(link.addon_id)
      if (!addon) return null
      if (!includeUnavailable && !addon.is_available) return null
      return {
        addon_id: addon.id,
        name: addon.name,
        price: addon.price,
        is_available: addon.is_available,
        min_quantity: link.min_quantity,
        max_quantity: link.max_quantity,
      }
    })
    .filter((item): item is ProductAddOnAdmin => item !== null)
    .sort((a, b) => a.name.localeCompare(b.name, 'fa'))
}
