' Create desktop shortcut for Bubble Pop Game
' Run this once to create the shortcut

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get desktop path
desktopPath = objShell.SpecialFolders("Desktop")

' Shortcut path
shortcutPath = desktopPath & "\Bubble Pop Game.lnk"

' Target script
targetPath = "C:\Users\temuri\bubble-pop-game\start-game.bat"

' Check if target exists
If Not objFSO.FileExists(targetPath) Then
    MsgBox "Target file not found: " & targetPath, vbCritical, "Error"
    WScript.Quit 1
End If

' Create shortcut
Set objShortcut = objShell.CreateShortcut(shortcutPath)
objShortcut.TargetPath = targetPath
objShortcut.WorkingDirectory = "C:\Users\temuri\bubble-pop-game"
objShortcut.Description = "Launch Bubble Pop Game"
objShortcut.IconLocation = "C:\Users\temuri\bubble-pop-game\icon.ico,0"  ' Will use default if not found
objShortcut.Save

MsgBox "Shortcut created on Desktop: " & shortcutPath, vbInformation, "Success"