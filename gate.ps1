param(
    [int]$mode=0,
    [switch]$update,
    [String[]]$arguments
)

$DebugPreference = 'Continue'
$ErrorActionPreference = "Stop"


# Some Dynamic Constants

$ScriptPath = (Get-Location).Path
$PythonPath = Join-Path -Path $ScriptPath -ChildPath "Python";
$executable = Join-Path -Path $PythonPath -ChildPath "python.exe";
$CoPo = Join-Path -Path $ScriptPath -ChildPath "CO_PO"


function Get-RunningProjects{
    $Pythons = Join-Path -Path $PythonPath -ChildPath "*";
    return  Get-WmiObject -Class "Win32_Process" -ComputerName "." | where-object {$_.Path -like $Pythons};
}


function Get-ProjectPyPath{
    param(
        [string]$file
    )
    return '"' + (Join-Path -Path $CoPo -ChildPath "$file.pyc") + '" '
}

function Start-PythonScript{
    param(
        [String]$file="main",
        [String[]]$arg_s=@()
    )

    $arg_s = (Get-ProjectPyPath -file $file) + $arg_s
    Start-Process $executable -WindowStyle Maximized -WorkingDirectory $ScriptPath -ArgumentList ($arg_s -Join " ")
}


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



function Get-Update{
        
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/RahulARanger/CO-PO-Mapping/releases/latest" -Method "GET"
    $update_it = $response.tag_name -ne $arguments[0]
    if (-not $update_it){
        return
    }

    Write-Output "Updating..."

    $download_url = $response.assets.browser_download_url
    $temp = Join-Path -Path $env:TEMP -ChildPath $response.assets.Name
    write-Output $temp

    Invoke-WebRequest -Uri $download_url -OutFile $temp

    Start-Process -FilePath $temp -Wait
    Remove-Item -Path $temp
}


switch($mode){
    # for running the application
    0{
        Show-Matlab;
        Start-Process $executable -WindowStyle Maximized -WorkingDirectory $ScriptPath -ArgumentList ('"' + (Join-Path -Path $CoPo -ChildPath "main.py") + '" ')
    }

    # Checking if all the instances are closed
    1{ 
        $store = @(Get-RunningProjects);
        if($store.length -gt 0){
            $store | Out-GridView -passthru -Title "These processes must be closed in-order to proceed forward!"
            exit 5
        }
    }

    # Checking for the updates
    2{
        Write-Debug "Checking for the updates...";
        Get-Update
    }

    3{
        Start-Sleep -Seconds 6;
        # Since this scripts are started by python, it's very likely that it will be executed by them

        $store = @(Get-RunningProjects);
        Write-Debug "Deleting Temp folder";

        if($store.length -eq 0){
            $temp = Join-Path -Path $CoPo -ChildPath "temp"

            if(Test-Path -Path $temp){
                Remove-Item -Recurse -Force -Path $temp;
            }
            
        }
    }
}

$DebugPreference = 'SilentlyContinue'
$ErrorActionPreference = "Continue"
