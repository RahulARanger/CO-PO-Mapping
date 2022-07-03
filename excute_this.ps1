
function Show-Failed {
    
    Add-Type -AssemblyName PresentationCore,PresentationFramework
    $ButtonType = [System.Windows.MessageBoxButton]::Ok
    $MessageIcon = [System.Windows.MessageBoxImage]::Error
    $MessageBody = "It seems Matlab was not installed in your System! Please Install Matlab and add it to path"
    $MessageTitle = "Matlab Engine Not Found"
    [console]::beep(2000,500)
    Start-Process "https://in.mathworks.com/matlabcentral/answers/94933-how-do-i-edit-my-system-path-in-windows"
    [System.Windows.MessageBox]::Show($MessageBody,$MessageTitle,$ButtonType,$MessageIcon)
    Exit;
}


function Show-Matlab{
    $MatLab = (Get-Command matlab.exe -ErrorAction SilentlyContinue);
    return $(If ($MatLab) {$matlab.Path} Else {Show-Failed});
}

$mat_path = Show-Matlab