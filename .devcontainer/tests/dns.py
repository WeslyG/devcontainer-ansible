"""Exercise all three BIND clients against a local deterministic DNS responder."""
import socketserver
import struct
import subprocess
import threading
from pathlib import Path

assert not list(Path('/usr/lib').glob('**/liblmdb.so*')), 'LMDB must not be present'
class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        query,sock=self.request
        end=12
        while query[end]:end+=query[end]+1
        end+=1
        qtype=struct.unpack('!H',query[end:end+2])[0]
        question=query[12:end+4]
        answer=b'\xc0\x0c'+struct.pack('!HHIH',1,1,60,4)+bytes([127,0,0,42]) if qtype==1 else b''
        packet=query[:2]+struct.pack('!HHHHH',0x8180,1,int(bool(answer)),0,0)+question+answer
        sock.sendto(packet,self.client_address)

with socketserver.UDPServer(('127.0.0.1',0),Handler) as server:
    threading.Thread(target=server.serve_forever,daemon=True).start()
    port=str(server.server_address[1])
    for args in [['dig','@127.0.0.1','-p',port,'security.example','A','+short'],
                 ['nslookup','-port='+port,'security.example','127.0.0.1'],
                 ['host','-p',port,'security.example','127.0.0.1']]:
        output=subprocess.check_output(args,stderr=subprocess.STDOUT,text=True,timeout=15)
        assert '127.0.0.42' in output,output
        print('PASS:',args[0])
    server.shutdown()
