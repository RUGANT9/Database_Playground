import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)
db = client.fastapi_db
collection = db.items


CATEGORIES = [
    "electronics",
    "books",
    "clothing",
    "sports",
    "home",
    "toys",
]


async def seed_data():
    total_records = 10_000
    batch_size = 1_000
    documents = []

    print("Seeding data...")

    for i in range(total_records):
        doc = {
            "name": f"Item {i}",
            "description": f"Description for item {i}",
            "price": random.randint(10, 5000),
            "category": random.choice(CATEGORIES),
            "is_active": random.choice([True, False]),
        }

        documents.append(doc)

        # Insert in batches
        if len(documents) == batch_size:
            await collection.insert_many(documents)
            documents.clear()
            print(f"Inserted {i + 1} records")

    # Insert remaining docs
    if documents:
        await collection.insert_many(documents)

    print("Seeding complete!")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
