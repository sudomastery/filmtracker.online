import { create } from 'zustand'

interface OnboardingState {
  step: 1 | 2 | 3
  selectedGenreIds: number[]
  selectedGenreNames: string[]
  followedUserIds: string[]

  setStep: (step: 1 | 2 | 3) => void
  toggleGenre: (id: number, name: string) => void
  toggleFollow: (userId: string) => void
  reset: () => void
}

export const useOnboardingStore = create<OnboardingState>()((set, get) => ({
  step: 1,
  selectedGenreIds: [],
  selectedGenreNames: [],
  followedUserIds: [],

  setStep: (step) => set({ step }),

  toggleGenre: (id, name) => {
    const { selectedGenreIds, selectedGenreNames } = get()
    const idx = selectedGenreIds.indexOf(id)
    if (idx === -1) {
      set({
        selectedGenreIds: [...selectedGenreIds, id],
        selectedGenreNames: [...selectedGenreNames, name],
      })
    } else {
      set({
        selectedGenreIds: selectedGenreIds.filter((g) => g !== id),
        selectedGenreNames: selectedGenreNames.filter((_, i) => i !== idx),
      })
    }
  },

  toggleFollow: (userId) => {
    const { followedUserIds } = get()
    if (followedUserIds.includes(userId)) {
      set({ followedUserIds: followedUserIds.filter((id) => id !== userId) })
    } else {
      set({ followedUserIds: [...followedUserIds, userId] })
    }
  },

  reset: () =>
    set({ step: 1, selectedGenreIds: [], selectedGenreNames: [], followedUserIds: [] }),
}))
