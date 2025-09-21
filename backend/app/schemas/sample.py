from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SampleSource(str, Enum):
    SERIAL = "SERIAL"
    BLYNK = "BLYNK"
    IMPORT = "IMPORT"
    MANUAL = "MANUAL"

class SampleIn(BaseModel):
    """Input schema matching API contract (t, V, I, P, T)."""
    t: Optional[datetime] = Field(default=None, description="ISO timestamp of the measurement")
    V: float = Field(..., description="Voltage in Volts (V)")
    I: float = Field(..., description="Current in Amperes (A)")
    P: Optional[float] = Field(None, description="Power in Watts (W)")
    T: Optional[float] = Field(None, description="Temperature in Celsius (°C)")
    source: Optional[SampleSource] = Field(default=SampleSource.MANUAL)

    @validator('P', pre=True, always=True)
    def calculate_power(cls, v, values):
        if v is None and 'V' in values and 'I' in values and values['V'] is not None and values['I'] is not None:
            return values['V'] * values['I']
        return v

    class Config:
        allow_population_by_field_name = True

class SampleOut(SampleIn):
    id: int

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

class SampleImportText(BaseModel):
    text: str
    source: Optional[SampleSource] = Field(default=SampleSource.IMPORT)

class MPPResponse(BaseModel):
    Vmp: float
    Imp: float
    Pmp: float
    index: int
    t: Optional[datetime] = None
