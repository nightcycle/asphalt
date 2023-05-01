-- Constants
local ARGS = {...}
local DIRECTORY_FILE_PATH = ARGS[1]
local FOLDER_CLASS_NAME = ARGS[2]
local FILE_EXT = ARGS[3]

-- for some reason string.split doesn't work, so here it is rewritten
function stringSplit(str, delimiter)
	local result = {}
	local from = 1
	local delim_from, delim_to = string.find(str, delimiter, from)

	while delim_from do
		table.insert(result, string.sub(str, from, delim_from - 1))
		from = delim_to + 1
		delim_from, delim_to = string.find(str, delimiter, from)
	end

	table.insert(result, string.sub(str, from))

	return result
end

function groupDirectory(directoryPath)
	assert(remodel.isDir(directoryPath), "path is not directory: "..directoryPath)
	
	local folderInst = Instance.new(FOLDER_CLASS_NAME)
	local keys = stringSplit(directoryPath, "/")
	folderInst.Name = keys[#keys]		

	for i, name in ipairs(remodel.readDir(directoryPath)) do

		local path = directoryPath .. "/" ..name

		if remodel.isFile(path) then

			local children = remodel.readModelFile(path)
			for j, child in ipairs(children) do
				child.Parent = folderInst

				-- why would you parent it under a sound group if you weren't going to set it
				if child.ClassName == "Sound" and FOLDER_CLASS_NAME == "SoundGroup" then
					child.SoundGroup = folderInst
				end
			end

		elseif remodel.isDir(path) then

			local subFolder = groupDirectory(path)
			subFolder.Parent = folderInst

		end
	end

	return folderInst
end

local dirFolder = groupDirectory(DIRECTORY_FILE_PATH)
remodel.writeModelFile(DIRECTORY_FILE_PATH.."."..FILE_EXT, dirFolder)