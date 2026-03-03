Option Explicit

Dim fso, shell, appDir, pythonwPath
Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

appDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonwPath = appDir & "\.venv\Scripts\pythonw.exe"

If Not fso.FileExists(pythonwPath) Then
    MsgBox "Virtual environment .venv was not found." & vbCrLf & _
           "Run once in PowerShell:" & vbCrLf & _
           "  py -m venv .venv" & vbCrLf & _
           "  .\.venv\Scripts\activate" & vbCrLf & _
           "  pip install -r requirements.txt", vbCritical, "Zibration Detect App"
    WScript.Quit 1
End If

shell.CurrentDirectory = appDir
shell.Environment("PROCESS")("PYTHONPATH") = appDir & "\src"
shell.Run """" & pythonwPath & """ -m app.main", 0, False
