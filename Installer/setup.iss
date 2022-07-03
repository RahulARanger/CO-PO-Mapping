#define Version="0.2.0"
#define Name="CO-PO Mapping"
#define Author="Tangellapalli Srinivas"
#define Mx="CO-PO"
#define SignTool="Sign"
#define Contact="mailto:srinivast@nitj.ac.in"
#define ProjectRoot = "{app}/CO_PO"
#define OpenTool = "../CO_PO/main.py"
#define PyRoot = "{app}/python"
#define Repo = "https://github.com/Tangellapalli-Srinivas/CO-PO-Mapping"
#include "misc.iss"

[Setup]
; Basic Meta
AppName="{#Name}"
AppVersion="{#Version}"
AppPublisher="{#Author}"
AppSupportURL="{#Contact}"
AppPublisherURL="{#Repo}"
AppUpdatesURL="{#Repo}"
AppContact="{#Contact}"


BackColor=clBlue
BackColor2=clBlack


; IMPORTANT
AllowCancelDuringInstall=yes
; tho default yes, don't change this, else we won't be able to quit even if install fails I GUESS

; does it add some registry keys
ChangesEnvironment=yes  

; 64 Bit Application, this changes lot of constants like the fodler for {app} its in program files
; instead of programe files (x86)
; refer: https://jrsoftware.org/ishelp/topic_consts.htm
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; makes installer not fully resizable (it still has some max and min sizes)
WindowResizable=no

; Group Name on starts folder
DefaultGroupName="{#Mx}"                                                 

; Show Selected Directory
AlwaysShowDirOnReadyPage=yes
AppComments="Downloads Python requirements and others if any, for the CO-PO"

; WHERE TO SAVE AFTER INSTALLATION
DefaultDirName="{autopf}\{#Name}"


OutputDir="Output"
OutputBaseFilename="{#Name}"

; uninstall exe file name 
UninstallDisplayName="CO-PO-Uninstall"

; Compression Things
Compression=lzma
SolidCompression=yes

; Uses Windows Vista style
WizardStyle=modern

DisableWelcomePage=no
; This is the first page up until now, it just shows the LICENSE and makes sure user accepts it

; doesn't allow more than one setup to run at the same time
SetupMutex={#Mx}
AppMutex={#Mx}

InfoBeforeFile="README.rtf"

; Below Value is Oberserved Value
ExtraDiskSpaceRequired=28736046
ReserveBytes=31330304

; Comment this line if you want to locally setup
SignTool=SignThis



[Files]
Source: "{tmp}\python.zip"; DestDir: "{app}"; flags: external skipifsourcedoesntexist; Permissions: users-modify;
Source: "{tmp}\get-pip.py"; DestDir: "{app}"; flags: external skipifsourcedoesntexist; Permissions: users-modify;
Source: "../CO_PO\assets\*"; DestDir: "{app}/CO_PO/assets";
Source: "{tmp}\bootstrap.min.css"; DestDir: "{app}/CO_PO/assets"; flags: external skipifsourcedoesntexist; Permissions: users-modify;
Source: "./setup.ps1"; DestDir: "{app}"; Permissions: users-modify; Flags: deleteafterinstall;
Source: "{app}/python/pythonw.exe"; DestDir: "{app}"; Flags: skipifsourcedoesntexist deleteafterinstall;
Source: "../gate.ps1"; DestDir: "{app}";
Source: "../requirements.txt"; DestDir: "{app}"; Permissions: users-modify; AfterInstall: PostInstall

Source: "../CO_PO\*"; DestDir: "{app}/CO_PO";


[Dirs]
Name: "{app}/CO_PO"; Permissions: everyone-modify;

; For more quality progress while uninistalling
Name: "{#PyRoot}"; Permissions: everyone-full;
Name: "{#PyRoot}/__pycache__"; Permissions: everyone-modify;
Name: "{#PyRoot}/scripts"; Permissions: everyone-full;
Name: "{#PyRoot}/pip"; Permissions: everyone-modify;


[UninstallDelete]
; files which have been skipped must be explicitly mentioned in this section 
Type: filesandordirs; Name: "{#PyRoot}";

Type: files; Name: "{app}\requirements.txt";
Type: files; Name: "{app}\setup.ps1";
Type: files; Name: "{app}\get-pip.py";  
Type: files; Name: "{app}\python.zip";
Type: files; Name: "{app}\python\lib\*.pyc";

Type: filesandordirs; Name: "{app}\CO_PO\__pycache__";
Type: filesandordirs; Name: "{app}\CO_PO\assets";
Type: filesandordirs; Name: "{app}\CO_PO\temp";
Type: filesandordirs; Name: "{#PyRoot}\scripts\*.exe";

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Icons]
Name: "{autodesktop}\{#Name}"; Filename: "{#PyRoot}/python.exe"; Parameters: "{#OpenTool}"; WorkingDir: "{#PyRoot}"; Comment: "Opens CO-PO Mapping APP"; Flags: runminimized; Tasks: desktopicon 
Name: "{group}\{#Name}"; Filename: "{#PyRoot}/python.exe"; Parameters: "{#OpenTool}"; WorkingDir: "{#PyRoot}"; Comment: "Opens CO-PO Mapping APP"; Flags: runminimized


[Run]
// any other than powershell.exe will trigger false positive virus test.
Filename: "powershell.exe"; Description: "Open Application"; Parameters: "-file ""{app}\gate.ps1"" -mode 0"; WorkingDir: "{app}"; Flags: postinstall runasoriginaluser runminimized; Check: IsFresh;


[Code]
// https://stackoverflow.com/questions/28221394/proper-structure-syntax-for-delphi-pascal-if-then-begin-end-and
// we start with this event
procedure InitializeWizard;
begin
  Ask := True;
  ImplicitExitCode := -1073741510;
  Downloaded := True;
  DownloadPage := CreateDownloadPage('Downloading Python...', 'Downloading & Extracting Embedded python 3.6.8.zip', @OnDownloadProgress);
  DataOutDated := False;
end;
                                    
function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  if CheckAndQuit() <> 0 then 
    Result := 'Please Close the necessary running applications to proceed forward'
  else
    Result := CheckAndDownloadPython();
end;
// one needs to copy this event function as it is or modify them as they need
procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  Confirm := Confirm and Ask;
end;
function InitializeUninstall: Boolean;
begin
  Result := CheckAndQuit() = 0;
  if not Result then
      MsgBox('Please close the necessary applications before uninstalling this application!', mbError, MB_OK)
end;      

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    ExecPSScript('gate.ps1', True, '-mode 3', ResultCode);
  end;
end;
