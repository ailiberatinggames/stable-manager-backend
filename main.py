from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta, timezone # Added timezone

# --- Pydantic Models ---

class TimeHistoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time: str
    race_id: Optional[str] = None

class AugmentHistoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cpu: Optional[str] = None
    ram: Optional[str] = None
    hydraulic: Optional[str] = None

class ZedBalanceHistoryEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    balance: str

class HorseBase(BaseModel):
    name: str
    gen: Optional[str] = None
    gender: Optional[str] = None
    breed: Optional[str] = None
    colourTrait: Optional[str] = None
    overall: Optional[str] = Field(default="-")
    speed: Optional[str] = Field(default="-")
    sprint: Optional[str] = Field(default="-")
    endurance: Optional[str] = Field(default="-")
    sireName: Optional[str] = None
    sireGen: Optional[str] = None
    sireBreed: Optional[str] = None
    sireColourTrait: Optional[str] = None
    sireOverall: Optional[str] = Field(default="-")
    sireSpeed: Optional[str] = Field(default="-")
    sireSprint: Optional[str] = Field(default="-")
    sireEndurance: Optional[str] = Field(default="-")
    damName: Optional[str] = None
    damGen: Optional[str] = None
    damBreed: Optional[str] = None
    damColourTrait: Optional[str] = None
    damOverall: Optional[str] = Field(default="-")
    damSpeed: Optional[str] = Field(default="-")
    damSprint: Optional[str] = Field(default="-")
    damEndurance: Optional[str] = Field(default="-")
    races: Optional[int] = 0
    first: Optional[int] = 0
    second: Optional[int] = 0
    third: Optional[int] = 0
    cpu: Optional[str] = None
    ram: Optional[str] = None
    hydraulic: Optional[str] = None
    breedCost: Optional[str] = "0"
    strtZedBal: Optional[str] = "0"
    totalRaceNetPL: Optional[str] = "0"
    zedBalance: Optional[str] = "0"
    soldBreeds: Optional[str] = "0"
    status: Optional[str] = "active" # active, forged
    order: Optional[int] = None

    race1TimeHistory: List[TimeHistoryEntry] = Field(default_factory=list)
    race2TimeHistory: List[TimeHistoryEntry] = Field(default_factory=list)
    augmentHistory: List[AugmentHistoryEntry] = Field(default_factory=list)
    zedBalanceHistory: List[ZedBalanceHistoryEntry] = Field(default_factory=list)
    processedCsvRaceEvents: List[str] = Field(default_factory=list)

class HorseCreate(HorseBase):
    pass

class HorseResponse(HorseBase):
    id: str

class HorseUpdate(HorseBase):
    name: Optional[str] = None # Allow updating only specific fields, others from HorseBase are optional by default
    # Add other fields here if you want them to be updatable in isolation via PUT payload
    # For example:
    # gen: Optional[str] = None
    # races: Optional[int] = None
    # If a field from HorseBase is not listed here, Pydantic's exclude_unset=True in model_dump
    # will prevent it from being part of the update if not provided in the PUT request body.
    # However, HorseBase already makes most fields Optional, so an update can send any of them.
    # The main purpose of HorseUpdate is if you want a *different set* of required/optional fields
    # for updates compared to creation or base. Given HorseBase is already mostly optional,
    # HorseUpdate might not strictly need to override many fields unless to make them non-optional
    # for an update, which is unusual.
    pass

# --- FastAPI App Initialization ---
app = FastAPI(title="Stable Manager API", version="0.1.0")

