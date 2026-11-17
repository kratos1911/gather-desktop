import { invoke, isTauri } from "@tauri-apps/api/core";
import {
  DOCX_MEDIA,
  LibraryClientError,
  type SavedOriginal,
} from "./libraryClient";

const extensions = {
  "text/plain": "txt",
  "text/markdown": "md",
  "application/pdf": "pdf",
  [DOCX_MEDIA]: "docx",
  "image/png": "png",
  "image/jpeg": "jpg",
};

export async function openSavedOriginal(file: SavedOriginal): Promise<void> {
  if (isTauri()) {
    let opened: boolean;
    try {
      opened = await invoke<boolean>("open_saved_original", {
        title: file.title,
        media: file.media,
        bytes: Array.from(file.bytes),
      });
    } catch {
      throw new LibraryClientError("original_save_failed");
    }
    if (!opened) throw new LibraryClientError("original_saved_without_viewer");
    return;
  }

  const download = document.createElement("a");
  const url = URL.createObjectURL(new Blob([file.bytes], { type: file.media }));
  const stem = file.title
    .replace(/\.[^.]*$/, "")
    .replace(/[^\p{L}\p{N}_ -]/gu, "_");
  download.download = `${stem.slice(0, 80).trim() || "Gather file"}.${extensions[file.media]}`;
  download.href = url;
  download.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
