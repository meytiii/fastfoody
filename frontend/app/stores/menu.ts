import { defineStore } from 'pinia'
import { storefrontApi } from '~/services/api'
import type {
  MenuCategoryPublic,
  MenuProductPublic,
  ProductDetailPublic,
  ProductSearchParams,
  ProductSortChoice,
  ProductSuggestionPublic,
  ProductSummaryPublic,
} from '~/types'

export const useMenuStore = defineStore('menu', {
  state: () => ({
    menuCategories: [] as MenuCategoryPublic[],
    menuLoaded: false,
    menuLoading: false,
    menuError: null as string | null,

    products: [] as ProductSummaryPublic[],
    totalCount: 0,
    productsLoading: false,
    productsError: null as string | null,

    selectedCategory: 'all',
    includeSubcategories: true,
    searchQuery: '',
    onlyInStock: false,
    onlyDiscounted: false,
    onlyMainDish: false,
    minPrice: undefined as number | undefined,
    maxPrice: undefined as number | undefined,
    sortBy: 'default' as ProductSortChoice,
    limit: 20,
    offset: 0,

    suggestions: [] as ProductSuggestionPublic[],
    didYouMean: null as string | null,
    suggestionsLoading: false,

    selectedProductForModal: null as ProductDetailPublic | null,
    productModalLoading: false,
    productModalError: null as string | null,
  }),

  getters: {
    topCategories: (state): MenuCategoryPublic[] => {
      return state.menuCategories.filter(c => c.parent_id === null)
    },

    subcategoriesForSelected: (state): MenuCategoryPublic[] => {
      if (state.selectedCategory === 'all') return []
      const selected = state.menuCategories.find(c => c.slug === state.selectedCategory)
      if (!selected) return []
      const parentId = selected.parent_id ?? selected.id
      return state.menuCategories.filter(c => c.parent_id === parentId)
    },

    specialOffers: (state): ProductSummaryPublic[] => {
      const catById = new Map(state.menuCategories.map(c => [c.id, c]))
      const list: ProductSummaryPublic[] = []
      for (const cat of state.menuCategories) {
        for (const p of cat.products) {
          if (p.is_discounted && p.status === 'AVAILABLE') {
            list.push({
              ...p,
              category: {
                id: cat.id,
                name: cat.name,
                slug: cat.slug,
                description: cat.description,
                parent_id: cat.parent_id,
                image_url: cat.image_url,
              },
            })
          }
        }
      }
      if (list.length > 0) return list
      for (const cat of state.menuCategories) {
        for (const p of cat.products) {
          if (p.is_main_dish && p.status === 'AVAILABLE') {
            list.push({
              ...p,
              category: {
                id: catById.get(cat.id)!.id,
                name: cat.name,
                slug: cat.slug,
                description: cat.description,
                parent_id: cat.parent_id,
                image_url: cat.image_url,
              },
            })
          }
        }
      }
      return list
    },

    upsellProducts: (state): MenuProductPublic[] => {
      const items: MenuProductPublic[] = []
      for (const cat of state.menuCategories) {
        for (const p of cat.products) {
          if (!p.is_main_dish && p.status === 'AVAILABLE') {
            items.push(p)
          }
        }
      }
      return items
    },

    totalPages: (state): number => {
      return Math.max(1, Math.ceil(state.totalCount / state.limit))
    },

    currentPage: (state): number => {
      return Math.floor(state.offset / state.limit) + 1
    },
  },

  actions: {
    async fetchMenu(force = false) {
      if (this.menuLoaded && !force) return
      this.menuLoading = true
      this.menuError = null
      try {
        const res = await storefrontApi.catalog.getMenu()
        this.menuCategories = res.categories
        this.menuLoaded = true
      } catch (err: any) {
        this.menuError = err?.message || 'خطا در بارگذاری منو'
      } finally {
        this.menuLoading = false
      }
    },

    async searchProducts(overrideParams?: Partial<ProductSearchParams>) {
      this.productsLoading = true
      this.productsError = null
      try {
        const params: ProductSearchParams = {
          q: this.searchQuery.trim() || undefined,
          category: this.selectedCategory === 'all' ? undefined : this.selectedCategory,
          include_subcategories: this.includeSubcategories,
          available: this.onlyInStock ? true : undefined,
          discount: this.onlyDiscounted ? true : undefined,
          is_main_dish: this.onlyMainDish ? true : undefined,
          min_price: this.minPrice,
          max_price: this.maxPrice,
          sort: this.sortBy,
          limit: this.limit,
          offset: this.offset,
          ...overrideParams,
        }
        const res = await storefrontApi.catalog.getProducts(params)
        this.products = res.results
        this.totalCount = res.count
      } catch (err: any) {
        this.productsError = err?.message || 'خطا در جستجوی محصولات'
      } finally {
        this.productsLoading = false
      }
    },

    async fetchSuggestions(q: string) {
      if (!q.trim()) {
        this.suggestions = []
        this.didYouMean = null
        return
      }
      this.suggestionsLoading = true
      try {
        const res = await storefrontApi.catalog.getSuggestions(q, 6)
        this.suggestions = res.results
        this.didYouMean = res.did_you_mean
      } finally {
        this.suggestionsLoading = false
      }
    },

    async setCategory(slug: string) {
      this.selectedCategory = slug
      this.offset = 0
      await this.searchProducts()
    },

    async setPage(page: number) {
      const target = Math.max(1, page)
      this.offset = (target - 1) * this.limit
      await this.searchProducts()
    },

    async resetFilters() {
      this.selectedCategory = 'all'
      this.includeSubcategories = true
      this.searchQuery = ''
      this.onlyInStock = false
      this.onlyDiscounted = false
      this.onlyMainDish = false
      this.minPrice = undefined
      this.maxPrice = undefined
      this.sortBy = 'default'
      this.offset = 0
      await this.searchProducts()
    },

    async openProductModal(slugOrProduct: string | { slug: string }) {
      const slug = typeof slugOrProduct === 'string' ? slugOrProduct : slugOrProduct.slug
      this.productModalLoading = true
      this.productModalError = null
      try {
        this.selectedProductForModal = await storefrontApi.catalog.getProductBySlug(slug)
      } catch (err: any) {
        this.productModalError = err?.message || 'محصول یافت نشد'
      } finally {
        this.productModalLoading = false
      }
    },

    closeProductModal() {
      this.selectedProductForModal = null
      this.productModalError = null
    },
  },
})