# --- CORS Configuration ---
origins = [
    "http://localhost", "http://localhost:3000",
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:8001", "http://127.0.0.1:8001",
    "https://stable-manager-frontend.vercel.app",
]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# In-memory "database"
horses_db: List[HorseResponse] = [
    HorseResponse(
        id=str(uuid.uuid4()), name="Thunderbolt", gen="G1", gender="M",
        breed="Nakamoto", colourTrait="Szabo", overall="⭐️⭐️⭐️", speed="⭐️⭐️⭐️⭐️",
        sprint="⭐️⭐️", endurance="⭐️⭐️⭐️☀️", races=10, first=2, second=3, third=1,
        breedCost="0.1", strtZedBal="0.05", totalRaceNetPL="0.02", zedBalance="0.07",
        soldBreeds="0", status="active", order=0,
        sireName="Zeus", damName="Hera", cpu="Void C100", ram="Void R100", hydraulic="Void H100",
        zedBalanceHistory=[
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc) - timedelta(days=2), balance="0.05"),
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc) - timedelta(days=1), balance="0.07")
        ]
    ),
    HorseResponse(
        id=str(uuid.uuid4()), name="Lightning", gen="G2", gender="F",
        breed="Finney", colourTrait="Buterin", overall="⭐️⭐️⭐️⭐️", speed="⭐️⭐️⭐️",
        sprint="⭐️⭐️⭐️⭐️", endurance="⭐️⭐️⭐️", races=5, first=1, second=1, third=0,
        breedCost="0.05", strtZedBal="0.025", totalRaceNetPL="-0.01", zedBalance="0.015",
        soldBreeds="0", status="active", order=1,
        sireName="Bolt", damName="Flash", cpu="Crimson C", ram="Crimson R", hydraulic="Crimson H",
        zedBalanceHistory=[
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc) - timedelta(days=2), balance="0.025"),
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc) - timedelta(days=1), balance="0.015")
        ]
    )
]

def get_next_order_value() -> int:
    if not horses_db: return 0
    valid_orders = [horse.order for horse in horses_db if horse.order is not None and horse.status != "forged"]
    if not valid_orders: return 0
    return max(valid_orders) + 1

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stable Manager API!"}

@app.get("/api/horses", response_model=List[HorseResponse])
async def get_horses_endpoint():
    print(f"GET /api/horses: Returning horses from in-memory DB (excluding forged).")
    active_horses = [horse for horse in horses_db if horse.status != "forged"]
    return active_horses

# --- THIS IS THE NEWLY ADDED ENDPOINT ---
@app.get("/api/horses/{horse_id}", response_model=HorseResponse)
async def get_horse_detail(horse_id: str):
    print(f"GET /api/horses/{horse_id}: Attempting to retrieve horse.")
    for horse in horses_db:
        if horse.id == horse_id:
            if horse.status == "forged":
                print(f"GET /api/horses/{horse_id}: Horse found but is forged. Denying access.")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horse not found or is forged")
            print(f"GET /api/horses/{horse_id}: Horse '{horse.name}' found.")
            return horse
    print(f"GET /api/horses/{horse_id}: Horse not found in database.")
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Horse not found")
# --- END OF NEWLY ADDED ENDPOINT ---

@app.post("/api/horses", response_model=HorseResponse, status_code=status.HTTP_201_CREATED)
async def create_horse(horse_payload: HorseCreate):
    print(f"POST /api/horses: Received payload to create horse: {horse_payload.model_dump_json(indent=2)}")

    new_horse_dict = horse_payload.model_dump()
    new_horse_id = str(uuid.uuid4())
    new_horse_dict["id"] = new_horse_id

    if new_horse_dict.get("order") is None:
         new_horse_dict["order"] = get_next_order_value()

    try:
        breed_cost_num = float(new_horse_dict.get("breedCost", "0"))
    except ValueError:
        breed_cost_num = 0.0

    new_horse_dict["strtZedBal"] = f"{breed_cost_num / 2:.3f}".rstrip('0').rstrip('.')
    new_horse_dict["totalRaceNetPL"] = "0"
    new_horse_dict["zedBalance"] = new_horse_dict["strtZedBal"]

    current_zed_history_list_of_dicts = new_horse_dict.get("zedBalanceHistory", [])
    if not isinstance(current_zed_history_list_of_dicts, list):
        current_zed_history_list_of_dicts = []

    needs_initial_balance_entry = True
    if current_zed_history_list_of_dicts:
        if any(entry.get("balance") == new_horse_dict["zedBalance"] for entry in current_zed_history_list_of_dicts):
            needs_initial_balance_entry = False

    if needs_initial_balance_entry and new_horse_dict["zedBalance"] != "0":
        current_zed_history_list_of_dicts.append(
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc), balance=new_horse_dict["zedBalance"]).model_dump()
        )
    new_horse_dict["zedBalanceHistory"] = current_zed_history_list_of_dicts

    for history_key in ["race1TimeHistory", "race2TimeHistory", "augmentHistory"]:
        if not isinstance(new_horse_dict.get(history_key), list):
            new_horse_dict[history_key] = []

    try:
        horse_to_add = HorseResponse(**new_horse_dict)
    except Exception as e:
        print(f"POST /api/horses: Error creating HorseResponse from dict: {e}")
        print(f"POST /api/horses: Problematic dict: {new_horse_dict}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing new horse data.")

    horses_db.append(horse_to_add)
    print(f"POST /api/horses: Horse '{horse_to_add.name}' created with ID {horse_to_add.id}.")
    return horse_to_add

