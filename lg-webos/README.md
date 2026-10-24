# LG webOS TV 5.x — direct playback

Open LG TV's Web Browser and enter `http://WINDOWS_PC_IP:8877/tv` (replace WINDOWS_PC_IP with the address shown by the Windows host). Enter the six-digit pairing PIN from Windows. Use the Android remote on the same network to search and queue songs. Videos are played by the TV's YouTube embedded player, not mirrored from the PC.

Run the updated Windows host in this ZIP; older versions do not serve `/tv`.

Notes:
- YouTube embedded playback is subject to YouTube's restrictions and the TV's browser compatibility. Some videos cannot play on webOS 5.x; test on the physical TV.
- Browser autoplay policies may require pressing OK/Play on the TV remote to start playback.
- 100/100 is only a completion indicator, not microphone pitch scoring.
- The PIN protects queue access on the LAN. Do not expose port 8877 to the public Internet.
- This package is a browser-based TV edition, not an installed `.ipk`. LG Developer Mode and device testing would be required for an IPK.
