const Names = new Set(["sldworks.exe", "sldmodu.dll", "swccu.dll", "sldarchiveu.dll", "sldgciparau.dll", "pskernel.dll", "mfc140u.dll"])
const Modules = Process.enumerateModules().filter(Value => Names.has(Value.name.toLowerCase())).map(Value => ({
  name: Value.name, path: Value.path, base: Value.base.toString(), size: Value.size
}))
send({kind: "target-identity", pid: Process.id, architecture: Process.arch, platform: Process.platform, pointer_size: Process.pointerSize, modules: Modules})
