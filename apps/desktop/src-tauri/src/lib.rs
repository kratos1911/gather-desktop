#[cfg(windows)]
mod original;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let builder = tauri::Builder::default();
    #[cfg(windows)]
    let builder = builder.invoke_handler(tauri::generate_handler![original::open_saved_original]);
    builder
        .run(tauri::generate_context!())
        .expect("error while running Gather preview");
}
