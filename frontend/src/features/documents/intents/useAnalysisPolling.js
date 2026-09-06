import { useEffect } from 'react'
import { useFileStore } from '../models/fileStore'
import { summarizeAPI } from '../../../shared/utils/api'

const PROCESSING_STATUSES = ['queued', 'uploaded', 'processing', 'extracting', 'chunking', 'embedding', 'indexing', 'analyzing']

export const useAnalysisPolling = (activeDocId) => {
  const { setSummary } = useFileStore()

  useEffect(() => {
    if (!activeDocId) return
    let cancelled = false
    let intervalId = null

    const fetchOnce = async () => {
      try {
        const res = await summarizeAPI.get(activeDocId)
        if (cancelled) return
        setSummary(res)
        const status = String(res?.status || '').toLowerCase()
        if (PROCESSING_STATUSES.includes(status)) {
          if (!intervalId) {
            intervalId = setInterval(fetchOnce, 3000)
          }
        } else if (intervalId) {
          clearInterval(intervalId)
          intervalId = null
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }

    fetchOnce()

    return () => {
      cancelled = true
      if (intervalId) clearInterval(intervalId)
    }
  }, [activeDocId, setSummary])
}