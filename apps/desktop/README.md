# Desktop shell

The Tauri 2 shell points at the browser frontend and has no filesystem plugin or unrestricted native capability. It intentionally does not bundle Python in V0.1. Build requires Rust/Cargo and Tauri platform prerequisites.

Verification commands:

```powershell
npm.cmd install
npm.cmd run tauri -- --version
npm.cmd run tauri info
npm.cmd run tauri build
```

`tauri info` is a static prerequisite check. A successful desktop build requires Rust/Cargo and MSVC/Windows SDK; the Phase 1 workstation had neither, so the build remains unverified.
