import { defineStore } from 'pinia'
import type { Category, Product } from '~/types'

export const useMenuStore = defineStore('menu', {
  state: () => ({
    selectedCategory: 'all',
    searchQuery: '',
    selectedProductForModal: null as Product | null,

    categories: [
      { id: 'all', slug: 'all', title: 'همه دسته‌ها', icon: '/svg/food.svg', itemCount: 16 },
      { id: 'burgers', slug: 'burgers', title: 'برگرهای دست‌ساز', icon: '/svg/sandwich.svg', itemCount: 4 },
      { id: 'pizzas', slug: 'pizzas', title: 'پیتزا ناپلی', icon: '/svg/pizza.svg', itemCount: 4 },
      { id: 'pasta', slug: 'pasta', title: 'پاستا تازه', icon: '/svg/food.svg', itemCount: 2 },
      { id: 'salads', slug: 'salads', title: 'سالادهای ارگانیک', icon: '/svg/food.svg', itemCount: 3 },
      { id: 'drinks', slug: 'drinks', title: 'نوشیدنی‌های طبیعی', icon: '/svg/drinks.svg', itemCount: 3 },
      { id: 'desserts', slug: 'desserts', title: 'دسرهای فصلی', icon: '/svg/dessert.svg', itemCount: 2 },
    ] as Category[],

    products: [
      {
        id: 'b1',
        slug: 'smoky-forest-burger',
        title: 'اسموکی فورست برگر',
        category: 'burgers',
        description: 'گوشت راسته گوساله تازه، پنیر گودای دودی دست‌ساز، قارچ وحشی تفت‌داده با کره گیاهی، سس ترامفل و نان بریوش تازه کنجدی.',
        price: 365000,
        originalPrice: 410000,
        rating: 4.9,
        reviewsCount: 142,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 20,
        calories: 680,
        isFeatured: true,
        isPopular: true,
        badges: ['پیشنهاد سرآشپز', 'پرفروش'],
        sizes: [
          { id: 'single', name: 'تک برگر (۱۸۰ گرم)', priceOffset: 0 },
          { id: 'double', name: 'دبل برگر (۳۶۰ گرم)', priceOffset: 120000 },
        ],
        addons: [
          { id: 'cheese', name: 'پنیر گودا اضافه', price: 35000 },
          { id: 'bacon', name: 'بیکن گوشت دودی', price: 45000 },
          { id: 'jalapeno', name: 'هالوپینو کبابی', price: 20000 },
        ],
      },
      {
        id: 'b2',
        slug: 'truffle-beef-burger',
        title: 'ترافل بیف کینگ',
        category: 'burgers',
        description: 'گوشت خالص گوساله رزماری، پیاز کاراملی با شکر قهوه‌ای، پنیر بلوچیز طبیعی و دیپ ترافل سفید در نان سیب‌زمینی نرم.',
        price: 385000,
        rating: 4.8,
        reviewsCount: 98,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 22,
        calories: 720,
        isFeatured: false,
        isPopular: true,
        badges: ['طعم خاص'],
        sizes: [
          { id: 'single', name: 'تک پتی (۲۰۰ گرم)', priceOffset: 0 },
          { id: 'double', name: 'دبل پتی (۴۰۰ گرم)', priceOffset: 130000 },
        ],
        addons: [
          { id: 'mushrooms', name: 'قارچ ترافلی اضافه', price: 40000 },
          { id: 'caramelized-onion', name: 'پیاز کاراملی دوبل', price: 25000 },
        ],
      },
      {
        id: 'b3',
        slug: 'nordic-crispy-chicken',
        title: 'چیکن کریسپی اسکاندیناوی',
        category: 'burgers',
        description: 'سینه مرغ سوخاری ترد مزه‌دار شده با دوغ کفیر و پاپریکا، کلم قرمز متبل، خیارشور خانگی و سس شوید و خردل فرانسوی.',
        price: 295000,
        rating: 4.7,
        reviewsCount: 84,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 18,
        calories: 590,
        isFeatured: true,
        isPopular: false,
        badges: ['ترد و ملایم'],
        sizes: [
          { id: 'standard', name: 'کلاسیک', priceOffset: 0 },
          { id: 'spicy', name: 'اسپایسی تند آتشین', priceOffset: 15000 },
        ],
        addons: [
          { id: 'cheddar', name: 'دیپ چدار گرم', price: 30000 },
          { id: 'fries-side', name: 'سیب‌زمینی سرخ‌کرده کناری', price: 65000 },
        ],
      },
      {
        id: 'b4',
        slug: 'green-avocado-burger',
        title: 'آووکادو برگر سبز',
        category: 'burgers',
        description: 'همبرگر ارگانیک، اسلایس‌های آووکادو هاس تازه، گوجه خشک آفتابی، جوانه شبدر و مایونز ریحان محلی در نان جو سبوس‌دار.',
        price: 345000,
        rating: 4.6,
        reviewsCount: 57,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 15,
        calories: 520,
        isFeatured: false,
        isPopular: false,
        badges: ['ارگانیک', 'سالم'],
        addons: [
          { id: 'avocado', name: 'اسلایس آووکادو دوبل', price: 50000 },
        ],
      },
      {
        id: 'p1',
        slug: 'margherita-bufala',
        title: 'مارگریتا بوفالا ناپلی',
        category: 'pizzas',
        description: 'خمیر تخمیر طولانی ۴۸ ساعته، سس گوجه سن‌مارزانو دست‌چین، پنیر موزارلا بوفالای تازه، برگ‌های ریحان تازه و روغن زیتون بکر فرابکر.',
        price: 310000,
        originalPrice: 350000,
        rating: 4.9,
        reviewsCount: 215,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 15,
        calories: 610,
        isFeatured: true,
        isPopular: true,
        badges: ['ایتالیایی اصیل', 'تنور هیزمی'],
        sizes: [
          { id: 'medium', name: 'متوسط (۲۸ سانتی‌متر)', priceOffset: 0 },
          { id: 'large', name: 'بزرگ (۳۴ سانتی‌متر)', priceOffset: 95000 },
        ],
        addons: [
          { id: 'extra-mozzarella', name: 'موزارلا بوفالا اضافه', price: 55000 },
          { id: 'cherry-tomatoes', name: 'گوجه گیلاسی بوداده', price: 25000 },
        ],
      },
      {
        id: 'p2',
        slug: 'pepperoni-hot-honey',
        title: 'پپرونی هات‌هانی',
        category: 'pizzas',
        description: 'پپرونی تند تنوری ترد، چیلی تازه، عسل گون طبیعی گرم تزریق‌شده با فلفل چیپوتله و پنیر موزارلا کشسانی روی خمیر ناپلی.',
        price: 355000,
        rating: 4.8,
        reviewsCount: 176,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 16,
        calories: 780,
        isFeatured: true,
        isPopular: true,
        badges: ['تند و ملس', 'پرفروش'],
        sizes: [
          { id: 'medium', name: 'متوسط (۲۸ سانتی‌متر)', priceOffset: 0 },
          { id: 'large', name: 'بزرگ (۳۴ سانتی‌متر)', priceOffset: 105000 },
        ],
        addons: [
          { id: 'extra-pepperoni', name: 'پپرونی اضافه تنوری', price: 48000 },
          { id: 'hot-honey', name: 'سس هات‌هانی دوبل', price: 28000 },
        ],
      },
      {
        id: 'p3',
        slug: 'wild-mushroom-gorgonzola',
        title: 'پیتزا قارچ وحشی و گورگونزولا',
        category: 'pizzas',
        description: 'مخلوط قارچ‌های جنگلی، پنیر بلو گورگونزولا با اصالت، خامه ترش تازه، سیر بو داده و مغز گردوی خرد شده معطر.',
        price: 370000,
        rating: 4.7,
        reviewsCount: 63,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 17,
        calories: 690,
        isFeatured: false,
        isPopular: false,
        badges: ['سبک اسکاندیناوی'],
        sizes: [
          { id: 'medium', name: 'متوسط (۲۸ سانتی‌متر)', priceOffset: 0 },
          { id: 'large', name: 'بزرگ (۳۴ سانتی‌متر)', priceOffset: 110000 },
        ],
      },
      {
        id: 'p4',
        slug: 'roast-beef-pesto',
        title: 'روست‌بیف پستو',
        category: 'pizzas',
        description: 'گوشت ریش‌ریش گوساله پخته شده به روش آرام‌پز، سس پستوی تازه دست‌ساز گردو و ریحان، پارمزان ۲۴ ماهه و زیتون کالاماتا.',
        price: 395000,
        rating: 4.9,
        reviewsCount: 112,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 18,
        calories: 740,
        isFeatured: false,
        isPopular: true,
        badges: ['پروتئین بالا'],
      },
      {
        id: 'pa1',
        slug: 'tagliatelle-truffle-mushroom',
        title: 'تالیتله دست‌ساز ترافل قارچ',
        category: 'pasta',
        description: 'رشته‌های تالیتله تازه زرده تخم‌مرغ تهیه شده روزانه، سس کره و مریم‌گلی، قارچ قهوه‌ای و ورقه ترافل تابستانی با پنیر گرانا پادانو.',
        price: 325000,
        rating: 4.8,
        reviewsCount: 78,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 16,
        calories: 580,
        isFeatured: true,
        isPopular: false,
        badges: ['دست‌ساز روزانه'],
      },
      {
        id: 'pa2',
        slug: 'penne-arrabbiata-stracciatella',
        title: 'پنه آرابیاتا استراچاتلا',
        category: 'pasta',
        description: 'پنه ریگاته سیسیلی، سس گوجه تند با سیر و فلفل قرمز تفت‌خورده، همراه با تکه‌های پنیر تازه و خنک استراچاتلا.',
        price: 285000,
        rating: 4.7,
        reviewsCount: 52,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 14,
        calories: 490,
        isFeatured: false,
        isPopular: false,
        badges: ['گیاهی', 'تند'],
      },
      {
        id: 's1',
        slug: 'nordic-salmon-quinoa-bowl',
        title: 'سالاد بوول سالمون نروژی و کینوا',
        category: 'salads',
        description: 'تکه‌های سالمون دودی ملایم، کینوای سه‌رنگ پخته شده در عصاره لیمو، آووکادو، ادامامه، کاهوپیچ محلی و سس دیژون عسل.',
        price: 345000,
        rating: 4.9,
        reviewsCount: 91,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 12,
        calories: 420,
        isFeatured: true,
        isPopular: true,
        badges: ['سوپرفود', 'سالم و سبک'],
      },
      {
        id: 's2',
        slug: 'caesar-grilled-chicken',
        title: 'سزار با فیله مرغ هیزمی',
        category: 'salads',
        description: 'مغز کاهو رومانو تازه و خنک، فیله مرغ گریل شده با لیمو و زعفران، کروتان نان چاودار برشته و سس سزار دست‌ساز بدون مایونز صنعتی.',
        price: 265000,
        rating: 4.8,
        reviewsCount: 163,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 12,
        calories: 380,
        isFeatured: false,
        isPopular: true,
        badges: ['پرفروش'],
      },
      {
        id: 's3',
        slug: 'beetroot-goat-cheese',
        title: 'سالاد چغندر تنوری و پنیر بز',
        category: 'salads',
        description: 'لبوی تنوری شیرین، راکت وحشی، پنیر بز نرم محلی، گردوی بوداده کاراملی و سرکه بالزامیک کهنه مودنا.',
        price: 245000,
        rating: 4.6,
        reviewsCount: 41,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 10,
        calories: 310,
        isFeatured: false,
        isPopular: false,
        badges: ['ارگانیک'],
      },
      {
        id: 'd1',
        slug: 'citrus-mint-cooler',
        title: 'کولر لیمو ترش و نعناع کوهی',
        category: 'drinks',
        description: 'عصاره لیموترش تازه سنگی، برگ‌های نعناع معطر کوبیده شده، شربت نیشکر ارگانیک و سودای خنک گازدار.',
        price: 85000,
        rating: 4.9,
        reviewsCount: 130,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 5,
        calories: 95,
        isFeatured: false,
        isPopular: true,
        badges: ['نوشیدنی طبیعی'],
      },
      {
        id: 'd2',
        slug: 'wild-berry-kombucha',
        title: 'کامبوچای توت‌های وحشی',
        category: 'drinks',
        description: 'نوشیدنی تخمیر شده پروبیوتیک طبیعی با تمشک جنگلی، زغال‌اخته و چای سبز، بدون هیچ‌گونه ماده افزودنی شیمیایی.',
        price: 95000,
        rating: 4.7,
        reviewsCount: 49,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 5,
        calories: 45,
        isFeatured: false,
        isPopular: false,
        badges: ['پروبیوتیک'],
      },
      {
        id: 'de1',
        slug: 'cardamom-cinnamon-bun',
        title: 'سینامون بان هل و دارچین اسکاندیناوی',
        category: 'desserts',
        description: 'رول نان سنتی سوئدی پخته شده در کره حیوانی معطر، مغز هل سبز ساییده، دارچین سیلان و دانه‌های مرواریدی شکر.',
        price: 125000,
        rating: 4.9,
        reviewsCount: 184,
        image: '/img/placeholder.webp',
        prepTimeMinutes: 5,
        calories: 340,
        isFeatured: true,
        isPopular: true,
        badges: ['دست‌پخت روز'],
      },
    ] as Product[],
  }),

  getters: {
    filteredProducts: (state): Product[] => {
      let list = state.products

      if (state.selectedCategory !== 'all') {
        list = list.filter(p => p.category === state.selectedCategory)
      }

      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase().trim()
        list = list.filter(p =>
          p.title.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q) ||
          p.badges?.some(b => b.toLowerCase().includes(q))
        )
      }

      return list
    },

    specialOffers: (state): Product[] => {
      return state.products.filter(p => p.isFeatured)
    },

    popularItems: (state): Product[] => {
      return state.products.filter(p => p.isPopular)
    },
  },

  actions: {
    setCategory(categoryId: string) {
      this.selectedCategory = categoryId
    },

    setSearchQuery(query: string) {
      this.searchQuery = query
    },

    openProductModal(product: Product) {
      this.selectedProductForModal = product
    },

    closeProductModal() {
      this.selectedProductForModal = null
    },
  },
})
