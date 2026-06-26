# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only

from os.path import exists, join

from Components.config import config

from . import _
from .configuration import (
	CAPABILITIES,
	driver_resolution_value,
	encoder_capabilities_for_selection,
	encoder_preference_index,
	get_encoder_config,
	resolution_dimensions,
)


class TranscodingBackend:
	"""Apply the new plugin settings to the receiver encoder proc nodes."""

	def __init__(self, capabilities=CAPABILITIES):
		self.capabilities = capabilities

	def _write(self, path, value, errors):
		if not path or not exists(path):
			return False
		try:
			with open(path, "w", encoding="UTF-8") as handle:
				handle.write(str(value))
			return True
		except OSError as error:
			errors.append(f"Unable to write {path}: {error}")
			return False

	def _write_feature(self, capability, feature, value, errors):
		return self._write(capability.node(feature), value, errors) if capability.has(feature) else False

	def normalize(self):
		# HLS and RTSP stay configured while port 8002 is selected, but are only
		# activated by the port-8001/live555 backend.
		config.plugins.transcodingsettings.hls.path.value = str(config.plugins.transcodingsettings.hls.path.value or "stream").strip("/") or "stream"
		config.plugins.transcodingsettings.rtsp.path.value = str(config.plugins.transcodingsettings.rtsp.path.value or "stream").strip("/") or "stream"

	def validate(self):
		errors = []
		self.normalize()
		print(config.plugins.transcodingsettings.port.value, type(config.plugins.transcodingsettings.port.value))
		print([(choice[0], type(choice[0])) for choice in self.capabilities.port_choices()])
		if config.plugins.transcodingsettings.port.value not in [choice[0] for choice in self.capabilities.port_choices()]:
			errors.append(_("The selected transcoding port is not available on this receiver."))
		live_enabled = bool(
			config.plugins.transcodingsettings.enabled.value
			and config.plugins.transcodingsettings.port.value == 8001
			and (config.plugins.transcodingsettings.hls.enabled.value or config.plugins.transcodingsettings.rtsp.enabled.value)
		)
		if live_enabled:
			if not self.capabilities.has_live555_binary:
				errors.append(_("HLS/RTSP requires /usr/bin/enigma2-live555."))
			if not self.capabilities.has_stream_server_api:
				errors.append(_("HLS/RTSP requires the Enigma2 eStreamServer API."))
			if (
				config.plugins.transcodingsettings.hls.enabled.value
				and config.plugins.transcodingsettings.rtsp.enabled.value
				and config.plugins.transcodingsettings.hls.port.value == config.plugins.transcodingsettings.rtsp.port.value
			):
				errors.append(_("HLS and RTSP must use different listening ports."))
			for name, endpoint in (
				("HLS", config.plugins.transcodingsettings.hls),
				("RTSP", config.plugins.transcodingsettings.rtsp),
			):
				if endpoint.enabled.value and endpoint.port.value in (8001, 8002):
					errors.append(_("%s cannot listen on transcoding port %d.") % (name, endpoint.port.value))
		possible_encoders = encoder_capabilities_for_selection(config.plugins.transcodingsettings.encoder.value)
		if live_enabled and any(
			not capability.supports_stream_codec(config.plugins.transcodingsettings.live.videoCodec.value)
			for capability in possible_encoders
		):
			if encoder_preference_index(config.plugins.transcodingsettings.encoder.value) < 0:
				errors.append(_("The selected codec is not supported by every encoder that Auto may allocate for HLS/RTSP."))
			else:
				errors.append(_("The selected encoder does not support this codec for HLS/RTSP."))
		return errors

	def _apply_encoder(self, capability, errors):
		entry = get_encoder_config(capability.index)
		if entry is None:
			return
		self._write_feature(capability, "enable", "enable", errors)
		self._write_feature(capability, "automode", entry.automode.value, errors)
		self._write_feature(capability, "bitrate", entry.bitrate.value, errors)
		self._write_feature(capability, "framerate", entry.framerate.value, errors)
		width, height = resolution_dimensions(entry.resolution.value)
		if capability.has("resolution"):
			driver_value = driver_resolution_value(capability.index, entry.resolution.value)
			self._write_feature(capability, "resolution", driver_value, errors)
			# BCM drivers use width/height only with display_format=custom.
			if driver_value == "custom":
				self._write_feature(capability, "width", width, errors)
				self._write_feature(capability, "height", height, errors)
		else:
			self._write_feature(capability, "width", width, errors)
			self._write_feature(capability, "height", height, errors)
		self._write_feature(capability, "aspectratio", entry.aspectratio.value, errors)
		self._write_feature(capability, "interlaced", entry.interlaced.value, errors)
		self._write_feature(capability, "videocodec", entry.videocodec.value, errors)
		self._write_feature(capability, "audiocodec", entry.audiocodec.value, errors)
		self._write_feature(capability, "gopframeb", entry.gopframeb.value, errors)
		self._write_feature(capability, "gopframep", entry.gopframep.value, errors)
		self._write_feature(capability, "level", entry.level.value, errors)
		self._write_feature(capability, "profile", entry.profile.value, errors)
		self._write_feature(capability, "apply", 1, errors)

	def apply(self, validate=True):
		errors = self.validate() if validate else []
		if errors:
			return errors
		global_enable = join(self.capabilities.proc_root, "enable")
		if not config.plugins.transcodingsettings.enabled.value:
			self._write(global_enable, "disable", errors)
			for capability in self.capabilities.encoders:
				self._write_feature(capability, "enable", "disable", errors)
			return errors
		self._write(global_enable, "enable", errors)
		for capability in self.capabilities.encoders:
			self._apply_encoder(capability, errors)
		return errors


backend = TranscodingBackend()
