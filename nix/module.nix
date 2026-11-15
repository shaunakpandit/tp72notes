self:
{ config, lib, pkgs, ... }:
let
  cfg = config.services.tp72notes;
in
{
  options.services.tp72notes = {
    enable = lib.mkEnableOption "transcribing TP-7 voice notes when it is plugged in";
    package = lib.mkOption {
      type = lib.types.package;
      default = self.packages.${pkgs.system}.default;
    };
  };

  config = lib.mkIf cfg.enable {
    # Starts the user service when the TP-7 connects in file transfer mode. Matches the MTP interface (06/01/01)
    # because ID_MTP_DEVICE is set in audio-interface mode too (same USB ids).
    services.udev.extraRules = ''
      ACTION=="add", SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ENV{ID_USB_INTERFACES}=="*:060101:*", ATTR{idVendor}=="2367", ATTR{idProduct}=="0019", TAG+="systemd", ENV{SYSTEMD_USER_WANTS}+="tp72notes.service"
    '';

    systemd.user.services.tp72notes = {
      description = "Transcribe TP-7 voice notes into daily notes";
      path = [ pkgs.git pkgs.openssh pkgs.libmtp pkgs.libnotify ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = lib.getExe' cfg.package "tp72notes";
      };
    };
  };
}
