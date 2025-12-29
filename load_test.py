import asyncio
import aiohttp
import time

URL = "http://127.0.0.1:9000/items/"
PARAMS = {"price_min": 1000, "price_max": 10000}
TOTAL_REQUESTS = 2000
CONCURRENT_REQUESTS = 200


async def fetch(session, i):
    """Fetch a single URL and return status code and latency."""
    try:
        start = time.perf_counter()
        timeout = aiohttp.ClientTimeout(total=30)
        async with session.get(URL, params=PARAMS, timeout=timeout) as response:
            await response.text()
            latency = time.perf_counter() - start
            return response.status, latency
    except asyncio.TimeoutError:
        return "timeout", 0
    except aiohttp.ClientError as e:
        return f"error: {type(e).__name__}", 0
    except Exception as e:
        return f"error: {type(e).__name__}", 0


async def run_load_test():
    # Configure connector with keep-alive and connection limits
    connector = aiohttp.TCPConnector(
        limit=CONCURRENT_REQUESTS,
        limit_per_host=CONCURRENT_REQUESTS,
        ttl_dns_cache=300,
        force_close=False  # Reuse connections
    )
    
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        tasks = []
        start = time.time()

        for i in range(TOTAL_REQUESTS):
            task = asyncio.create_task(fetch(session, i))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        end = time.time()

        # Process results with detailed breakdown
        status_codes = []
        latencies = []
        exceptions_list = []
        
        for r in results:
            if isinstance(r, tuple):
                status_codes.append(r[0])
                if isinstance(r[1], (int, float)) and r[1] > 0:
                    latencies.append(r[1])
            else:
                # Captured exception
                exceptions_list.append(type(r).__name__ if isinstance(r, Exception) else str(r))
        
        success_count = sum(1 for s in status_codes if s == 200)
        error_strings = sum(1 for s in status_codes if isinstance(s, str) and s != "timeout")
        timeout_count = sum(1 for s in status_codes if s == "timeout")
        other_status = sum(1 for s in status_codes if isinstance(s, int) and s != 200)
        
        # Count status distribution
        from collections import Counter
        status_distribution = Counter(status_codes)
        exception_distribution = Counter(exceptions_list)

        print(f"\n{'='*50}")
        print(f"Load Test Results")
        print(f"{'='*50}")
        print(f"Total requests: {TOTAL_REQUESTS}")
        print(f"Concurrent requests: {CONCURRENT_REQUESTS}")
        print(f"Time taken: {end - start:.2f}s")
        print(f"Requests/sec: {TOTAL_REQUESTS/(end - start):.2f}")
        print(f"\n{'='*50}")
        print(f"Response Summary")
        print(f"{'='*50}")
        print(f"Successful (200): {success_count}")
        print(f"Other HTTP status: {other_status}")
        print(f"Error strings: {error_strings}")
        print(f"Timeouts: {timeout_count}")
        print(f"Exceptions caught: {len(exceptions_list)}")
        print(f"Total accounted: {len(status_codes) + len(exceptions_list)}/{TOTAL_REQUESTS}")
        
        if status_distribution:
            print(f"\n{'='*50}")
            print(f"Status Code Distribution")
            print(f"{'='*50}")
            for status, count in sorted(status_distribution.items(), key=lambda x: str(x[0])):
                print(f"  {status}: {count}")
        
        if exception_distribution:
            print(f"\n{'='*50}")
            print(f"Exception Distribution")
            print(f"{'='*50}")
            for exc, count in exception_distribution.most_common():
                print(f"  {exc}: {count}")
        
        if latencies:
            print(f"\n{'='*50}")
            print(f"Latency Statistics")
            print(f"{'='*50}")
            print(f"Avg latency: {sum(latencies)/len(latencies):.4f}s")
            print(f"Max latency: {max(latencies):.4f}s")
            print(f"Min latency: {min(latencies):.4f}s")
        else:
            print(f"\nNo successful requests to calculate latency.")
        
        print(f"{'='*50}\n")


if __name__ == "__main__":
    asyncio.run(run_load_test())
