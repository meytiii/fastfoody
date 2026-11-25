export function usePersian() {
  const persianDigits = ['۰', '۱', '۲', '۳', '۴', '۵', '۶', '۷', '۸', '۹']

  const toPersianDigits = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return ''
    return String(value).replace(/[0-9]/g, w => persianDigits[+w] || w)
  }

  const toEnglishDigits = (value: string | undefined | null): string => {
    if (!value) return ''
    return String(value)
      .replace(/[\u06f0-\u06f9]/g, ch => String(ch.charCodeAt(0) - 0x06f0))
      .replace(/[\u0660-\u0669]/g, ch => String(ch.charCodeAt(0) - 0x0660))
  }

  const formatNumber = (value: number | string | undefined | null): string => {
    if (value === undefined || value === null) return '۰'
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (Number.isNaN(num)) return '۰'
    const formatted = new Intl.NumberFormat('en-US').format(num)
    return toPersianDigits(formatted)
  }

  const formatToman = (amount: number | string | undefined | null): string => {
    return `${formatNumber(amount)} تومان`
  }

  const formatTime = (isoOrTime: string | undefined | null): string => {
    if (!isoOrTime) return ''
    if (/^\d{2}:\d{2}(:\d{2})?$/.test(isoOrTime)) {
      return toPersianDigits(isoOrTime.slice(0, 5))
    }
    const date = new Date(isoOrTime)
    if (Number.isNaN(date.getTime())) return toPersianDigits(isoOrTime)
    const formatted = new Intl.DateTimeFormat('fa-IR', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
    return toPersianDigits(formatted)
  }

  const formatDateTime = (iso: string | undefined | null): string => {
    if (!iso) return ''
    const date = new Date(iso)
    if (Number.isNaN(date.getTime())) return ''
    const formatted = new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
    return toPersianDigits(formatted)
  }

  const formatCountdown = (seconds: number): string => {
    const safe = Math.max(0, Math.floor(seconds))
    const mins = Math.floor(safe / 60)
    const secs = safe % 60
    const padded = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
    return toPersianDigits(padded)
  }

  return {
    toPersianDigits,
    toEnglishDigits,
    formatNumber,
    formatToman,
    formatTime,
    formatDateTime,
    formatCountdown,
  }
}
