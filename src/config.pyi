from _typeshed import Incomplete
from typing import TypedDict
from .util import AssetData as AssetData

CONFIG_PATH: str
LOCK_PATH: str
AUTH_LOCK_PATH: str
INITIAL_LOCK_CONFIG: Incomplete
ROBLOX_ASSET_KEY_CREDENTIAL_NAME: str
ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME: Incomplete
INITIAL_CONFIG: Incomplete
MediaType: Incomplete

class LockData(TypedDict):
    audio: dict[str, AssetData]
    image: dict[str, AssetData]
    material: dict[str, AssetData]
    mesh: dict[str, AssetData]
    model: dict[str, AssetData]
    particle: dict[str, AssetData]
    animation: dict[str, AssetData]

class MediaConfig(TypedDict):
    sources: list[str]

class MediaDirectoryConfig(TypedDict):
    audio: MediaConfig
    image: MediaConfig
    material: MediaConfig
    mesh: MediaConfig
    model: MediaConfig
    particle: MediaConfig
    animation: MediaConfig

class PublishConfigData(TypedDict):
    publish_to_group: bool
    entity_id: int

class BuildConfigData(TypedDict):
    dir_path: str
    module_path: str
    efficient_build_includes_all_local_files: bool
    asset_usage_audit_script_directories: list[str]
    publish: PublishConfigData

class ConfigData(TypedDict):
    build: BuildConfigData
    media: MediaDirectoryConfig

def get_config_data() -> ConfigData: ...
def init() -> None: ...
def get_asset_auth_key() -> str: ...
def get_lock_data() -> LockData: ...
def set_lock_data(lock_data: LockData): ...
