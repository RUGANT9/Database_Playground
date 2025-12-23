import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)
db = client.fastapi_db
collection = db.items

async def create_index():
    print("Creating index on 'price'...")
    index_name = await collection.create_index("price")
    print(f"Index created: {index_name}")

    # Optional: see all indexes
    indexes = await collection.index_information()
    print("Current indexes:")
    for name in indexes:
        print(name)

    client.close()

if __name__ == "__main__":
    asyncio.run(create_index())
