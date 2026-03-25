Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
venvPythonw = projectDir & "\.venv\Scripts\pythonw.exe"
systemPythonw = "pythonw"

If fso.FileExists(venvPythonw) Then
    shell.Run """" & venvPythonw & """ """ & projectDir & "\desktop.py""", 0, False
Else
    shell.Run systemPythonw & " """ & projectDir & "\desktop.py""", 0, False
End If
