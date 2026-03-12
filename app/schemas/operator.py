from pydantic import BaseModel, ConfigDict


class OperatorRead(BaseModel):
    id: int
    noc: str
    name: str
    region: str

    model_config = ConfigDict(from_attributes=True)
