-- Constants
local ARGS = {...}
local MODEL_FILE_PATH = ARGS[1]
local FOLDER_CLASS_NAME = ARGS[2]
local OUT_DIRECTORY_PATH = ARGS[3]
local FILE_EXT = ARGS[4]


local instList = remodel.readModelFile(MODEL_FILE_PATH)

function extractInstance(instances, path)
	for i, inst in ipairs(instances) do
		local instPath = path.."/"..inst.Name
		if inst.ClassName == FOLDER_CLASS_NAME then
			remodel.createDirAll(instPath)
			extractInstance(inst:GetChildren(), instPath)
		else
			remodel.writeModelFile(instPath.."."..FILE_EXT, inst)
		end
	end
end

if #instList > 1 then
	extractInstance(instList, OUT_DIRECTORY_PATH)
	remodel.removeFile(MODEL_FILE_PATH)
else
	local inst = instList[1]
	if inst.ClassName == FOLDER_CLASS_NAME then
		extractInstance(inst:GetChildren(), OUT_DIRECTORY_PATH)
		remodel.removeFile(MODEL_FILE_PATH)
	end
end