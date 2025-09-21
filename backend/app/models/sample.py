from sqlalchemy import Column, Integer, Float, DateTime, String, func, Index
from sqlalchemy import Enum as SAEnum
from datetime import datetime
from enum import Enum

from ..database import Base

class SampleSource(str, Enum):
    SERIAL = "SERIAL"
    BLYNK = "BLYNK"
    IMPORT = "IMPORT"
    MANUAL = "MANUAL"

class Sample(Base):
    """Database model for storing solar panel measurement samples."""
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=False), default=datetime.utcnow, index=True)
    voltage = Column(Float, nullable=False)  # in Volts
    current = Column(Float, nullable=False)  # in Amperes
    power = Column(Float, nullable=True)     # in Watts (can be calculated as V*I if not provided)
    temperature = Column(Float, nullable=True)  # in °C
    source = Column(
        SAEnum(SampleSource, name="sample_source"),
        nullable=False,
        default=SampleSource.MANUAL
    )

    # Add a composite index on (timestamp, voltage, current) to speed up queries
    __table_args__ = (
        Index('idx_sample_composite', 'timestamp', 'voltage', 'current'),
    )

    def calculate_power(self):
        """Calculate power if not provided."""
        if self.power is None and self.voltage is not None and self.current is not None:
            self.power = self.voltage * self.current
        return self.power

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "t": self.timestamp.isoformat() if self.timestamp else None,
            "V": self.voltage,
            "I": self.current,
            "P": self.calculate_power(),
            "T": self.temperature,
            "source": self.source.value if isinstance(self.source, Enum) else self.source
        }
