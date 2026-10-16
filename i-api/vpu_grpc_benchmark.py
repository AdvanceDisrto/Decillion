"""Real localhost-only gRPC latency measurement, not silicon attestation."""
from concurrent import futures
import grpc,hashlib,json,statistics,time
def benchmark(n=100):
    server=grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    handler=grpc.unary_unary_rpc_method_handler(lambda p,c:hashlib.sha256(p).digest(),
      request_deserializer=lambda b:b,response_serializer=lambda b:b)
    server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler(
      "i.vpu.IPC",{"EchoHash":handler}),))
    port=server.add_insecure_port("127.0.0.1:0")
    if port==0:raise RuntimeError("loopback bind failed")
    server.start()
    measurements=[]
    try:
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            grpc.channel_ready_future(channel).result(timeout=5)
            call=channel.unary_unary("/i.vpu.IPC/EchoHash",request_serializer=lambda b:b,
                 response_deserializer=lambda b:b)
            packet=b"iCalcula"*128
            for i in range(n):
                start=time.perf_counter_ns()
                assert call(packet,timeout=3)==hashlib.sha256(packet).digest()
                measurements.append((time.perf_counter_ns()-start)/1000)
    finally:server.stop(grace=0).wait(5)
    samples=sorted(measurements)
    return {"iterations":n,"latency_p50_us":round(statistics.median(samples),2),
       "latency_p95_us":round(samples[min(n-1,int(n*.95))],2),
       "transport":"real gRPC on localhost only","physical_vpu_tested":False,
       "remote_tls_link_tested":False}
if __name__=="__main__":print(json.dumps(benchmark(),indent=2))
