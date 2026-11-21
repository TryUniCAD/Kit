class OwnerGuard:
    def __init__(self):
        self.active = False
        self.denied = []

    def inspect(self, event, args):
        if event == "import" and args and str(args[0]).split(".")[0] in ("win32com", "pythoncom", "comtypes", "FreeCAD", "Part", "bpy"):
            self.denied.append(event)
            raise PermissionError("owner proof attempted a CAD runtime import")
        if self.active and event in ("open", "os.listdir", "os.scandir", "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.fork", "os.forkpty", "socket.connect"):
            self.denied.append(event)
            raise PermissionError("owner proof attempted runtime I/O: " + event)

    def profile(self, frame, event, arg):
        if self.active and event == "call" and frame.f_code.co_name in ("BuildSldprt", "FinishBlindMut", "EmitPartStreams", "MakeThroughPart", "MakeScopedThru"):
            self.denied.append(frame.f_code.co_name)
            raise PermissionError("owner component reached complete-file construction")
