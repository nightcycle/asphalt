-- Constants
local ARGS = {...}
local BUILD_PATH = ARGS[1]
local CLASS_NAME = ARGS[2]
local JSON_STRING = ARGS[3]:gsub("'", "\"")
local INST_CONFIG_TREE = json.fromString(JSON_STRING)
print("building instance")

-- set properties
local inst = Instance.new(CLASS_NAME)
if INST_CONFIG_TREE["Name"] then
	inst.Name = INST_CONFIG_TREE["Name"]["value"]
	print("setting name: "..inst.Name)
end
for propertyName, valueConfig in pairs(INST_CONFIG_TREE) do
	if propertyName ~= "Name" then
		print("setting property "..propertyName.." to "..tostring(valueConfig["value"]))
		remodel.setRawProperty(
			inst, 
			propertyName, 
			valueConfig["type"],
			valueConfig["value"]
		)
	end
end

-- write file
print("writing model file to "..tostring(BUILD_PATH))
remodel.writeModelFile(BUILD_PATH, inst)