import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', {
  state: () => ({
    isMobileMenuOpen: false,
    isSearchOpen: false,
    activeSection: 'home',
  }),

  actions: {
    toggleMobileMenu() {
      this.isMobileMenuOpen = !this.isMobileMenuOpen
    },

    closeMobileMenu() {
      this.isMobileMenuOpen = false
    },

    toggleSearch() {
      this.isSearchOpen = !this.isSearchOpen
    },

    closeSearch() {
      this.isSearchOpen = false
    },

    setActiveSection(section: string) {
      this.activeSection = section
    },
  },
})

