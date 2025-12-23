import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)
db = client.fastapi_db
collection = db.items


async def drop_index():
    print("Dropping index 'price_1'...")

    try:
        await collection.drop_index("price_1")
        print("Index dropped successfully.")
    except Exception as e:
        print("Error dropping index:", e)

    # Verify remaining indexes
    indexes = await collection.index_information()
    print("Current indexes:")
    for name in indexes:
        print(name)

    client.close()


if __name__ == "__main__":
    asyncio.run(drop_index())
