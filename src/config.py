import json
import toml
import os
from typing import TypedDict, Literal, Any
from util import AssetData
import keyring

CONFIG_PATH = "asphalt.toml"
LOCK_PATH = "asphalt.lock"

INITIAL_LOCK_CONFIG = {
	"audio": {},
	"image": {},
	"material": {},
	"mesh": {},
	"model": {},
	"particle": {},
	"animation": {},
}

ROBLOX_ASSET_KEY_CREDENTIAL_NAME = "AsphaltAssetKey"
ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME = os.path.abspath("src")
INITIAL_CONFIG = {
	"build": {
		"dir_path": "lib",
		"module_path": "src/Shared/Library.luau",
		"efficient_build_includes_all_local_files": True,
		"asset_usage_audit_script_directories": ["src"],
		"publish": {
			"publish_to_group": True,
			"entity_id": -1,
		}
	},
	"media": {
		"audio": {
			"sources": [],
		},
		"image": {
			"sources": [],
		},
		"material": {
			"sources": [],
		},
		"mesh": {
			"sources": [],
		},
		"model": {
			"sources": [],
		},
		"particle": {
			"sources": [],
		},
		"animation": {
			"sources": [],
		},
	}
}

MediaType = Literal["audio", "image", "mesh", "animation", "model", "material", "particle"]

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

def get_config_data() -> ConfigData:
	with open(CONFIG_PATH, "r") as file:
		file_content = file.read()
		file_data = toml.loads(file_content)
		for media_type, media_config in file_data["media"].items():
			out = []
			for v in media_config["sources"]:
				out.append(os.path.abspath(v).replace("\\", "/"))
			media_config["sources"] = out
			
		return file_data


def init():
	assert not os.path.exists(CONFIG_PATH), "asphalt is already initialized"
	with open(LOCK_PATH, "w") as file:
		file.write(json.dumps(INITIAL_LOCK_CONFIG))
	
	with open(CONFIG_PATH, "w") as file:
		file.write(toml.dumps(INITIAL_CONFIG))


def get_asset_auth_key() -> str:
	return keyring.get_password(ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME)

def get_lock_data() -> LockData:
	with open(LOCK_PATH, "r") as file:
		return json.loads(file.read())

def set_lock_data(lock_data: LockData):
	with open(LOCK_PATH, "w") as file:
		file.write(json.dumps(lock_data,indent=5))