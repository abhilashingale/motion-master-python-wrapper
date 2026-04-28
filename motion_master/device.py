from __future__ import annotations

from typing import Any

from ._base import _BaseClient


class Device(_BaseClient):
    """Calls targeting a specific device identified by device_ref.

    device_ref accepts:
      - position in the EtherCAT chain, starting from 1 (e.g. 1)
      - auto-generated device address (e.g. 2692012680)
      - serial number string (e.g. "8504-03-0002369-2329")

    Typically obtained via System.device(ref) so the HTTP session is shared::

        system = System("http://localhost:63526/api")
        system.connect()
        drive = system.device(1)
        value = drive.upload_parameter("0x6064", "0x00")

    Can also be instantiated standalone::

        drive = Device(device_ref=1, base_url="http://localhost:63526/api")
    """

    def __init__(
        self,
        device_ref: str | int,
        base_url: str = "http://localhost:63526/api",
    ) -> None:
        super().__init__(base_url)
        self.device_ref = str(device_ref)

    # ------------------------------------------------------------------ #
    # Parameters                                                           #
    # ------------------------------------------------------------------ #

    def get_parameter_info(self, request_timeout: int | None = None) -> list:
        """List parameters available on the device (names/types, no values)."""
        return self._get(
            f"devices/{self.device_ref}/parameter-info",
            self._build_params(request_timeout=request_timeout),
        )

    def upload_parameter(
        self,
        index: str,
        subindex: str,
        load_from_cache: bool | None = None,
        request_timeout: int | None = None,
    ) -> dict:
        """Read a single parameter value from the device (SDO upload)."""
        return self._get(
            f"devices/{self.device_ref}/upload/{index}/{subindex}",
            self._build_params(load_from_cache=load_from_cache, request_timeout=request_timeout),
        )

    def download_parameter(
        self,
        index: str,
        subindex: str,
        value: Any,
        request_timeout: int | None = None,
    ) -> None:
        """Write a single scalar parameter value to the device (SDO download)."""
        self._get(
            f"devices/{self.device_ref}/download/{index}/{subindex}/{value}",
            self._build_params(request_timeout=request_timeout),
        )

    def download_binary_parameter(
        self,
        index: str,
        subindex: str,
        value: bytes,
        request_timeout: int | None = None,
    ) -> None:
        """Write a binary (octet-stream) parameter value to the device."""
        self._put(
            f"devices/{self.device_ref}/download/{index}/{subindex}",
            params=self._build_params(request_timeout=request_timeout),
            data=value,
        )

    def get_parameter_values(
        self,
        parameters: list[dict[str, Any]],
        request_timeout: int | None = None,
    ) -> dict:
        """Retrieve values for a list of {index, subindex} parameter dicts."""
        return self._post(
            f"devices/{self.device_ref}/get-parameter-values",
            params=self._build_params(request_timeout=request_timeout),
            json=parameters,
        )

    def set_parameter_values(
        self,
        parameter_values: list[dict[str, Any]],
        request_timeout: int | None = None,
    ) -> dict:
        """Set multiple parameter values on the device in one call."""
        return self._post(
            f"devices/{self.device_ref}/set-parameter-values",
            params=self._build_params(request_timeout=request_timeout),
            json=parameter_values,
        )

    def get_parameters(
        self,
        load_from_cache: bool | None = None,
        request_timeout: int | None = None,
    ) -> dict:
        """Retrieve all parameter info and current values for the device."""
        return self._get(
            f"devices/{self.device_ref}/parameters",
            self._build_params(load_from_cache=load_from_cache, request_timeout=request_timeout),
        )

    # ------------------------------------------------------------------ #
    # Files                                                                #
    # ------------------------------------------------------------------ #

    def get_file_list(self, request_timeout: int | None = None) -> list:
        """List files stored in the device flash memory."""
        return self._get(
            f"devices/{self.device_ref}/files",
            self._build_params(request_timeout=request_timeout),
        )

    def unlock_protected_files(self, request_timeout: int | None = None) -> None:
        """Unlock protected files to allow writing or deletion."""
        self._get(
            f"devices/{self.device_ref}/files/unlock",
            self._build_params(request_timeout=request_timeout),
        )

    def get_file(self, filename: str, request_timeout: int | None = None) -> bytes | str:
        """Retrieve a file from the device; returns str for text, bytes for binary."""
        return self._get(
            f"devices/{self.device_ref}/files/{filename}",
            self._build_params(request_timeout=request_timeout),
        )

    def set_file(self, filename: str, content: bytes, request_timeout: int | None = None) -> None:
        """Write binary content to a file on the device."""
        self._put(
            f"devices/{self.device_ref}/files/{filename}",
            params=self._build_params(request_timeout=request_timeout),
            data=content,
        )

    def delete_file(self, filename: str, request_timeout: int | None = None) -> None:
        """Delete a file from the device flash memory."""
        self._delete(
            f"devices/{self.device_ref}/files/{filename}",
            self._build_params(request_timeout=request_timeout),
        )

    def get_log(self, request_timeout: int | None = None) -> str:
        """Retrieve the device log as plain text."""
        return self._get(
            f"devices/{self.device_ref}/log",
            self._build_params(request_timeout=request_timeout),
        )

    def save_config(self) -> None:
        """Persist modified parameter values to the device's config.csv."""
        self._get(f"devices/{self.device_ref}/save-config")

    def load_config(
        self,
        config_data: bytes,
        refresh: bool | None = None,
        strategy: str | None = None,
    ) -> None:
        """Replace or merge config.csv on the device and reload configuration.

        strategy: "replace" (default) or "merge".
        refresh: re-read parameters from device after loading if True.
        """
        self._put(
            f"devices/{self.device_ref}/load-config",
            params=self._build_params(refresh=refresh, strategy=strategy),
            data=config_data,
        )

    # ------------------------------------------------------------------ #
    # Firmware                                                             #
    # ------------------------------------------------------------------ #

    def start_firmware_installation(
        self,
        firmware: bytes,
        skip_sii_installation: bool | None = None,
        skip_files: list[str] | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Install a firmware package on the device."""
        params = self._build_params(request_timeout=request_timeout)
        if skip_sii_installation is not None:
            params["skip-sii-installation"] = str(skip_sii_installation).lower()
        if skip_files:
            params["skip-files"] = skip_files
        self._post(
            f"devices/{self.device_ref}/start-firmware-installation",
            params=params,
            data=firmware,
        )

    def factory_reset(
        self,
        files_to_keep: str | None = None,
        install_empty_firmware: bool | None = None,
        reload_firmware: bool | None = None,
    ) -> None:
        """Perform a factory reset. Irreversible — all files not in files_to_keep are deleted."""
        self._get(
            f"devices/{self.device_ref}/factory-reset",
            self._build_params(
                files_to_keep=files_to_keep,
                install_empty_firmware=install_empty_firmware,
                reload_firmware=reload_firmware,
            ),
        )

    # ------------------------------------------------------------------ #
    # Motion control                                                       #
    # ------------------------------------------------------------------ #

    def quick_stop(self) -> None:
        """Issue a Quick Stop request to the device."""
        self._get(f"devices/{self.device_ref}/quick-stop")

    def reset_fault(self, force: bool | None = None) -> None:
        """Reset the device fault; force=True bypasses the CiA402 FAULT state check."""
        self._get(
            f"devices/{self.device_ref}/reset-fault",
            self._build_params(force=force),
        )

    def set_modes_of_operation(self, modes_of_operation: int) -> None:
        """Write Mode of Operation (0x6060:00). See ModesOfOperation enum for values."""
        self._get(f"devices/{self.device_ref}/set-modes-of-operation/{modes_of_operation}")

    def transition_to_cia402_state(self, state: str, request_timeout: int | None = None) -> None:
        """Transition the device to a CiA 402 state (e.g. "OPERATION_ENABLED")."""
        self._get(
            f"devices/{self.device_ref}/transition-to-cia402-state/{state}",
            self._build_params(request_timeout=request_timeout),
        )

    def get_cia402_state(self, request_timeout: int | None = None) -> dict:
        """Return the current CiA 402 state of the device."""
        return self._get(
            f"devices/{self.device_ref}/cia402-state",
            self._build_params(request_timeout=request_timeout),
        )

    def set_halt_bit(self, value: bool) -> None:
        """Set the halt bit high (True) or low (False)."""
        self._get(f"devices/{self.device_ref}/set-halt-bit/{str(value).lower()}")

    def apply_set_point(self) -> None:
        """Apply a new position set-point."""
        self._get(f"devices/{self.device_ref}/apply-set-point")

    def force_on_demand_parameters_update(self) -> None:
        """Trigger a fault reset or CiA402 transition to apply updated on-demand parameters."""
        self._get(f"devices/{self.device_ref}/force-on-demand-parameters-update")

    # ------------------------------------------------------------------ #
    # Motion controller                                                    #
    # ------------------------------------------------------------------ #

    def set_motion_controller_parameters(self, target: int | None = None) -> None:
        """Set the motion controller parameters."""
        self._get(
            f"devices/{self.device_ref}/set-motion-controller-parameters",
            self._build_params(target=target),
        )

    def enable_motion_controller(
        self,
        controller_type: str,
        filter: bool | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Enable the motion controller. controller_type: "TORQUE", "VELOCITY", "POSITION", etc."""
        self._get(
            f"devices/{self.device_ref}/enable-motion-controller/{controller_type}",
            self._build_params(filter=filter, request_timeout=request_timeout),
        )

    def disable_motion_controller(self, request_timeout: int | None = None) -> None:
        """Disable the motion controller."""
        self._get(
            f"devices/{self.device_ref}/disable-motion-controller",
            self._build_params(request_timeout=request_timeout),
        )

    # ------------------------------------------------------------------ #
    # EtherCAT                                                             #
    # ------------------------------------------------------------------ #

    def get_ethercat_network_state(self, request_timeout: int | None = None) -> dict:
        """Return the current EtherCAT network state."""
        return self._get(
            f"devices/{self.device_ref}/get-ethercat-network-state",
            self._build_params(request_timeout=request_timeout),
        )

    def set_ethercat_network_state(self, state: str, request_timeout: int | None = None) -> None:
        """Set the EtherCAT network state (e.g. "BOOT", "INIT", "PRE_OP", "SAFE_OP", "OP")."""
        self._get(
            f"devices/{self.device_ref}/set-ethercat-network-state/{state}",
            self._build_params(request_timeout=request_timeout),
        )

    # ------------------------------------------------------------------ #
    # System identification & auto-tuning                                  #
    # ------------------------------------------------------------------ #

    def start_system_identification(
        self,
        duration_seconds: float | None = None,
        torque_amplitude: int | None = None,
        start_frequency: int | None = None,
        end_frequency: int | None = None,
        next_gen_sys_id: bool | None = None,
        request_timeout: int | None = None,
    ) -> str:
        """Run System Identification; returns plant_model.csv content."""
        return self._get(
            f"devices/{self.device_ref}/start-system-identification",
            self._build_params(
                duration_seconds=duration_seconds,
                torque_amplitude=torque_amplitude,
                start_frequency=start_frequency,
                end_frequency=end_frequency,
                next_gen_sys_id=next_gen_sys_id,
                request_timeout=request_timeout,
            ),
        )

    def compute_auto_tuning_gains_velocity(
        self,
        velocity_loop_bandwidth: float | None = None,
        velocity_damping: float | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Compute velocity controller gains without running the full procedure."""
        self._get(
            f"devices/{self.device_ref}/compute-auto-tuning-gains/velocity",
            self._build_params(
                velocity_loop_bandwidth=velocity_loop_bandwidth,
                velocity_damping=velocity_damping,
                request_timeout=request_timeout,
            ),
        )

    def compute_auto_tuning_gains_position(
        self,
        controller_type: str,
        settling_time: float | None = None,
        position_damping: float | None = None,
        alpha_mult: int | None = None,
        order: int | None = None,
        lb: float | None = None,
        ub: float | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Compute position controller gains. controller_type e.g. "P_PI"."""
        self._get(
            f"devices/{self.device_ref}/compute-auto-tuning-gains/position",
            self._build_params(
                controller_type=controller_type,
                settling_time=settling_time,
                position_damping=position_damping,
                alpha_mult=alpha_mult,
                order=order,
                lb=lb,
                ub=ub,
                request_timeout=request_timeout,
            ),
        )

    def start_full_auto_tuning_velocity(self, request_timeout: int | None = None) -> dict:
        """Run the full velocity auto-tuning procedure; returns gain values."""
        return self._get(
            f"devices/{self.device_ref}/start-full-auto-tuning/velocity",
            self._build_params(request_timeout=request_timeout),
        )

    def start_full_auto_tuning_position(
        self, controller_type: str, request_timeout: int | None = None
    ) -> dict:
        """Run the full position auto-tuning procedure. controller_type e.g. "P_PI"."""
        return self._get(
            f"devices/{self.device_ref}/start-full-auto-tuning/position/{controller_type}",
            self._build_params(request_timeout=request_timeout),
        )

    def stop_full_auto_tuning(self, request_timeout: int | None = None) -> None:
        """Abort the running full auto-tuning procedure."""
        self._get(
            f"devices/{self.device_ref}/stop-full-auto-tuning",
            self._build_params(request_timeout=request_timeout),
        )

    # ------------------------------------------------------------------ #
    # Motion profiles                                                      #
    # ------------------------------------------------------------------ #

    def run_torque_profile(
        self,
        target: int | None = None,
        holding_duration: int | None = None,
        slope: int | None = None,
        skip_quick_stop: bool | None = None,
        target_reach_timeout: int | None = None,
        window: int | None = None,
        window_time: int | None = None,
    ) -> str:
        """Run the torque profile; returns CSV data."""
        return self._get(
            f"devices/{self.device_ref}/run-torque-profile",
            self._build_params(
                target=target,
                holding_duration=holding_duration,
                slope=slope,
                skip_quick_stop=skip_quick_stop,
                target_reach_timeout=target_reach_timeout,
                window=window,
                window_time=window_time,
            ),
        )

    def run_velocity_profile(
        self,
        acceleration: int | None = None,
        target: int | None = None,
        deceleration: int | None = None,
        holding_duration: int | None = None,
        skip_quick_stop: bool | None = None,
        target_reach_timeout: int | None = None,
        window: int | None = None,
        window_time: int | None = None,
    ) -> str:
        """Run the velocity profile; returns CSV data."""
        return self._get(
            f"devices/{self.device_ref}/run-velocity-profile",
            self._build_params(
                acceleration=acceleration,
                target=target,
                deceleration=deceleration,
                holding_duration=holding_duration,
                skip_quick_stop=skip_quick_stop,
                target_reach_timeout=target_reach_timeout,
                window=window,
                window_time=window_time,
            ),
        )

    def run_position_profile(
        self,
        acceleration: int | None = None,
        target: int | None = None,
        deceleration: int | None = None,
        holding_duration: int | None = None,
        relative: bool | None = None,
        skip_quick_stop: bool | None = None,
        target_reach_timeout: int | None = None,
        velocity: int | None = None,
        window: int | None = None,
        window_time: int | None = None,
    ) -> str:
        """Run the position profile; returns CSV data."""
        return self._get(
            f"devices/{self.device_ref}/run-position-profile",
            self._build_params(
                acceleration=acceleration,
                target=target,
                deceleration=deceleration,
                holding_duration=holding_duration,
                relative=relative,
                skip_quick_stop=skip_quick_stop,
                target_reach_timeout=target_reach_timeout,
                velocity=velocity,
                window=window,
                window_time=window_time,
            ),
        )

    # ------------------------------------------------------------------ #
    # Open-loop & chirp                                                    #
    # ------------------------------------------------------------------ #

    def start_open_loop_field_control(
        self,
        angle: int | None = None,
        velocity: int | None = None,
        acceleration: int | None = None,
        torque: int | None = None,
        torque_speed: int | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Start open-loop field control (useful for motor commissioning)."""
        self._get(
            f"devices/{self.device_ref}/start-open-loop-field-control",
            self._build_params(
                angle=angle,
                velocity=velocity,
                acceleration=acceleration,
                torque=torque,
                torque_speed=torque_speed,
                request_timeout=request_timeout,
            ),
        )

    def run_chirp_signal(
        self,
        hrd_streaming_duration: int | None = None,
        modes_of_operation: int | None = None,
        signal_type: int | None = None,
        start_frequency: int | None = None,
        start_procedure: int | None = None,
        target_amplitude: int | None = None,
        target_frequency: int | None = None,
        transition_time: int | None = None,
    ) -> str:
        """Run a chirp (frequency-sweep) signal; returns HRD CSV data."""
        return self._get(
            f"devices/{self.device_ref}/run-chirp-signal",
            self._build_params(
                hrd_streaming_duration=hrd_streaming_duration,
                modes_of_operation=modes_of_operation,
                signal_type=signal_type,
                start_frequency=start_frequency,
                start_procedure=start_procedure,
                target_amplitude=target_amplitude,
                target_frequency=target_frequency,
                transition_time=transition_time,
            ),
        )

    def start_limited_range_system_identification(
        self,
        hrd_streaming_duration: int | None = None,
        range_limit: int | None = None,
        range_limit_min: int | None = None,
        start_frequency: int | None = None,
        target_amplitude: int | None = None,
        target_frequency: int | None = None,
        transition_time: int | None = None,
    ) -> None:
        """Run the Limited Range System Identification procedure."""
        self._get(
            f"devices/{self.device_ref}/start-limited-range-system-identification",
            self._build_params(
                hrd_streaming_duration=hrd_streaming_duration,
                range_limit=range_limit,
                range_limit_min=range_limit_min,
                start_frequency=start_frequency,
                target_amplitude=target_amplitude,
                target_frequency=target_frequency,
                transition_time=transition_time,
            ),
        )

    # ------------------------------------------------------------------ #
    # Offset detection                                                     #
    # ------------------------------------------------------------------ #

    def start_offset_detection(self, request_timeout: int | None = None) -> dict:
        """Run the (legacy) Offset Detection procedure; returns commutationAngleOffset."""
        return self._get(
            f"devices/{self.device_ref}/start-offset-detection",
            self._build_params(request_timeout=request_timeout),
        )

    def run_offset_detection(self, step_names: str | None = None) -> list:
        """Run the new Offset Detection procedure with optional step selection.

        step_names: comma-separated step names, e.g.
          "openPhaseDetection,phaseResistanceMeasurement,phaseInductanceMeasurement"
        """
        # API uses camelCase "stepNames", not kebab-case
        params: dict[str, Any] = {}
        if step_names is not None:
            params["stepNames"] = step_names
        return self._get(f"devices/{self.device_ref}/run-offset-detection", params)

    # ------------------------------------------------------------------ #
    # Cogging torque                                                       #
    # ------------------------------------------------------------------ #

    def start_cogging_torque_recording(
        self,
        skip_auto_tuning: bool | None = None,
        request_timeout: int | None = None,
    ) -> list:
        """Run Cogging Torque Recording; returns array of 1024 integer values."""
        return self._get(
            f"devices/{self.device_ref}/start-cogging-torque-recording",
            self._build_params(skip_auto_tuning=skip_auto_tuning, request_timeout=request_timeout),
        )

    def get_cogging_torque_data(self, request_timeout: int | None = None) -> list:
        """Return the parsed content of the cogging_torque.bin file (1024 values)."""
        return self._get(
            f"devices/{self.device_ref}/cogging-torque-data",
            self._build_params(request_timeout=request_timeout),
        )

    # ------------------------------------------------------------------ #
    # Circulo encoder                                                      #
    # ------------------------------------------------------------------ #

    def get_circulo_encoder_magnet_distance(
        self,
        encoder_ordinal: int | None = None,
        ring_revision: int | None = None,
        request_timeout: int | None = None,
    ) -> dict:
        """Return the Circulo encoder magnet distance and position."""
        return self._get(
            f"devices/{self.device_ref}/circulo-encoder-magnet-distance",
            self._build_params(
                encoder_ordinal=encoder_ordinal,
                ring_revision=ring_revision,
                request_timeout=request_timeout,
            ),
        )

    def start_circulo_encoder_narrow_angle_calibration(
        self,
        encoder_ordinal: int | None = None,
        activate_health_monitoring: bool | None = None,
        measurement_only: bool | None = None,
        external_encoder_type: int | None = None,
        request_timeout: int | None = None,
    ) -> list:
        """Run the Circulo Encoder Narrow Angle Calibration; returns iteration data + robustness score."""
        return self._get(
            f"devices/{self.device_ref}/start-circulo-encoder-narrow-angle-calibration",
            self._build_params(
                encoder_ordinal=encoder_ordinal,
                activate_health_monitoring=activate_health_monitoring,
                measurement_only=measurement_only,
                external_encoder_type=external_encoder_type,
                request_timeout=request_timeout,
            ),
        )

    def start_circulo_encoder_configuration(
        self,
        encoder_ordinal: int | None = None,
        battery_mode_max_acceleration: int | None = None,
        external_circulo_type: int | None = None,
        request_timeout: int | None = None,
    ) -> None:
        """Run the Circulo Encoder Configuration procedure."""
        self._get(
            f"devices/{self.device_ref}/start-circulo-encoder-configuration",
            self._build_params(
                encoder_ordinal=encoder_ordinal,
                battery_mode_max_acceleration=battery_mode_max_acceleration,
                external_circulo_type=external_circulo_type,
                request_timeout=request_timeout,
            ),
        )

    def check_circulo_encoder_errors(self, encoder_ordinal: int | None = None) -> list:
        """Return a list of active Circulo encoder errors (empty list if none)."""
        return self._get(
            f"devices/{self.device_ref}/check-circulo-encoder-errors",
            self._build_params(encoder_ordinal=encoder_ordinal),
        )

    def write_circulo_integrated_encoder_config_bin_file(self, encoder_ordinal: int) -> None:
        """Write the Circulo integrated encoder configuration binary file to the device."""
        self._get(
            f"devices/{self.device_ref}/write-circulo-integrated-encoder-config-bin-file/{encoder_ordinal}"
        )

    # ------------------------------------------------------------------ #
    # Integro encoder                                                      #
    # ------------------------------------------------------------------ #

    def start_integro_encoder_calibration(self) -> None:
        """Run the Integro Encoder Calibration procedure."""
        self._get(f"devices/{self.device_ref}/start-integro-encoder-calibration")

    def get_integro_encoder_firmware_version(self) -> dict:
        """Return the Integro encoder firmware version."""
        return self._get(f"devices/{self.device_ref}/get-integro-encoder-firmware-version")

    def readout_integro_integrated_encoder_error(self) -> dict:
        """Read and parse the error register from the Integro integrated encoder."""
        return self._get(f"devices/{self.device_ref}/readout-integro-integrated-encoder-error")

    # ------------------------------------------------------------------ #
    # Kubler encoder                                                       #
    # ------------------------------------------------------------------ #

    def run_kubler_encoder_register_communication_os_command(
        self,
        rw: int | None = None,
        register_address: int | None = None,
        register_length: int | None = None,
        register_write_value: int | None = None,
        command_timeout: int | None = None,
        response_polling_interval: int | None = None,
        os_command_mode: bool | None = None,
    ) -> dict:
        """Read (rw=0) or write (rw=1) a Kubler encoder register via OS command."""
        return self._get(
            f"devices/{self.device_ref}/run-kubler-encoder-register-communication-os-command",
            self._build_params(
                rw=rw,
                register_address=register_address,
                register_length=register_length,
                register_write_value=register_write_value,
                command_timeout=command_timeout,
                response_polling_interval=response_polling_interval,
                os_command_mode=os_command_mode,
            ),
        )

    def reset_kubler_encoder_multiturn_position(self) -> dict:
        """Reset the Kubler encoder multiturn position to 0."""
        return self._get(f"devices/{self.device_ref}/reset-kubler-encoder-multiturn-position")

    # ------------------------------------------------------------------ #
    # OS commands                                                          #
    # ------------------------------------------------------------------ #

    def run_os_command(
        self,
        command: str,
        data: bytes | None = None,
        command_timeout: int | None = None,
        response_polling_interval: int | None = None,
        os_command_mode: str | bool | None = None,
        read_fs_buffer: bool | None = None,
        fs_buffer_read_write_timeout: int | None = None,
    ) -> dict:
        """Execute an OS command on the device.

        command: comma-separated byte values, e.g. "0,0,0,0,0,0,0,0".
        data: optional filesystem buffer content (octet-stream).
        """
        return self._post(
            f"devices/{self.device_ref}/run-os-command",
            params=self._build_params(
                command=command,
                command_timeout=command_timeout,
                response_polling_interval=response_polling_interval,
                os_command_mode=os_command_mode,
                read_fs_buffer=read_fs_buffer,
                fs_buffer_read_write_timeout=fs_buffer_read_write_timeout,
            ),
            data=data,
        )

    # ------------------------------------------------------------------ #
    # SMM (Safe Motion Module)                                             #
    # ------------------------------------------------------------------ #

    def configure_smm(
        self,
        config_csv: bytes,
        username: str | None = None,
        password: str | None = None,
        request_timeout: int | None = None,
    ) -> str:
        """Load, verify and validate SMM parameters from a CSV file.

        Returns the safety parameters report as plain text.
        Default credentials: username="Test", password="SomanetSMM".
        """
        return self._post(
            f"devices/{self.device_ref}/configure-smm",
            params=self._build_params(
                username=username,
                password=password,
                request_timeout=request_timeout,
            ),
            data=config_csv,
        )

    def update_smm_software(
        self,
        firmware: bytes,
        username: str | None = None,
        password: str | None = None,
        crc: str | None = None,
        chunk_size: int | None = None,
        command_timeout: int | None = None,
        response_polling_interval: int | None = None,
        fs_buffer_read_write_timeout: int | None = None,
    ) -> None:
        """Update the SMM software using the provided binary firmware file."""
        # API uses camelCase for these params
        params: dict[str, Any] = {}
        if username is not None:
            params["username"] = username
        if password is not None:
            params["password"] = password
        if crc is not None:
            params["crc"] = crc
        if chunk_size is not None:
            params["chunkSize"] = chunk_size
        if command_timeout is not None:
            params["commandTimeout"] = command_timeout
        if response_polling_interval is not None:
            params["responsePollingInterval"] = response_polling_interval
        if fs_buffer_read_write_timeout is not None:
            params["fsBufferReadWriteTimeout"] = fs_buffer_read_write_timeout
        self._post(f"devices/{self.device_ref}/update-smm-software", params=params, data=firmware)

    def update_smm_software_to_encrypted(
        self,
        firmware: bytes,
        username: str | None = None,
        password: str | None = None,
        crc: str | None = None,
        chunk_size: int | None = None,
        command_timeout: int | None = None,
        response_polling_interval: int | None = None,
        fs_buffer_read_write_timeout: int | None = None,
    ) -> None:
        """Update the SMM software to an encrypted version."""
        # API uses camelCase for these params
        params: dict[str, Any] = {}
        if username is not None:
            params["username"] = username
        if password is not None:
            params["password"] = password
        if crc is not None:
            params["crc"] = crc
        if chunk_size is not None:
            params["chunkSize"] = chunk_size
        if command_timeout is not None:
            params["commandTimeout"] = command_timeout
        if response_polling_interval is not None:
            params["responsePollingInterval"] = response_polling_interval
        if fs_buffer_read_write_timeout is not None:
            params["fsBufferReadWriteTimeout"] = fs_buffer_read_write_timeout
        self._post(
            f"devices/{self.device_ref}/update-smm-software-to-encrypted",
            params=params,
            data=firmware,
        )

    # ------------------------------------------------------------------ #
    # Monitoring                                                           #
    # ------------------------------------------------------------------ #

    def start_monitoring(self, request_timeout: int | None = None) -> None:
        """Start a data monitoring session; data accumulates until stop_monitoring is called."""
        self._get(
            f"devices/{self.device_ref}/monitoring/start",
            self._build_params(request_timeout=request_timeout),
        )

    def get_monitoring_data(self) -> str:
        """Return collected monitoring data as CSV (header row + value rows)."""
        return self._get(f"devices/{self.device_ref}/monitoring/data")

    def stop_monitoring(self) -> None:
        """Stop the active monitoring session (data remains readable until a new session starts)."""
        self._get(f"devices/{self.device_ref}/monitoring/stop")
