// Every Windows app build is a GUI, including the packaged debug pilot.
#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

fn main() {
    gather_desktop_lib::run()
}

