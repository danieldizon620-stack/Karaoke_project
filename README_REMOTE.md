# dannyboi's Karaoke v4.0 + Android Remote (source build)

## Included
- Windows app updated with a LAN-only paired remote service on TCP 8877.
- Android Studio Java app for searching karaoke videos, adding songs to the shared queue, seeing/removing queued songs, and sending microphone audio to the PC over Wi-Fi.
- Windows microphone receiver script (`mic_receiver.py`).
- GitHub Actions Android APK build workflow, plus the existing Windows EXE installer workflow.

## Windows setup
1. Build and install the Windows app using `.github/workflows/build-windows-exe.yml`.
2. **Recommended:** Set a stable 6-digit PIN before launching the Windows app: `setx DANNYBOI_REMOTE_PIN 123456` (replace 123456 with your own random PIN), then sign out and back in. If not set, the app generates a new PIN each launch.
3. Launch the Windows app. The console prints `Windows IP`, `PIN`, and port `8877`. For a windowed EXE without a console, start the Python source from a terminal (`python app.py`) to view these details. You may also set your own PIN as above and determine your PC IP using `ipconfig`.
4. Allow incoming TCP 8877 through Windows Defender Firewall for **Private networks only**. Keep your phone and PC on the same trusted Wi-Fi network.
5. Install the Android APK and enter the PC's IPv4 address and pairing PIN. Press Connect, then search and add songs.
6. Remote song additions appear in the Windows Singing Queue within about two seconds. Existing automatic next-song playback is retained.

## Android APK build
1. Upload the entire project to a GitHub repository.
2. Run Actions > Build Android Karaoke Remote APK > Run workflow.
3. Download `Dannybois_Karaoke_Remote_Android_APK` from Artifacts, unzip it and install `app-debug.apk` on your phone (allow installation from that source).
4. Or open `android-remote/` in Android Studio and select Build > Build APK(s).

## Phone microphone
- Microphone streaming is **experimental**, and is separate from YouTube video audio. It requires the Windows receiver running and a low-latency audio device.
- Install on PC: `python -m pip install sounddevice`.
- In the same terminal session, set the PIN: `set DANNYBOI_REMOTE_PIN=123456` (use your PIN), then `python mic_receiver.py`.
- Allow incoming UDP 8878 through Windows Firewall for Private networks only.
- Tap `Start Phone Microphone` on Android, grant mic permission, and sing. Audio comes from the PC's selected default output device.
- Use headphones or a mixer to prevent loud feedback. Phone Wi-Fi microphones may have delay and are not a replacement for a dedicated wireless karaoke mic.

## Security / limitations
- Do not expose TCP 8877 or UDP 8878 to the public internet. PIN is sent over local unencrypted HTTP, so only use a trusted private Wi-Fi network. Prefer stronger TLS pairing for untrusted networks.
- The supplied YouTube API key in the Windows source is not sent to Android. You should rotate/restrict that key before sharing source publicly.
- YouTube playback remains subject to the owner's embedding permissions. Phone requests queue songs on the PC, not on the phone.
- The ZIP is a buildable source project, **not a compiled APK or installer EXE**. GitHub/Android Studio builds and device testing are required.
