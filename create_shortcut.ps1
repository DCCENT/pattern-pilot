param(
    [string]$ShortcutPath,
    [string]$TargetPath,
    [string]$WorkingDir
)

$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $TargetPath
$shortcut.WorkingDirectory = $WorkingDir
$shortcut.Description = "Pattern Pilot - Financial Analysis"
$shortcut.Save()
