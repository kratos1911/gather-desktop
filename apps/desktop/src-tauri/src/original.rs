use std::fs::{self, OpenOptions};
use std::io::Write;
use std::os::windows::ffi::OsStrExt;
use std::ptr::{null, null_mut};
use tauri::{AppHandle, Manager};
use windows_sys::Win32::UI::{Shell::ShellExecuteW, WindowsAndMessaging::SW_SHOWNORMAL};

fn extension(media: &str, bytes: &[u8]) -> Option<&'static str> {
    match media {
        "text/plain" if std::str::from_utf8(bytes).is_ok() => Some("txt"),
        "text/markdown" if std::str::from_utf8(bytes).is_ok() => Some("md"),
        "application/pdf" if bytes.starts_with(b"%PDF-") => Some("pdf"),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if bytes.starts_with(b"PK\x03\x04") =>
        {
            Some("docx")
        }
        "image/png" if bytes.starts_with(b"\x89PNG\r\n\x1a\n") => Some("png"),
        "image/jpeg" if bytes.starts_with(b"\xff\xd8\xff") => Some("jpg"),
        _ => None,
    }
}

#[tauri::command]
pub fn open_saved_original(
    app: AppHandle,
    title: String,
    media: String,
    bytes: Vec<u8>,
) -> Result<bool, String> {
    let failed = || "original_save_failed".to_owned();
    if !(1..=65_536).contains(&bytes.len()) {
        return Err(failed());
    }
    let extension = extension(&media, &bytes).ok_or_else(failed)?;
    let stem: String = title.rsplit_once('.').map_or(title.as_str(), |(stem, _)| stem)
        .chars()
        .take(64)
        .map(|c| if c.is_alphanumeric() || matches!(c, '-' | '_' | ' ') { c } else { '_' })
        .collect();
    let directory = app.path().download_dir().map_err(|_| failed())?.join("Gather");
    fs::create_dir_all(&directory).map_err(|_| failed())?;
    let path = directory.join(format!("{}-{}.{}", stem.trim(), uuid::Uuid::new_v4(), extension));
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&path)
        .map_err(|_| failed())?;
    let written = file.write_all(&bytes);
    drop(file);
    let mut zone = path.as_os_str().to_os_string();
    zone.push(":Zone.Identifier");
    if written.is_err() || fs::write(zone, b"[ZoneTransfer]\r\nZoneId=3\r\n").is_err() {
        let _ = fs::remove_file(&path);
        return Err(failed());
    }
    let wide: Vec<u16> = path.as_os_str().encode_wide().chain([0]).collect();
    // Use the Windows file association with an absolute path created above.
    let status = unsafe {
        ShellExecuteW(null_mut(), null(), wide.as_ptr(), null(), null(), SW_SHOWNORMAL)
    };
    Ok(status as usize > 32)
}
