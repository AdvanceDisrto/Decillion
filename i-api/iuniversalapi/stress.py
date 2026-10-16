"""Deterministic bounded 10,000-event workload. No live remote API connections."""
import argparse
import asyncio
import json
import time
from . import ScopedCache, Telemetry, digest

async def stress(count=10000, concurrency=100):
    if not (1<=count<=100000 and 1<=concurrency<=500):
        raise ValueError('events 1..100000, concurrency 1..500')
    gate=asyncio.Semaphore(concurrency)
    cache=ScopedCache()
    started=time.perf_counter()
    results=[None]*count
    async def work(i):
        async with gate:
            prompt='repeat-query-'+str(i%100)
            scope='stress-test-user'
            model='mock-only-no-external-provider'
            hit=cache.get(scope,model,prompt)
            if hit is None:
                await asyncio.sleep(0)
                cache.put(scope,model,prompt,{'result':digest({'prompt':prompt})})
            results[i]={'ok':True,'cache_hit':hit is not None}
    # Batch creation limits queued task allocation even for large event counts.
    for offset in range(0,count,1000):
        await asyncio.gather(*(work(i) for i in range(offset,min(offset+1000,count))))
    duration=max(time.perf_counter()-started,1e-6)
    telemetry=Telemetry.optimize_cross_plane(results)
    return {'workload':'bounded-in-process-mock-events','actual_network_connections':0,
            'requested_events':count,'max_concurrency':concurrency,
            'duration_s':round(duration,4),'events_per_second':round(count/duration,2),
            'telemetry':telemetry,'receipt_sha256':digest({'count':count,'telemetry':telemetry}),
            'certification':'not issued','signature':None,
            'claims':'Simulation only; not a 10,000-socket load test'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--events',type=int,default=10000)
    p.add_argument('--concurrency',type=int,default=100)
    a=p.parse_args()
    print(json.dumps(asyncio.run(stress(a.events,a.concurrency)),indent=2))

if __name__=='__main__':main()
