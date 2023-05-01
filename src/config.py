import json
import toml
import os
import keyring
from copy import deepcopy
from typing import TypedDict, Literal, Any, Union, MutableMapping
from src.util import AssetData

CONFIG_PATH = "asphalt.toml"
LOCK_PATH = "asphalt.lock"

INITIAL_LOCK_CONFIG: dict = {
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
		"importable_lock_files": [],
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
	importable_lock_files: list[str]
	publish: PublishConfigData

class ConfigData(TypedDict):
	build: BuildConfigData
	media: MediaDirectoryConfig

def get_config_data() -> ConfigData:
	with open(CONFIG_PATH, "r") as file:
		file_content = file.read()
		file_data: Any = toml.loads(file_content)
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
	auth = keyring.get_password(ROBLOX_ASSET_KEY_CREDENTIAL_NAME, ROBLOX_ASSET_KEY_CREDENTIAL_USERNAME)
	assert auth, "not authorized, run \"asphalt auth\" and paste your roblox asset api key"
	return auth

def apply_import_data(lock_data: LockData) -> LockData:
	untyped_lock_data: Any = lock_data
	mutable_lock_data: MutableMapping[Any, Any] = untyped_lock_data
	config_data = get_config_data()
	
	import_file_paths = config_data["build"]["importable_lock_files"]

	for file_path in import_file_paths:
		with open(file_path, "r") as import_file:
			import_data: dict[MediaType, dict[str, AssetData]] = json.loads(import_file.read())
			for media_type, asset_registry in import_data.items():
				if not media_type in lock_data:
					lock_data[media_type] = {}

				for asset_path, asset_data in asset_registry.items():
					
					# current_asset_id: None | int = None
					# current_hash: None | str = None
					# if "asset_id" in asset_data:
					# 	current_asset_id = asset_data["asset_id"]
					# 	current_hash = asset_data["hash"]
					
					# prior_asset_id: None | int = None
					# prior_hash: None | str = None

					# if asset_path in lock_data[media_type]:
					# 	prior_asset_data: AssetData = lock_data[media_type][asset_path]
						
					# 	if "asset_id" in prior_asset_data:
					# 		prior_asset_id = prior_asset_data["asset_id"]
						
					# 	if "hash" in prior_asset_data:
					# 		prior_hash = prior_asset_data["hash"]

					# if prior_asset_id == None and current_asset_id != None:
					# 	asset_data["update_needed"] = False
					# else:
					# 	if current_asset_id == None:
					# 		asset_data["update_needed"] = True
					# 	else:
					# 		asset_data["update_needed"] = False
					lock_data[media_type][asset_path] = asset_data

	return untyped_lock_data

def get_lock_data() -> LockData:

	with open(LOCK_PATH, "r") as file:	
		return json.loads(file.read())

def set_lock_data(lock_data: LockData):
	with open(LOCK_PATH, "w") as file:
		file.write(json.dumps(lock_data,indent=5))