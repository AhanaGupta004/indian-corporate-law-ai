import { create } from 'zustand'
import { documentAPI } from '../../../shared/utils/api'

export const useFileStore = create((set, get) => ({
  files: [],
  activeDocId: null,
  activeDoc: null,
  summaryData: null,
  analyzing: false,

  setFiles: (files) => set({ files }),

  refreshFiles: async () => {
    const res = await documentAPI.list()
    set({ files: res.documents || [] })
    return res
  },

  setActiveDoc: (docId, doc = null) => set({ activeDocId: docId, activeDoc: doc, summaryData: null, analyzing: false }),

  setActive: (docId, summaryData = null) => set({ activeDocId: docId, summaryData }),

  setSummary: (data) => set({ summaryData: data }),

  setAnalyzing: (value) => set({ analyzing: value }),

  clearActive: () => set({ activeDocId: null, activeDoc: null, summaryData: null, analyzing: false }),
}))