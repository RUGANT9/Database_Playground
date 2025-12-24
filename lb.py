# lb.py
import asyncio
from aiohttp import web, ClientSession

# FastAPI instances
BACKENDS = [
    "http://127.0.0.1:8001",
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8003"
]

current = 0  # for round-robin


async def handle(request):
    global current
    # Pick backend server
    backend = BACKENDS[current]
    current = (current + 1) % len(BACKENDS)

    # Forward the request to backend
    async with ClientSession() as session:
        # Forward query params
        params = request.rel_url.query
        async with session.get(f"{backend}{request.rel_url}", params=params) as resp:
            data = await resp.text()
            return web.Response(text=data, status=resp.status, headers=resp.headers)


app = web.Application()
app.router.add_route("*", "/{tail:.*}", handle)

if __name__ == "__main__":
    web.run_app(app, port=9000)
