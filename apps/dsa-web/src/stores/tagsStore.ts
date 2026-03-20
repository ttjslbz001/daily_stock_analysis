import { create } from 'zustand';
import { tagsApi } from '../api/tags';

interface TagsState {
  stockTags: Record<string, string[]>;
  allTags: string[];
  loading: boolean;
  error: string | null;
  fetchStockTags: (code: string) => Promise<void>;
  fetchAllTags: () => Promise<void>;
  addTag: (code: string, tag: string) => Promise<void>;
  removeTag: (code: string, tag: string) => Promise<void>;
}

const getMsg = (e: unknown) => (e instanceof Error ? e.message : String(e));

export const useTagsStore = create<TagsState>((set) => ({
  stockTags: {},
  allTags: [],
  loading: false,
  error: null,

  fetchStockTags: async (code: string) => {
    try {
      const tags = await tagsApi.getStockTags(code);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
      }));
    } catch (error: unknown) {
      set({ error: getMsg(error) });
    }
  },

  fetchAllTags: async () => {
    try {
      const tags = await tagsApi.getAllTags();
      set({ allTags: tags });
    } catch (error: unknown) {
      set({ error: getMsg(error) });
    }
  },

  addTag: async (code: string, tag: string) => {
    try {
      const tags = await tagsApi.addTag(code, tag);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
        allTags: state.allTags.includes(tag) ? state.allTags : [...state.allTags, tag].sort(),
      }));
    } catch (error: unknown) {
      set({ error: getMsg(error) });
      throw error;
    }
  },

  removeTag: async (code: string, tag: string) => {
    try {
      const tags = await tagsApi.removeTag(code, tag);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
      }));
    } catch (error: unknown) {
      set({ error: getMsg(error) });
      throw error;
    }
  },
}));
