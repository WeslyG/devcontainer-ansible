// Exercise the real elasticdump SOCKS dependency after its security override.
const assert=require('node:assert/strict');
const net=require('node:net');
const {createRequire}=require('node:module');
const root=process.env.ELASTICDUMP_ROOT || '/usr/local/share/elasticdump';
const app=createRequire(root+'/package.json');
const dump=createRequire(app.resolve('elasticdump/package.json'));
const http=createRequire(dump.resolve('socks5-http-client/package.json'));
const socks=createRequire(http.resolve('socks5-client/package.json'));
const retry=createRequire(dump.resolve('requestretry/package.json'));
const request=createRequire(retry.resolve('request/package.json'));
const FormData=request('form-data');
assert.equal(request('form-data/package.json').version,app('./package.json').overrides['form-data@<3']);
const form=new FormData();
form.append('field\r\nX-Test: injected','value',{filename:'name\r\nBad: x'});
const multipart=form.getBuffer().toString();
assert(!multipart.includes('\r\nX-Test:'));
assert(!multipart.includes('\r\nBad:'));
const {Address6}=socks('ip-address');
assert.equal(socks('ip-address/package.json').version,app('./package.json').overrides['ip-address']);
assert.equal(new Address6('::ffff:127.0.0.1').isLoopback(),true);
const Socket=http('socks5-client/lib/Socket');
const timer=setTimeout(()=>{console.error('SOCKS handshake timeout');process.exit(1)},5000);
const server=net.createServer(connection=>{
  connection.once('data',greeting=>{
    assert.equal(greeting[0],5);
    connection.write(Buffer.from([5,0]));
    connection.once('data',request=>{
      assert.equal(request[3],4); // IPv6 request: 16 bytes followed by port.
      assert.equal(request.subarray(4,20).toString('hex'),'20010db8000000000000000000000001');
      assert.equal(request.readUInt16BE(20),443);
      connection.write(Buffer.from([5,0,0,1,127,0,0,1,0,80]));
    });
  });
});
server.listen(0,'127.0.0.1',()=>{
  const client=new Socket({socksHost:'127.0.0.1',socksPort:server.address().port});
  client.on('error',error=>{throw error});
  client.on('connect',()=>{
    client.destroy();server.close();clearTimeout(timer);
    console.log('PASS: elasticdump security override, mapped loopback and real SOCKS5 IPv6 handshake');
  });
  client.connect(443,'2001:db8::1');
});
