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
    services.udisks2.enable = true;

    # Starts the user service for whoever is logged in when the TP-7's disk appears.
    services.udev.extraRules = ''
      ACTION=="add", SUBSYSTEM=="block", ENV{DEVTYPE}=="disk", ATTRS{idVendor}=="2367", ATTRS{idProduct}=="0019", TAG+="systemd", ENV{SYSTEMD_USER_WANTS}+="tp72notes.service"
    '';

    systemd.user.services.tp72notes = {
      description = "Transcribe TP-7 voice notes into daily notes";
      path = [ pkgs.git pkgs.openssh pkgs.udisks pkgs.libnotify ];
      serviceConfig = {
        Type = "oneshot";
        ExecStart = lib.getExe' cfg.package "tp72notes";
      };
    };
  };
}
