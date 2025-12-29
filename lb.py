# lb.py
import asyncio
from aiohttp import web, ClientSession, TCPConnector
import random
import heapq

# FastAPI instances
BACKENDS = [
    [0,"http://127.0.0.1:8001"],
    [0,"http://127.0.0.1:8002"],
    [0,"http://127.0.0.1:8003"]
]

current = 0  # for round-robin
healthy_backends = []
backend_lock = asyncio.Lock()  # Protect heap access
proxy_session = None  # Reusable session for proxying requests
async def check_backend(session, backend):
    try:
        async with session.get(f"{backend}/health", timeout=2) as resp:
            if resp.status == 200:
                return backend
    except Exception:
        pass
    return None

async def health_check_loop():
    global healthy_backends
    async with ClientSession() as session:
        while True:
            results = await asyncio.gather(*[check_backend(session, b[1]) for b in BACKENDS])
            healthy_urls = set(url for url in results if url is not None)
            
            async with backend_lock:
                # Preserve existing counts for healthy backends, remove unhealthy ones
                healthy_backends = [[count, url] for count, url in healthy_backends if url in healthy_urls]
                
                # Add new healthy backends with count 0
                existing_urls = {url for count, url in healthy_backends}
                for url in healthy_urls:
                    if url not in existing_urls:
                        healthy_backends.append([0, url])
                
                heapq.heapify(healthy_backends)
                print(f"Healthy backends: {healthy_backends}")
            
            await asyncio.sleep(5)  # check every 5 seconds

async def handle(request):
    async with backend_lock:
        if not healthy_backends:
            return web.Response(text="No backends available", status=503)
        
        # Peek at the least loaded backend (don't remove it)
        count, backend = healthy_backends[0]
        # Increment its count in-place
        healthy_backends[0][0] += 1
        heapq.heapify(healthy_backends)
    
    params = request.rel_url.query
    try:
        async with proxy_session.get(f"{backend}{request.rel_url}", params=params, timeout=30) as resp:
            data = await resp.text()
            # Decrement on completion
            async with backend_lock:
                for item in healthy_backends:
                    if item[1] == backend:
                        item[0] -= 1
                        heapq.heapify(healthy_backends)
                        break
            return web.Response(text=data, status=resp.status, headers=resp.headers)
    except Exception as e:
        # Decrement on failure too
        async with backend_lock:
            for item in healthy_backends:
                if item[1] == backend:
                    item[0] -= 1
                    heapq.heapify(healthy_backends)
                    break
        return web.Response(text=f"Backend {backend} failed: {e}", status=503)

app = web.Application()
app.router.add_route("*", "/{tail:.*}", handle)

if __name__ == "__main__":
    async def main():
        global proxy_session
        
        # Create reusable session with connection pooling
        connector = TCPConnector(limit=300, limit_per_host=100)
        proxy_session = ClientSession(connector=connector)
        
        try:
            # Start health check loop
            asyncio.create_task(health_check_loop())
            # Start the web server
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host="127.0.0.1", port=9000)
            await site.start()
            print("Load balancer running on http://127.0.0.1:9000")
            while True:
                await asyncio.sleep(3600)  # keep running
        finally:
            await proxy_session.close()

    asyncio.run(main())