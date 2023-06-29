import json
import toml
import os
import keyring
from copy import deepcopy
from typing import TypedDict, Literal, Any, Union, MutableMapping
from src.util import AssetData

CONFIG_PATH = "asphalt.toml"
LOCK_PATH = "asphalt.cache"
ASPHALT_LIBRARY_PATH = ".asphalt-libraries"

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
		"libraries": {},
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
	dir_path: str | None
	compression_directory_instance: str | None
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
	libraries: dict[str, str]
	efficient_build_includes_all_local_files: bool
	asset_usage_audit_script_directories: list[str]
	publish: PublishConfigData

class ConfigData(TypedDict):
	build: BuildConfigData
	media: MediaDirectoryConfig

def get_library_local_path(github_repo_path: str) -> str:
	return ASPHALT_LIBRARY_PATH+"/"+github_repo_path.replace(".", "-").replace("/","_")

def get_config_data() -> ConfigData:
	with open(CONFIG_PATH, "r") as file:
		file_content = file.read()
		file_data: Any = toml.loads(file_content)
		for media_type, media_config in file_data["media"].items():
			out = []
			for v in media_config["sources"]:
				v = v.replace("\\", "/")
				start_key = v.split("/")[0]
				if start_key in file_data["build"]["libraries"]:
					repo_path = file_data["build"]["libraries"][start_key]
					local_path = get_library_local_path(repo_path)
					v = "/".join([local_path] + v.split("/")[1:])
				out.append(v)
			print("OUT", out)
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
	
	import_file_paths = []
	for dir_name in os.listdir(ASPHALT_LIBRARY_PATH):
		import_file_paths.append(ASPHALT_LIBRARY_PATH+"/"+dir_name+"/"+LOCK_PATH)

	for file_path in import_file_paths:
		with open(file_path, "r") as import_file:
			import_data: dict[MediaType, dict[str, AssetData]] = json.loads(import_file.read())
			for media_type, asset_registry in import_data.items():
				if not media_type in lock_data:
					lock_data[media_type] = {}

				for asset_path, asset_data in asset_registry.items():
					asset_data["source"] = ASPHALT_LIBRARY_PATH+"/"+dir_name + "/src/" + media_type + asset_data["source"].split(media_type)[1]
					lock_data[media_type][asset_path] = asset_data

	return untyped_lock_data

def get_lock_data() -> LockData:

	with open(LOCK_PATH, "r") as file:	
		return json.loads(file.read())

def set_lock_data(lock_data: LockData):
	with open(LOCK_PATH, "w") as file:
		file.write(json.dumps(lock_data,indent=5))