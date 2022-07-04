[Code]
var       
  DownloadPage: TDownloadWizardPage;  // downloads packages
  Ask: Boolean;   // Ask is Flag for like, say we click Click button to exit setup
  // Ask = true for asking confirmation else False [we set False if we need to exit by force]
  ImplicitExitCode: Integer; // like this has ability to detect implicit closes of powershell scripts
  Downloaded: Boolean;
  DataOutDated: Boolean;
function ExecPSScript(file: String; show: Boolean; Params: String; var ResultCode: Integer): Boolean;
var
ShowCmd: Integer;
begin
  if show then
    ShowCmd := SW_SHOW
  else
    ShowCmd := SW_HIDE;
  Result := ShellExec(
              '',
              'powershell',
              ExpandConstant(
                Format(
                  '-NoLogo -ExecutionPolicy ByPass -File "{app}/%s" %s', [file, Params]
                  )
                ),
              ExpandConstant('{app}'),
              ShowCmd,
              ewWaitUntilTerminated,
              ResultCode
          );
end;      

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if Progress = ProgressMax then
    Log(Format('Successfully downloaded file to {tmp}: %s', [FileName]));
  Result := True;
end;

procedure CloseSetup(CancelMsg: String);
begin 
  if Length(CancelMsg) > 0 then 
    MsgBox(CancelMsg, mbCriticalError, MB_OK);
  
  Ask := False;
  WizardForm.Close();
end;
// Checks for the Python Directory, if found it says Downloaded else it downloads it

function CheckAndDownloadPython(): String;
begin
    Downloaded := DirExists(ExpandConstant('{app}/python'));
    Result := '';
    if not Downloaded then
      begin 
        DownloadPage.Clear;
        DownloadPage.Add('https://bootstrap.pypa.io/pip/3.6/get-pip.py', 'get-pip.py', '');
        DownloadPage.Add('https://www.python.org/ftp/python/3.6.8/python-3.6.8-embed-amd64.zip', 'python.zip', '');
        DownloadPage.Add('https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css', 'bootstrap.min.css', '');
        DownloadPage.Show;
        try 
          DownloadPage.Download;
        except 
          Result := AddPeriod(GetExceptionMessage);
        finally
          DownloadPage.Hide;
        end;
      end;
end;

procedure PostInstall;
var 
  ResultCode: Integer;
  ResultString: String;
  PythonPath: String;
begin
    if not Downloaded then 
    
    begin
      WizardForm.Hide;
      
      repeat
  
      if not ExecPSScript('setup.ps1', True, '', ResultCode) then
      
       ResultString := 'It seems we can''t run setup.ps1, maybe that file was not installed! anyways please raise the issue in the repo!';
      
      if ResultCode = ImplicitExitCode then
        begin
          if SuppressibleMsgBox
          ('Do you want cancel the Installation ?'#13#10''#13#10'Installer uses Powershell script as a part of Installation'#13#10'',
           mbConfirmation,
            MB_YESNO,
             IDNO) = IDYES then 
            begin 
              ResultCode := -1
              ResultString := 'Closed as requested'
            end;
        end
      else if ResultCode <> 0 then 
        ResultString := 'Setup Script didn''t return the favorable result. Maybe there was some unexpected error, which shouldn''t have happended causally. Please raise this issue in the repo';
 
      until ResultCode <> ImplicitExitCode
      WizardForm.Show;
    
      if ResultCode <> 0 then
        begin 
          PythonPath := ExpandConstant('{app}/python');
          if DirExists(PythonPath) then
            DelTree(PythonPath, True, True, True); // deleting everything that setup  did if failed
          
          CloseSetup(ResultString);
        end;
    end;
end;

function CheckAndQuit: Integer;
begin
    if FileExists(ExpandConstant('{app}/gate.ps1')) then 
      ExecPSScript('gate.ps1', False, '-mode 1', Result)
end;

function IsFresh: Boolean;
// will not ask for Run Script after Setup was successfull if the setup was for update
begin
  Result := Downloaded;
end;
