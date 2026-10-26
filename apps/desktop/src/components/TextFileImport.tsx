import { useEffect, useRef, useState } from "react";
import { LibraryClientError } from "../services/libraryClient";
import { readTextFile, type SelectedTextFile } from "../services/textFile";

const messages: Record<string, string> = {
  file_type: "Choose a TXT or Markdown file (.txt, .md or .markdown).",
  file_size: "Choose a nonempty file no larger than 64 KiB.",
  file_encoding: "Save this file as UTF-8, then select it again.",
  file_controls: "This file contains binary or unsupported control characters.",
  file_empty: "This file has no searchable text.",
  file_read_failed: "The file could not be read. Select it again.",
  cancelled: "File reading cancelled.",
};

export function TextFileImport({
  disabled,
  onSave,
}: {
  disabled: boolean;
  onSave: (file: SelectedTextFile) => Promise<boolean>;
}) {
  const [selected, setSelected] = useState<SelectedTextFile | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [reading, setReading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const request = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => () => request.current?.abort(), []);

  async function choose(file: File | undefined) {
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setSelected(null);
    setConfirmed(false);
    setError(null);
    setReading(!!file);
    if (!file) return;
    try {
      const result = await readTextFile(file, controller.signal);
      if (!controller.signal.aborted) setSelected(result);
    } catch (failure) {
      if (!controller.signal.aborted)
        setError(
          failure instanceof LibraryClientError
            ? failure.code
            : "file_read_failed",
        );
    } finally {
      if (!controller.signal.aborted) setReading(false);
    }
  }
  async function save() {
    if (!selected || !confirmed || disabled || saving || reading) return;
    setSaving(true);
    setError(null);
    try {
      if (await onSave(selected)) {
        setSelected(null);
        setConfirmed(false);
        if (input.current) input.current.value = "";
      }
    } catch {
      setError("file_save_failed");
    } finally {
      setSaving(false);
    }
  }
  return (
    <div className="text-file-import">
      <label htmlFor="pilot-text-file">Choose a TXT or Markdown file</label>
      <input
        id="pilot-text-file"
        ref={input}
        type="file"
        accept=".txt,.md,.markdown,text/plain,text/markdown"
        disabled={disabled || saving}
        onChange={(event) => void choose(event.target.files?.[0])}
      />
      <p>
        Private testing only. UTF-8, at most 64 KiB. Choosing a file reads it
        locally; nothing is uploaded until you confirm and save.
      </p>
      {reading && <p role="status">Reading selected file locally…</p>}
      {selected && (
        <>
          <p>
            Selected: <strong>{selected.title}</strong> ·{" "}
            {selected.bytes.byteLength} bytes
          </p>
          <div
            className="paper text-file-preview"
            aria-label="Local plain-text preview"
          >
            {selected.preview}
          </div>
          {selected.previewTruncated && (
            <p>
              Preview shortened. Saving preserves the complete validated file.
            </p>
          )}
          <p>
            Saving sends the original text and filename to Gather’s Supabase
            database in Sydney. Explicit worker/search actions send text to the
            private CPU model in Mumbai. Content stays stored after disconnect.
            Delete hides it immediately; an operator must finish physical
            cleanup. No completion time is promised. The pilot accepts only
            files that fit three processing passages.
          </p>
          <label className="text-file-confirm">
            <input
              type="checkbox"
              checked={confirmed}
              disabled={disabled || saving}
              onChange={(event) => setConfirmed(event.target.checked)}
            />
            I have permission to use this nonsensitive file and understand the
            cloud storage and cleanup described above.
          </label>
          <button
            className="pilot-action"
            disabled={!confirmed || disabled || saving || reading}
            onClick={() => void save()}
          >
            Save selected file
          </button>
        </>
      )}
      {error && (
        <p role="alert">
          {messages[error] ??
            "Saving could not complete. Check the import status before trying a different file."}
        </p>
      )}
    </div>
  );
}
