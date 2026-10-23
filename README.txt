INTERNET VIDEOKE v2.0 — WINDOWS EXE BUILD PROJECT

WHAT IT DOES
- Windows desktop karaoke video player with dark fullscreen-capable interface
- Internet YouTube karaoke links, song queue, next/play/pause
- Search shortcut opens YouTube
- Phone requests on same private Wi-Fi network
- Stores queue in %LOCALAPPDATA%\InternetVideoke\videoke.db
- Windows WebView2 runtime required; available on most Windows 10/11 PCs
- No PHP or XAMPP needed

IMPORTANT
- This ZIP is source code and a GitHub Actions build workflow, NOT a compiled EXE.
- To build: upload the extracted project to the ROOT of a GitHub repository,
  including .github/workflows/build-windows-exe.yml.
  GitHub > Actions > Build Windows Videoke EXE > Run workflow.
  Download the InternetVideoke_Windows_EXE artifact; extract InternetVideoke.exe.
- The app uses Python/pywebview and a local HTTP server bound to the PC's network
  interfaces. It is for trusted private networks ONLY. Windows Firewall may prompt.
  Do NOT port-forward or use it on untrusted/public Wi-Fi.
- Queue requests are unauthenticated by design on the LAN. Host playback controls
  require a session token delivered only to localhost.
- The app does not have microphone scoring or offline licensed karaoke songs.
- Some YouTube videos disable embedding; internet and user interaction required.
- YouTube policies and music/public performance licensing are your responsibility.
- If the YouTube player stays blank, check WebView2 installation and video embed rights.
- For stronger network isolation, host on a dedicated trusted Wi-Fi or disable
  the phone request feature by changing 0.0.0.0 to 127.0.0.1 in app.py.
