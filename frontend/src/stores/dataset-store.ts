import { create } from "zustand";

interface DatasetStore {
  activeDataset: string | null;
  setActiveDataset: (name: string | null) => void;
}

export const useDatasetStore = create<DatasetStore>((set) => ({
  activeDataset: null,
  setActiveDataset: (name) => set({ activeDataset: name }),
}));
