export interface ProductModifier {
  id: string
  name: string
  price: number
}

export interface ProductSize {
  id: string
  name: string
  priceOffset: number
}

export interface Product {
  id: string
  slug: string
  title: string
  category: string
  description: string
  price: number
  originalPrice?: number
  rating: number
  reviewsCount: number
  image: string
  prepTimeMinutes: number
  calories?: number
  isFeatured?: boolean
  isPopular?: boolean
  badges?: string[]
  sizes?: ProductSize[]
  addons?: ProductModifier[]
}

export interface Category {
  id: string
  slug: string
  title: string
  icon: string
  itemCount: number
}

export interface CartItem {
  id: string
  productId: string
  product: Product
  quantity: number
  selectedSize?: ProductSize
  selectedAddons: ProductModifier[]
  unitPrice: number
  totalPrice: number
  specialInstructions?: string
}

export interface TableReservation {
  fullName: string
  phone: string
  email?: string
  guestsCount: number
  date: string
  time: string
  notes?: string
}

export interface CustomerReview {
  id: string
  name: string
  role?: string
  avatar: string
  rating: number
  text: string
  dishOrdered?: string
  date: string
}