@app.put("/api/horses/{horse_id}", response_model=HorseResponse)
async def update_horse(horse_id: str, horse_payload: HorseUpdate):
    print(f"PUT /api/horses/{horse_id}: Attempting to update horse.")
    print(f"PUT /api/horses/{horse_id}: Received payload: {horse_payload.model_dump_json(indent=2, exclude_unset=True)}")

    horse_index = -1
    for index, h_db_item in enumerate(horses_db):
        if h_db_item.id == horse_id:
            horse_index = index
            break

    if horse_index == -1 or horses_db[horse_index].status == "forged":
        print(f"PUT /api/horses/{horse_id}: Horse not found or is forged.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Horse with ID {horse_id} not found or is forged")

    original_horse_model = horses_db[horse_index] # This is a HorseResponse instance
    update_data_dict = horse_payload.model_dump(exclude_unset=True) # This is a dict

    print(f"PUT /api/horses/{horse_id}: Data to apply (exclude_unset=True): {update_data_dict}")

    # Create a new model instance with updates. Pydantic handles nested model conversion if update_data_dict is structured correctly.
    updated_horse_model = original_horse_model.model_copy(update=update_data_dict)

    # Ensure history lists within updated_horse_model are lists of Pydantic models.
    # model_copy should handle this if update_data_dict values for history lists are lists of dicts.
    # This is a defensive step or if direct manipulation of history lists happens before this.
    # It's important that updated_horse_model maintains lists of Pydantic models internally.
    def ensure_pydantic_history_list(history_list, entry_model_class):
        if not isinstance(history_list, list): return []
        return [entry_model_class(**item) if isinstance(item, dict) else item for item in history_list]

    if 'race1TimeHistory' in update_data_dict:
        updated_horse_model.race1TimeHistory = ensure_pydantic_history_list(updated_horse_model.race1TimeHistory, TimeHistoryEntry)
    if 'race2TimeHistory' in update_data_dict:
        updated_horse_model.race2TimeHistory = ensure_pydantic_history_list(updated_horse_model.race2TimeHistory, TimeHistoryEntry)
    if 'augmentHistory' in update_data_dict: # This list might be appended to later, so ensure it's models
        updated_horse_model.augmentHistory = ensure_pydantic_history_list(updated_horse_model.augmentHistory, AugmentHistoryEntry)
    if 'zedBalanceHistory' in update_data_dict: # This list might be appended to later
        updated_horse_model.zedBalanceHistory = ensure_pydantic_history_list(updated_horse_model.zedBalanceHistory, ZedBalanceHistoryEntry)


    if "breedCost" in update_data_dict:
        try:
            breed_cost_num = float(updated_horse_model.breedCost if updated_horse_model.breedCost is not None else "0")
            updated_horse_model.strtZedBal = f"{breed_cost_num / 2:.3f}".rstrip('0').rstrip('.')
            if "zedBalance" not in update_data_dict: # Recalculate zedBalance if not explicitly provided
                strt_bal_num = float(updated_horse_model.strtZedBal)
                total_pl_num = float(updated_horse_model.totalRaceNetPL or "0")
                updated_horse_model.zedBalance = f"{strt_bal_num + total_pl_num:.3f}".rstrip('0').rstrip('.')
        except ValueError:
            print(f"PUT /api/horses/{horse_id}: Invalid breedCost during update: {updated_horse_model.breedCost}")
            # Potentially revert or raise error, for now, it might keep the old value or an invalid new one

    if "soldBreeds" in update_data_dict and update_data_dict["soldBreeds"] is not None:
        try:
            original_sold_val_from_db = float(original_horse_model.soldBreeds or "0")
            # Assuming soldBreeds in payload is the *additional* amount, not the new total
            additional_sold_num_from_payload = float(update_data_dict["soldBreeds"] or "0")
            updated_horse_model.soldBreeds = str(original_sold_val_from_db + additional_sold_num_from_payload)
        except ValueError:
            # Keep original if payload value is bad
            updated_horse_model.soldBreeds = original_horse_model.soldBreeds
            print(f"PUT /api/horses/{horse_id}: Invalid soldBreeds value in payload: {update_data_dict['soldBreeds']}")


    if any(key in update_data_dict for key in ["cpu", "ram", "hydraulic"]):
        if (original_horse_model.cpu != updated_horse_model.cpu or
            original_horse_model.ram != updated_horse_model.ram or
            original_horse_model.hydraulic != updated_horse_model.hydraulic):

            # Ensure augmentHistory is a list of AugmentHistoryEntry models before appending
            temp_augment_history = ensure_pydantic_history_list(list(updated_horse_model.augmentHistory), AugmentHistoryEntry) # list() for a mutable copy

            new_augment_entry = AugmentHistoryEntry(
                timestamp=datetime.now(timezone.utc),
                cpu=updated_horse_model.cpu,
                ram=updated_horse_model.ram,
                hydraulic=updated_horse_model.hydraulic
            )
            temp_augment_history.append(new_augment_entry)
            updated_horse_model.augmentHistory = temp_augment_history

    if "zedBalance" in update_data_dict and updated_horse_model.zedBalance is not None:
        current_balance_str_payload = str(updated_horse_model.zedBalance)

        # Ensure zedBalanceHistory is a list of ZedBalanceHistoryEntry models before appending
        temp_zed_history = ensure_pydantic_history_list(list(updated_horse_model.zedBalanceHistory), ZedBalanceHistoryEntry) # list() for a mutable copy

        last_zed_entry_model = temp_zed_history[-1] if temp_zed_history else None

        add_new_history_entry = True
        if last_zed_entry_model and last_zed_entry_model.balance == current_balance_str_payload:
            add_new_history_entry = False

        if add_new_history_entry:
            new_hist_timestamp = datetime.now(timezone.utc)
            if last_zed_entry_model and last_zed_entry_model.timestamp >= new_hist_timestamp:
                new_hist_timestamp = last_zed_entry_model.timestamp + timedelta(milliseconds=1)

            new_balance_entry = ZedBalanceHistoryEntry(
                timestamp=new_hist_timestamp,
                balance=current_balance_str_payload
            )
            temp_zed_history.append(new_balance_entry)
            updated_horse_model.zedBalanceHistory = temp_zed_history

    horses_db[horse_index] = updated_horse_model
    print(f"PUT /api/horses/{horse_id}: Horse updated successfully.")
    return updated_horse_model

@app.delete("/api/horses/{horse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse(horse_id: str):
    print(f"DELETE /api/horses/{horse_id}: Attempting to 'forge' horse.")
    horse_index = -1
    for index, h_db_item in enumerate(horses_db):
        if h_db_item.id == horse_id:
            horse_index = index
            break

    if horse_index == -1:
        print(f"DELETE /api/horses/{horse_id}: Horse not found for forging.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Horse with ID {horse_id} not found")

    if horses_db[horse_index].status == "forged":
        print(f"DELETE /api/horses/{horse_id}: Horse '{horses_db[horse_index].name}' is already forged.")
        return # Return 204 as it's idempotent

    horses_db[horse_index].status = "forged"
    print(f"DELETE /api/horses/{horse_id}: Horse '{horses_db[horse_index].name}' marked as forged.")
    # No body content for 204