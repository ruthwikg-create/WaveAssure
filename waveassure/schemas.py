from __future__ import annotations
from typing import Literal
import math
from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_UNITS = {"ECG": {"mV"}, "PPG": {"a.u.", "NU"}, "ABP": {"mmHg"}}
MAX_SAMPLES = 100_000

class Channel(BaseModel):
    kind: Literal["ECG", "PPG", "ABP"]
    name: str = Field(default="", max_length=24)
    unit: str
    samples: list[float | None] = Field(min_length=100, max_length=MAX_SAMPLES)

    @model_validator(mode="after")
    def check_units(self):
        if not self.name:
            self.name = self.kind
        if not self.name.isprintable() or self.name.strip() != self.name:
            raise ValueError("Invalid channel name")
        if self.unit not in ALLOWED_UNITS[self.kind]:
            raise ValueError(f"{self.kind} must have one of {sorted(ALLOWED_UNITS[self.kind])}")
        if any(v is not None and not math.isfinite(v) for v in self.samples):
            raise ValueError("Only finite values or null (missing samples) accepted")
        return self

class RecordCreate(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    sample_rate_hz: float = Field(ge=50, le=1000)
    channels: list[Channel] = Field(min_length=1, max_length=8)
    origin: Literal["synthetic", "local_csv_unverified", "wfdb_research"]
    source_reference: str = Field(default="", max_length=240)
    reference_label: Literal["True", "False", "Unlabeled"] = "Unlabeled"
    # Time in seconds relative to recording start. Never inferred from waveform shape.
    alarm_time_s: float | None = Field(default=None, ge=0, le=600)
    alarm_time_source: Literal['dataset_annotation', 'user_annotation_unverified'] | None = None

    @model_validator(mode="after")
    def consistent(self):
        lengths = {len(c.samples) for c in self.channels}
        names = [c.name for c in self.channels]
        if len(lengths) != 1 or len(names) != len(set(names)):
            raise ValueError("All channels must have same length and unique name")
        duration = len(self.channels[0].samples) / self.sample_rate_hz
        if (self.alarm_time_s is None) != (self.alarm_time_source is None):
            raise ValueError("An alarm time requires an annotation source")
        if self.alarm_time_s is not None and self.alarm_time_s > duration:
            raise ValueError("Alarm time is outside the recording")
        if duration > 600:
            raise ValueError("Maximum recording duration is 600 seconds")
        return self

class FaultRequest(BaseModel):
    kind: Literal["dropout", "baseline_drift", "mains_interference", "clipping"]
    target: str = Field(min_length=1, max_length=24)
    severity: float = Field(default=0.5, ge=0.1, le=1.0)

class CSVChannelMap(BaseModel):
    column: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=24)
    kind: Literal['ECG', 'PPG', 'ABP']
    unit: str

class CSVImport(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    csv_text: str = Field(min_length=1, max_length=8_000_000)
    time_column: str = 'time_s'
    time_unit: Literal['s', 'ms'] = 's'
    channel_mapping: list[CSVChannelMap] | None = None
    alarm_time_s: float | None = Field(default=None, ge=0, le=600)
