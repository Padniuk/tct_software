from typing import Tuple, List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    output_folder: str
    dut_name: str
    logging_level: str
    current_compliance_amperes: float
    device_center: Tuple[float, float, float]
    laser_dac: int
    laser_frequency: int
    voltages: List[float]
    x_span: float
    y_span: float
    step_xy: float
    rotation_angle_deg: float
    n_triggers_per_position: int
    remove_pads: Optional[List[int]] = None
    acquire_channels: List[int]
    trigger_delay_scope: Optional[int] = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()
