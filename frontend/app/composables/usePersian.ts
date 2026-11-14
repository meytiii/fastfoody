export function usePersian() {
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

  const toPersianDigits = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return ''
    return String(value).replace(/[0-9]/g, (w) => persianDigits[+w] || w)
  }

  const formatNumber = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return '۰'
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return '۰'
    const formatted = new Intl.NumberFormat('en-US').format(num)
    return toPersianDigits(formatted)
  }

  const formatToman = (amount: number | string | undefined | null): string => {
    return `${formatNumber(amount)} تومان`
  }

  return {
    toPersianDigits,
    formatNumber,
    formatToman,
  }
}

