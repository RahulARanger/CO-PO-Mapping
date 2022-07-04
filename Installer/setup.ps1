
$DebugPreference = 'Continue'
$ErrorActionPreference = "Stop"

$host.UI.RawUI.WindowTitle = "Don't close this window, Closing this would affect the installation process."

$ScriptPath = (Get-Location).Path 
$PythonPath = Join-Path -Path $ScriptPath -ChildPath "Python";
$executable = Join-Path -Path $PythonPath -ChildPath "python.exe";

# Extracting Embedded Python, NOTE: this assumes Innosetup has already 
$temp_file = Join-Path -Path $ScriptPath -ChildPath "python.zip"
if(Test-Path -Path $temp_file){
    Write-Debug "Extracting Embedded Package"
    Expand-Archive -Path $temp_file -DestinationPath $PythonPath;
    Remove-Item -Path $temp_file;
    Write-Output "Done"
}

# Installs Pip
$temp_file = Join-Path -Path $ScriptPath -ChildPath "get-pip.py";

if(Test-Path -Path $temp_file){
    Write-Debug "Installing and setting Pip up..."
    & $executable $temp_file;
    Remove-Item -Path $temp_file;   
    Write-Output "Done"
}

# This enables python to use Lib and site-packages inside it, so the one we install through pip
Write-Debug "Enabling Python to use Lib and site-packages"
$temp_file = Get-ChildItem -Path $PythonPath -Filter "*._pth"

Set-Content -Path $temp_file.FullName -Value "
Lib
Lib/site-packages
../
.
import site
"
# creates a site-customize.py, which enables python Interpreter know the sys.path
# we also make sure to not use any pre-existing python paths
Write-Debug "Restricting python to use any other path"
$temp_file = Join-Path -Path $PythonPath -ChildPath "sitecustomize.py"

if(Test-Path -Path $temp_file) {Remove-Item -Path $temp_file} else {}

New-Item -Path $temp_file -ItemType "file"

Set-Content -Path $temp_file -Value "
import sys;
sys.path = sys.path[: 4]
"
Write-Output "Done"

# Now we unzip the internal Modules, we do that so we can use mostly all of them without any problem
$temp_file = (Get-ChildItem -Path $PythonPath -Filter "*.zip")

if($temp_file -and (Test-Path -Path $temp_file[0].FullName)){
    Write-Debug("Unzipping Internal Modules...")
    $unzipped = Join-Path -Path $PythonPath -ChildPath "Lib"
    Expand-Archive -Path $temp_file.FullName -DestinationPath $unzipped 
    Remove-Item -Path $temp_file.Fullname
    Write-Output "Done"
}

Write-Debug "Installing Packages, May take some time. Please wait. Takes Around 5 Minutes"
# Now we install external packages for the build from requirements.txt
$temp_file = Join-Path -Path $ScriptPath -ChildPath "requirements.txt";
if (Test-Path -Path $temp_file) {& $executable @("-m", "pip", "install", "-r", $temp_file)} else {}

Write-Debug "Deleting Requirements.txt"
Remove-Item -Path $temp_file


function Show-Failed {
    
    Add-Type -AssemblyName PresentationCore,PresentationFramework
    $ButtonType = [System.Windows.MessageBoxButton]::Ok
    $MessageIcon = [System.Windows.MessageBoxImage]::Error
    $MessageBody = "It seems Matlab was not installed in your System! Please Install Matlab and add it to path"
    $MessageTitle = "Matlab Engine Not Found"
    [console]::beep(2000,500)
    Start-Process "https://in.mathworks.com/matlabcentral/answers/94933-how-do-i-edit-my-system-path-in-windows"
    [System.Windows.MessageBox]::Show($MessageBody,$MessageTitle,$ButtonType,$MessageIcon)
    Exit -5;
}


function Show-Matlab{
    $MatLab = (Get-Command matlab.exe -ErrorAction SilentlyContinue);
    return $(If ($MatLab) {$matlab.Path} Else {Show-Failed});
}

$mat_path = Resolve-Path(
    Join-Path -Path (Join-Path -Path (Join-Path -Path (Join-Path -Path (Join-Path -Path (Show-Matlab) -ChildPath "..") -ChildPath "..") -ChildPath "extern") -ChildPath "engines") -ChildPath "python"
    )

Set-Location $mat_path;
& $executable @("-m", "pip", "install", ".");

Write-Debug "Deleting One Time Use Modules";
& $executable @("-m", "pip", "uninstall", "wheel", "pip", "-y");

Write-Output "Installation is over"

$DebugPreference = 'SilentlyContinue'
$ErrorActionPreference = "Continue"
