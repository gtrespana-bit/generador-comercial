; -----------------------------------------------------------------------------
; Instalador del Generador de Presupuestos (Inno Setup)
; Se ejecuta desde CREAR_INSTALADOR.bat, que primero empaqueta la app con
; PyInstaller, descarga el bootstrapper oficial de WebView2 y luego compila
; este script.
; Resultado: instalador\Instalador_Presupuestos.exe
;
; La instalación es por usuario (sin pedir permisos de administrador) y
; crea acceso directo en el escritorio y en el menú Inicio, con su
; desinstalador. Los datos del usuario viven en %LOCALAPPDATA%\Presupuestos
; y NO se borran al desinstalar (para que no pierdas nada por accidente).
; -----------------------------------------------------------------------------

#define WebView2RuntimeKey "Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"

[Setup]
AppName=Generador de Presupuestos
AppVersion=1.0
AppPublisher=RemodelaT Venezuela
AppPublisherURL=https://www.remodelat.net
DefaultDirName={localappdata}\Programs\Presupuestos
DefaultGroupName=Presupuestos
DisableProgramGroupPage=yes
OutputDir=instalador
OutputBaseFilename=Instalador_Presupuestos
SetupIconFile=icono.ico
UninstallDisplayIcon={app}\Presupuestos.exe
UninstallDisplayName=Generador de Presupuestos
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\Presupuestos.exe"; DestDir: "{app}"; Flags: ignoreversion
; Bootstrapper oficial de Microsoft (≈2 MB). Solo se ejecuta si el equipo no
; dispone ya de WebView2; entonces descarga e instala el runtime en silencio.
Source: "recursos\MicrosoftEdgeWebview2Setup.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{autoprograms}\Presupuestos"; Filename: "{app}\Presupuestos.exe"
Name: "{autodesktop}\Presupuestos"; Filename: "{app}\Presupuestos.exe"; Tasks: desktopicon

[Run]
; El bootstrapper detecta automáticamente x86/x64/ARM64. Al estar el setup
; instalado por usuario, WebView2 se instala por usuario sin pedir elevación.
Filename: "{tmp}\MicrosoftEdgeWebview2Setup.exe"; Parameters: "/silent /install"; StatusMsg: "Preparando el motor de la aplicación..."; Flags: waituntilterminated runhidden; Check: WebView2Falta
Filename: "{app}\Presupuestos.exe"; Description: "Abrir Generador de Presupuestos"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; No borramos %LOCALAPPDATA%\Presupuestos: conserva tus datos al desinstalar.

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
