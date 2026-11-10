export function usePersian() {
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

  /**
   * Converts any English/ASCII digits in a string or number to Persian digits
   */
  const toPersianDigits = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return ''
    return String(value).replace(/[0-9]/g, (w) => persianDigits[+w] || w)
  }

  /**
   * Formats a number with comma separators (e.g. 185,000) using Persian digits
   */
  const formatNumber = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return '۰'
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return '۰'
    const formatted = new Intl.NumberFormat('en-US').format(num)
    return toPersianDigits(formatted)
  }

  /**
   * Formats a monetary value in Tomans with Persian digits
   * Example: 185000 -> "۱۸۵٬۰۰۰ تومان"
   */
  const formatToman = (amount: number | string | undefined | null): string => {
    return `${formatNumber(amount)} تومان`
  }

  return {
    toPersianDigits,
    formatNumber,
    formatToman,
  }
}
