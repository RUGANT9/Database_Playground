# lb.py
import asyncio
from aiohttp import web, ClientSession
import random

# FastAPI instances
BACKENDS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003"
]

current = 0  # for round-robin
healthy_backends = []
async def check_backend(session, backend):
    try:
        async with session.get(f"{backend}/health") as resp:
            if resp.status == 200:
                return backend
    except:
        pass
    return None

async def health_check_loop():
    global healthy_backends
    async with ClientSession() as session:
        while True:
            results = await asyncio.gather(*[check_backend(session, b) for b in BACKENDS])
            healthy_backends = [b for b in results if b is not None]
            print(f"Healthy backends: {healthy_backends}")
            await asyncio.sleep(5)  # check every 5 seconds

async def handle(request):
    if not healthy_backends:
        return web.Response(text="No backends available", status=503)
    
    backend = random.choice(healthy_backends)  # simple random routing
    
    params = request.rel_url.query
    async with ClientSession() as session:
        try:
            async with session.get(f"{backend}{request.rel_url}", params=params) as resp:
                data = await resp.text()
                return web.Response(text=data, status=resp.status, headers=resp.headers)
        except:
            return web.Response(text=f"Backend {backend} failed", status=503)

app = web.Application()
app.router.add_route("*", "/{tail:.*}", handle)

if __name__ == "__main__":
    async def main():
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

    asyncio.run(main())