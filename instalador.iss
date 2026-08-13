; -----------------------------------------------------------------------------
; Instalador de CotizaT (Inno Setup)
; Se ejecuta desde CREAR_INSTALADOR.bat, que primero empaqueta la app con
; PyInstaller, descarga el bootstrapper oficial de WebView2 y luego compila
; este script. Resultado: instalador\Instalador_CotizaT.exe
;
; La instalación es por usuario y no borra los datos al desinstalar.
; Al actualizar una versión anterior se conserva su directorio de programa y
; CotizaT detecta automáticamente %LOCALAPPDATA%\Presupuestos si allí existe
; una base previa. Las instalaciones nuevas usan %LOCALAPPDATA%\CotizaT.
; -----------------------------------------------------------------------------

#define WebView2RuntimeKey "Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"

[Setup]
; Conserva el identificador implícito del instalador anterior para que CotizaT
; sea una actualización y no una segunda aplicación independiente.
AppId=Generador de Presupuestos
AppName=CotizaT
AppVersion=1.0
AppPublisher=CotizaT
DefaultDirName={localappdata}\Programs\CotizaT
DefaultGroupName=CotizaT
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
OutputDir=instalador
OutputBaseFilename=Instalador_CotizaT
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\CotizaT.exe
UninstallDisplayName=CotizaT
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\CotizaT.exe"; DestDir: "{app}"; Flags: ignoreversion
; Bootstrapper oficial de Microsoft (≈2 MB). Solo se ejecuta si el equipo no
; dispone ya de WebView2; entonces descarga e instala el runtime en silencio.
Source: "recursos\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[InstallDelete]
; Limpia solo binarios y accesos directos antiguos. Nunca toca la base,
; backups, imágenes ni otros datos creados por el usuario.
Type: files; Name: "{app}\Presupuestos.exe"
Type: files; Name: "{autodesktop}\Presupuestos.lnk"
Type: files; Name: "{autoprograms}\Presupuestos.lnk"

[Icons]
Name: "{autoprograms}\CotizaT"; Filename: "{app}\CotizaT.exe"
Name: "{autodesktop}\CotizaT"; Filename: "{app}\CotizaT.exe"; Tasks: desktopicon

[Run]
; El bootstrapper detecta automáticamente x86/x64/ARM64. Al estar el setup
; instalado por usuario, WebView2 se instala por usuario sin pedir elevación.
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Preparando el motor de la aplicación..."; Flags: waituntilterminated runhidden; Check: WebView2Falta
Filename: "{app}\CotizaT.exe"; Description: "Abrir CotizaT"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Deliberadamente vacío: los presupuestos y copias del usuario se conservan.

[Code]
function EsVersionWebView2Valida(const Version: String): Boolean;
begin
  Result := (Version <> '') and (Version <> '0.0.0.0');
end;

function HayWebView2EnRegistro(const RootKey: Integer; const SubKey: String): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(RootKey, SubKey, 'pv', Version) and EsVersionWebView2Valida(Version);
end;

function WebView2Instalado(): Boolean;
begin
  { Microsoft indica comprobar tanto una instalación por usuario como por
    máquina. Se usan explícitamente ambas vistas del registro en 64 bits. }
  if IsWin64 then
    Result :=
      HayWebView2EnRegistro(HKCU64, '{#WebView2RuntimeKey}') or
      HayWebView2EnRegistro(HKCU32, '{#WebView2RuntimeKey}') or
      HayWebView2EnRegistro(HKLM64, 'SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}') or
      HayWebView2EnRegistro(HKLM32, '{#WebView2RuntimeKey}')
  else
    Result :=
      HayWebView2EnRegistro(HKCU32, '{#WebView2RuntimeKey}') or
      HayWebView2EnRegistro(HKLM32, '{#WebView2RuntimeKey}');
end;

function WebView2Falta(): Boolean;
begin
  Result := not WebView2Instalado();
end;
