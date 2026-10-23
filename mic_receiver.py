"""Run on Windows PC: pip install sounddevice; python mic_receiver.py
Audio: 16 kHz 16-bit mono PCM over UDP. Do not expose UDP 8878 to the internet.
"""
import os, socket, sys, queue
try:import sounddevice as sd
except ImportError:sys.exit('Install sounddevice: python -m pip install sounddevice')
PIN=os.environ.get('DANNYBOI_REMOTE_PIN','')
if not (len(PIN)==6 and PIN.isdigit()):sys.exit('Set DANNYBOI_REMOTE_PIN to the same 6-digit PIN shown by the karaoke Windows app.')
sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);sock.bind(('0.0.0.0',8878));sock.settimeout(1)
print('Phone microphone receiver ready on UDP 8878. Use headphones to avoid feedback. Ctrl+C to stop.')
with sd.RawOutputStream(samplerate=16000,channels=1,dtype='int16',blocksize=320) as stream:
 try:
  while True:
   try:packet,addr=sock.recvfrom(2048)
   except socket.timeout:continue
   if packet[:6]==PIN.encode('ascii') and len(packet)>6:stream.write(packet[6:])
 except KeyboardInterrupt:pass
