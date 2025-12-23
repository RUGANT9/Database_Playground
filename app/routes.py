from fastapi import APIRouter, HTTPException, Query
from app.database import collection
from app.schemas import ItemCreate, ItemResponse
from app.models import item_helper
from bson import ObjectId
from aiocache import Cache
import json

router = APIRouter(prefix="/items", tags=["Items"])

r = Cache(Cache.MEMORY)
# CREATE
@router.post("/", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    result = await collection.insert_one(item.dict())
    new_item = await collection.find_one({"_id": result.inserted_id})
    return item_helper(new_item)

# READ ALL
@router.get("/")
async def get_items(price_min: int = Query(None), price_max: int = Query(None), limit: int = Query(10)):
    query = {}
    cache_key = f"items_{price_min}_{price_max}_{limit}"
    # Try fetching from cache
    
    cached = await r.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Build query
    if price_min is not None:
        query["price"] = {"$gte": price_min}
    if price_max is not None:
        query.setdefault("price", {})["$lte"] = price_max

    # MongoDB query with projection + limit
    cursor = collection.find(query)
    items = await cursor.to_list(length=limit)
    
    items_list = [item_helper(item) for item in items]
    
    # Store in Redis cache
    await r.set(cache_key, json.dumps([item_helper(item) for item in items]), ttl=60)
    
    return items_list


# READ ONE
@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    item = await collection.find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_helper(item)

# UPDATE
@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item: ItemCreate):
    updated = await collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": item.dict()},
        return_document=True,
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_helper(updated)

# DELETE
@router.delete("/{item_id}")
async def delete_item(item_id: str):
    result = await collection.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}
