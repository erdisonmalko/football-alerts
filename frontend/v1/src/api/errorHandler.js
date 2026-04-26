export function parseApiError(err) {
  const data = err?.response?.data

  if (!data) {
    return 'Network error. Please try again.'
  }

  // NEW FORMAT (your standardized backend)
  if (data.errors && typeof data.errors === 'object') {
    return Object.entries(data.errors)
      .map(([field, messages]) => {
        if (field === 'general') return messages.join(', ')
        return `${field}: ${messages.join(', ')}`
      })
      .join('\n')
  }

  // BACKWARD COMPAT (optional, can remove later)
  if (Array.isArray(data.detail)) {
    return data.detail
      .map(e => `${e.loc.at(-1)}: ${e.msg}`)
      .join(', ')
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  return 'Something went wrong'
}