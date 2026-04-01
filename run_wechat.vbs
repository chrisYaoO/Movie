Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
venvPython = projectDir & "\.venv\Scripts\python.exe"
systemPython = "python"

If fso.FileExists(venvPython) Then
    pythonCmd = """" & venvPython & """"
Else
    pythonCmd = systemPython
End If

cmd = "cmd.exe /k cd /d """ & projectDir & """ && " & pythonCmd & " wechat.py"
shell.Run cmd, 1, False
