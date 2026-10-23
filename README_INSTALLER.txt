dannyboi's Karaoke v2.9 - Windows installer build project

HOW TO GET THE ACTUAL SETUP EXE
1. Extract ZIP, upload contents into a private GitHub repository.
2. Open Actions > Build Windows Installer EXE > Run workflow.
3. Download artifact Dannybois_Karaoke_v2.9_Windows_Installer.
4. Unzip artifact and run Dannybois_Karaoke_v2.9_Setup.exe on Windows 10/11.
5. Use desktop or Start Menu shortcut. Right-click running app on taskbar > Pin to taskbar.

Windows app uses pywebview, WebView2 runtime may be required. The app has a local library and YouTube Data API search, which needs your own API key. The attached third-party YouTube API tools were reviewed; they require Google OAuth and are not required for the existing API-key search implementation. No keys or OAuth secrets are included.

NOTE: This ZIP is source + installer build automation, not a precompiled Windows EXE.
