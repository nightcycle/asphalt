from _typeshed import Incomplete
from typing import Any, TypedDict

RemodelType: Incomplete

class AssetData(TypedDict):
    source: str
    hash: str
    asset_id: str | None
    operation_id: str | None
    update_needed: bool
    is_used: bool

class RemodelValue(TypedDict):
    type: RemodelType
    value: Any

def get_file_hash(path: str): ...
def get_asset_url_from_id(asset_id: int): ...
def get_rbxmk_path() -> str: ...
def get_remodel_path() -> str: ...
def convert_to_roblox_ext(file_path: str, goal_ext: str, is_model: bool) -> str: ...
def convert_to_rbxl(file_path: str) -> str: ...
def convert_to_rbxlx(file_path: str) -> str: ...
def convert_to_rbxmx(file_path: str) -> str: ...
def convert_to_rbxm(file_path: str) -> str: ...
def group_directory(directory_path: str, folder_class_name: str = ..., ext: str = ...): ...
def expand_into_directory(model_file: str, folder_class_name: str = ...): ...
def write_model_asset(build_path: str, class_name: str, inst_config: RemodelValue): ...
def decode_tags(bin_str: str) -> list[str]: ...
def encode_tags(tags: list[str]) -> str: ...
