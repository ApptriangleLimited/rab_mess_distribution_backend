from pydantic import BaseModel, ConfigDict


class BoroKhanaPutIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    on: bool
