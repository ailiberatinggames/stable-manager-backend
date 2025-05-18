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
    status: Optional[str] = "active"
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
    name: Optional[str] = None 
    pass

# --- FastAPI App Initialization ---
app = FastAPI(title="Stable Manager API", version="0.1.0")

# --- CORS Configuration ---
origins = [
    "http://localhost", "http://localhost:3000",
    "http://localhost:5500", "http://127.0.0.1:5500",
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
    valid_orders = [horse.order for horse in horses_db if horse.order is not None and horse.status != "forged"] # Consider active horses for order
    if not valid_orders: return 0
    return max(valid_orders) + 1

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Stable Manager API!"}

@app.get("/api/horses", response_model=List[HorseResponse])
async def get_horses_endpoint(): 
    print(f"Returning horses from in-memory DB (excluding forged).")
    active_horses = [horse for horse in horses_db if horse.status != "forged"]
    return active_horses

@app.post("/api/horses", response_model=HorseResponse, status_code=status.HTTP_201_CREATED)
async def create_horse(horse_payload: HorseCreate): 
    print(f"Received payload to create horse: {horse_payload.model_dump_json(indent=2)}")
    
    # horse_payload is a HorseCreate Pydantic model.
    # Its history lists (e.g., horse_payload.zedBalanceHistory) are List[ZedBalanceHistoryEntry]
    
    new_horse_dict = horse_payload.model_dump() # Convert the whole payload to a dict for manipulation
    
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

    # --- Corrected zedBalanceHistory handling ---
    # new_horse_dict["zedBalanceHistory"] currently holds a list of DICTS from model_dump()
    # or an empty list if none was provided in payload (due to Pydantic default_factory on HorseBase)
    
    # Ensure current_zed_history_list_of_dicts is a list of dicts.
    # new_horse_dict["zedBalanceHistory"] should already be this if default_factory worked or payload was provided.
    current_zed_history_list_of_dicts = new_horse_dict.get("zedBalanceHistory", [])
    if not isinstance(current_zed_history_list_of_dicts, list): # Defensive check
        current_zed_history_list_of_dicts = []

    # Check if an entry with the current zedBalance already exists
    needs_initial_balance_entry = True
    if current_zed_history_list_of_dicts: # If history from payload is not empty
        # Check if any existing entry (which are dicts here) matches the new calculated zedBalance
        if any(entry.get("balance") == new_horse_dict["zedBalance"] for entry in current_zed_history_list_of_dicts):
            needs_initial_balance_entry = False
    
    if needs_initial_balance_entry and new_horse_dict["zedBalance"] != "0": # Also check it's not "0" for adding
        current_zed_history_list_of_dicts.append(
            ZedBalanceHistoryEntry(timestamp=datetime.now(timezone.utc), balance=new_horse_dict["zedBalance"]).model_dump()
        )
    new_horse_dict["zedBalanceHistory"] = current_zed_history_list_of_dicts
    # --- End of corrected zedBalanceHistory handling ---
    
    # Ensure other history lists are lists of dicts (Pydantic's model_dump handles this for nested models)
    for history_key in ["race1TimeHistory", "race2TimeHistory", "augmentHistory"]:
        if not isinstance(new_horse_dict.get(history_key), list): # Defensive
            new_horse_dict[history_key] = []


    try:
        # Create the final HorseResponse object using the processed dictionary.
        # Pydantic will validate and convert items in history lists if they match the sub-model types.
        horse_to_add = HorseResponse(**new_horse_dict)
    except Exception as e:
        print(f"Error creating HorseResponse from dict during POST: {e}")
        print(f"Problematic dict for POST: {new_horse_dict}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing new horse data.")

    horses_db.append(horse_to_add)
    print(f"Horse '{horse_to_add.name}' created with ID {horse_to_add.id}.")
    return horse_to_add

@app.put("/api/horses/{horse_id}", response_model=HorseResponse)
async def update_horse(horse_id: str, horse_payload: HorseUpdate):
    print(f"Attempting to update horse with ID: {horse_id}")
    print(f"Received payload for update: {horse_payload.model_dump_json(indent=2, exclude_unset=True)}")

    # --- THIS PART IS CRUCIAL AND WAS MISSING FROM THE FOCUSED SNIPPET ---
    horse_index = -1 
    for index, h_db_item in enumerate(horses_db):
        if h_db_item.id == horse_id:
            horse_index = index
            break
    # --- END OF CRUCIAL PART ---
    
    if horse_index == -1 or horses_db[horse_index].status == "forged": # Cannot update forged horse
        print(f"Horse with ID {horse_id} not found or is forged.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Horse with ID {horse_id} not found or is forged")

    original_horse_model = horses_db[horse_index]
    update_data_dict = horse_payload.model_dump(exclude_unset=True)
    
    print(f"Data to apply for update (exclude_unset=True): {update_data_dict}")

    updated_horse_model = original_horse_model.model_copy(update=update_data_dict)

    # Ensure nested history lists are lists of Pydantic models after model_copy
    try:
        if 'race1TimeHistory' in update_data_dict and isinstance(updated_horse_model.race1TimeHistory, list):
            updated_horse_model.race1TimeHistory = [TimeHistoryEntry(**item) if isinstance(item, dict) else item for item in updated_horse_model.race1TimeHistory]
        if 'race2TimeHistory' in update_data_dict and isinstance(updated_horse_model.race2TimeHistory, list):
            updated_horse_model.race2TimeHistory = [TimeHistoryEntry(**item) if isinstance(item, dict) else item for item in updated_horse_model.race2TimeHistory]
        if 'augmentHistory' in update_data_dict and isinstance(updated_horse_model.augmentHistory, list):
            updated_horse_model.augmentHistory = [AugmentHistoryEntry(**item) if isinstance(item, dict) else item for item in updated_horse_model.augmentHistory]
        if 'zedBalanceHistory' in update_data_dict and isinstance(updated_horse_model.zedBalanceHistory, list):
            updated_horse_model.zedBalanceHistory = [ZedBalanceHistoryEntry(**item) if isinstance(item, dict) else item for item in updated_horse_model.zedBalanceHistory]
    except Exception as e:
        print(f"Warning: Error re-parsing history lists from payload during update: {e}")

    # ... (breedCost logic) ...
    if "breedCost" in update_data_dict:
        try:
            breed_cost_num = float(updated_horse_model.breedCost)
            updated_horse_model.strtZedBal = f"{breed_cost_num / 2:.3f}".rstrip('0').rstrip('.')
            if "zedBalance" not in update_data_dict: 
                strt_bal_num = float(updated_horse_model.strtZedBal)
                total_pl_num = float(updated_horse_model.totalRaceNetPL or "0")
                updated_horse_model.zedBalance = f"{strt_bal_num + total_pl_num:.3f}".rstrip('0').rstrip('.')
        except ValueError:
            print(f"Invalid breedCost during update: {updated_horse_model.breedCost}")

    # ... (soldBreeds logic) ...
    if "soldBreeds" in update_data_dict and update_data_dict["soldBreeds"] is not None:
        try:
            original_sold_val_from_db = float(original_horse_model.soldBreeds or "0")
            additional_sold_num_from_payload = float(update_data_dict["soldBreeds"] or "0")
            updated_horse_model.soldBreeds = str(original_sold_val_from_db + additional_sold_num_from_payload)
        except ValueError:
            updated_horse_model.soldBreeds = original_horse_model.soldBreeds
            
    # ... (augmentHistory update logic - now appends Pydantic models) ...
    if any(key in update_data_dict for key in ["cpu", "ram", "hydraulic"]):
        if (original_horse_model.cpu != updated_horse_model.cpu or
            original_horse_model.ram != updated_horse_model.ram or
            original_horse_model.hydraulic != updated_horse_model.hydraulic):
            
            # Ensure mutable list of Pydantic models
            temp_augment_history = [entry if isinstance(entry, AugmentHistoryEntry) else AugmentHistoryEntry(**entry) for entry in updated_horse_model.augmentHistory]
            
            new_augment_entry = AugmentHistoryEntry(
                timestamp=datetime.now(timezone.utc), 
                cpu=updated_horse_model.cpu, 
                ram=updated_horse_model.ram, 
                hydraulic=updated_horse_model.hydraulic
            )
            temp_augment_history.append(new_augment_entry)
            updated_horse_model.augmentHistory = temp_augment_history

    # ... (zedBalanceHistory update logic - now appends Pydantic models) ...
    if "zedBalance" in update_data_dict and updated_horse_model.zedBalance is not None:
        current_balance_str_payload = str(updated_horse_model.zedBalance)
        
        # Ensure mutable list of Pydantic models
        temp_zed_history = [entry if isinstance(entry, ZedBalanceHistoryEntry) else ZedBalanceHistoryEntry(**entry) for entry in updated_horse_model.zedBalanceHistory]
        
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
    print(f"Horse with ID {horse_id} updated successfully. New data: {updated_horse_model.model_dump_json(indent=2)}")
    return updated_horse_model

@app.delete("/api/horses/{horse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_horse(horse_id: str):
    print(f"Attempting to 'forge' horse with ID: {horse_id}")
    horse_index = -1
    for index, h_db_item in enumerate(horses_db):
        if h_db_item.id == horse_id:
            horse_index = index
            break
    
    if horse_index == -1:
        print(f"Horse with ID {horse_id} not found for forging.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Horse with ID {horse_id} not found")

    if horses_db[horse_index].status == "forged":
        print(f"Horse '{horses_db[horse_index].name}' with ID {horse_id} is already forged.")
        return 

    horses_db[horse_index].status = "forged"
    print(f"Horse '{horses_db[horse_index].name}' with ID {horse_id} marked as forged.")
    
    return