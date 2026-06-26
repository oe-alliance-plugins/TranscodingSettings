# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only

from os import kill, listdir, readlink, unlink
from os.path import isfile, realpath
from subprocess import DEVNULL, call
from time import monotonic, sleep
from urllib.parse import parse_qs

from Components.config import config

from .configuration import (
	CAPABILITIES,
	CAPABILITY_BY_INDEX,
	ENCODER_AUTO,
	encoder_preference_index,
	encoder_profile_index,
	get_encoder_config,
	live_resolution_dimensions,
	INPUT_MODE_BACKGROUND,
	INPUT_MODE_HDMI_IN,
	INPUT_MODE_LIVE,
)

try:
	from enigma import eServiceCenter, eServiceReference, eStreamServer, getBestPlayableServiceReference, iPlayableService, iServiceInformation
except Exception:
	eServiceCenter = None
	eServiceReference = None
	eStreamServer = None
	getBestPlayableServiceReference = None
	iPlayableService = None
	iServiceInformation = None

try:
	from ServiceReference import hdmiInServiceRef
except Exception:
	hdmiInServiceRef = None


LIVE555_INIT_SCRIPT = "/etc/init.d/enigma2-live555"
LIVE555_PIDFILE = "/var/run/enigma2-live555.pid"
LIVE555_START_TIMEOUT = 2.0
LIVE555_STOP_TIMEOUT = 2.0


def live_streaming_enabled():
	"""Return whether the saved settings require the live555 daemon."""
	return bool(
		config.plugins.transcodingsettings.enabled.value
		and str(config.plugins.transcodingsettings.port.value) == "8001"
		and (
			config.plugins.transcodingsettings.hls.enabled.value
			or config.plugins.transcodingsettings.rtsp.enabled.value
		)
	)


def _pid_running(pid):
	try:
		pid = int(pid)
		if pid <= 0:
			return False
		kill(pid, 0)
		return True
	except (OSError, TypeError, ValueError):
		return False


def _pid_matches_daemon(pid):
	if not _pid_running(pid):
		return False
	binary = realpath(CAPABILITIES.live555_binary)
	try:
		target = readlink("/proc/%s/exe" % int(pid))
		if target.endswith(" (deleted)"):
			target = target[:-10]
		if realpath(target) == binary:
			return True
	except OSError:
		pass
	try:
		with open("/proc/%s/cmdline" % int(pid), "rb") as handle:
			command = handle.read().split(b"\0", 1)[0].decode("UTF-8", "ignore")
		return realpath(command) == binary
	except OSError:
		return False


def _pid_from_file():
	try:
		with open(LIVE555_PIDFILE, "r", encoding="ASCII") as handle:
			pid = int(handle.read().strip())
		return pid if _pid_matches_daemon(pid) else None
	except (OSError, TypeError, ValueError):
		return None


def _find_daemon_pid():
	pid = _pid_from_file()
	if pid is not None:
		return pid
	try:
		entries = listdir("/proc")
	except OSError:
		return None
	for entry in entries:
		if entry.isdigit() and _pid_matches_daemon(entry):
			return int(entry)
	return None


def live555_daemon_running():
	return _find_daemon_pid() is not None


def _remove_stale_pidfile():
	if _pid_from_file() is None:
		try:
			unlink(LIVE555_PIDFILE)
		except OSError:
			pass


def _run_init_action(action):
	if not isfile(LIVE555_INIT_SCRIPT):
		return "Missing %s." % LIVE555_INIT_SCRIPT
	try:
		result = call([LIVE555_INIT_SCRIPT, action], stdout=DEVNULL, stderr=DEVNULL)
	except OSError as error:
		return "Unable to %s enigma2-live555: %s" % (action, error)
	if result:
		return "The enigma2-live555 init script returned status %d while trying to %s the daemon." % (result, action)
	return None


def start_live555_daemon():
	"""Start the daemon only when HLS or RTSP is configured."""
	if live555_daemon_running():
		return None
	_remove_stale_pidfile()
	error = _run_init_action("start")
	if error:
		return error
	deadline = monotonic() + LIVE555_START_TIMEOUT
	while monotonic() < deadline:
		if live555_daemon_running():
			return None
		sleep(0.1)
	return "enigma2-live555 did not start."


def stop_live555_daemon():
	"""Stop the manually managed daemon and remove a stale PID file."""
	pid = _find_daemon_pid()
	if pid is None:
		_remove_stale_pidfile()
		return None
	# A manually started process may not have a PID file. Supply it to the init
	# script so that start-stop-daemon can still stop the correct executable.
	if _pid_from_file() is None:
		try:
			with open(LIVE555_PIDFILE, "w", encoding="ASCII") as handle:
				handle.write(str(pid))
		except OSError:
			pass
	error = _run_init_action("stop")
	if error:
		return error
	deadline = monotonic() + LIVE555_STOP_TIMEOUT
	while monotonic() < deadline:
		if not live555_daemon_running():
			_remove_stale_pidfile()
			return None
		sleep(0.1)
	return "enigma2-live555 did not stop."


FRAME_RATE_MAP = {
	"23.976": 23,
	"24": 24,
	"25": 25,
	"29.97": 29,
	"30": 30,
	"50": 50,
	"59.94": 59,
	"60": 60,
	"23976": 23,
	"24000": 24,
	"25000": 25,
	"29970": 29,
	"30000": 30,
	"50000": 50,
	"59940": 59,
	"60000": 60,
}


class LiveStreamController:
	"""Bridge the new configuration namespace to eStreamServer/live555."""

	ENCODER_TARGET = 2

	def __init__(self, session=None):
		self.session = session
		self.server = None
		self.uriServiceRef = ""
		self.uriEncoder = None
		self.encoderService = None
		self._signals = []
		self._navigationConnected = False
		self._open_server()

	def _log(self, message):
		print("[TranscodingSettings] %s" % message)

	def _open_server(self):
		if not CAPABILITIES.has_live555_binary or eStreamServer is None:
			return
		try:
			self.server = eStreamServer.getInstance()
		except Exception as error:
			self._log("Unable to access eStreamServer: %s" % error)
			self.server = None
		if self.server is None:
			return
		self._connect_signal("availabilityChanged", self._availability_changed)
		self._connect_signal("sourceStateChanged", self._source_state_changed)
		self._connect_signal("rtspClientCountChanged", self._client_count_changed)
		self._connect_signal("hlsClientCountChanged", self._client_count_changed)
		self._connect_signal("uriParametersChanged", self._uri_parameters_changed)
		self._connect_signal("dbusError", self._dbus_error)
		self._connect_navigation()

	def _connect_signal(self, name, callback):
		try:
			callbacks = getattr(self.server, name).get()
			if callback not in callbacks:
				callbacks.append(callback)
				self._signals.append((callbacks, callback))
		except Exception:
			pass

	def _connect_navigation(self):
		if self._navigationConnected or self.session is None or not hasattr(self.session, "nav"):
			return
		try:
			if self._navigation_event not in self.session.nav.event:
				self.session.nav.event.append(self._navigation_event)
			self._navigationConnected = True
		except Exception:
			pass

	def shutdown(self):
		for callbacks, callback in self._signals:
			try:
				if callback in callbacks:
					callbacks.remove(callback)
			except Exception:
				pass
		self._signals = []
		if self._navigationConnected and self.session is not None:
			try:
				if self._navigation_event in self.session.nav.event:
					self.session.nav.event.remove(self._navigation_event)
			except Exception:
				pass
		self._navigationConnected = False
		self.stop_encoder_service()

	@property
	def available(self):
		return self.server is not None and CAPABILITIES.has_live555_binary and CAPABILITIES.has_stream_server_api

	def _call(self, method, *args):
		if self.server is None or not hasattr(self.server, method):
			return None
		try:
			return getattr(self.server, method)(*args)
		except Exception as error:
			self._log("%s failed: %s" % (method, error))
			return None

	def _endpoint_enabled(self, endpoint):
		return bool(
			config.plugins.transcodingsettings.enabled.value
			and str(config.plugins.transcodingsettings.port.value) == "8001"
			and self.available
			and endpoint.enabled.value
		)

	def _current_service_ref(self):
		if self.session is None or not hasattr(self.session, "nav"):
			return ""
		try:
			ref = self.session.nav.getCurrentlyPlayingServiceReference()
			ref = self._get_ref(ref)
			return ref.toString() if ref and ref.valid() else ""
		except Exception:
			return ""

	def _hdmi_service_ref(self):
		if not CAPABILITIES.has_hdmi_input or hdmiInServiceRef is None:
			return ""
		try:
			ref = hdmiInServiceRef()
			return ref.toString() if ref and ref.valid() else ""
		except Exception:
			return ""

	def _configured_input(self):
		try:
			mode = int(config.plugins.transcodingsettings.live.source.value)
		except (TypeError, ValueError):
			mode = int(INPUT_MODE_LIVE)
		if mode == int(INPUT_MODE_HDMI_IN) and CAPABILITIES.has_hdmi_input:
			service_ref = self._hdmi_service_ref()
			if service_ref:
				return mode, service_ref
		return int(INPUT_MODE_LIVE), self._current_service_ref()

	def _selected_index(self):
		value = self.uriEncoder if self.uriEncoder is not None else config.plugins.transcodingsettings.encoder.value
		return encoder_preference_index(value)

	def _framerate_value(self, value):
		value = str(value or "25000")
		if "/" in value:
			value = value.split("/", 1)[0]
		if value in FRAME_RATE_MAP:
			return FRAME_RATE_MAP[value]
		try:
			number = int(value)
			if number <= 0:
				return 25
			if number >= 1000:
				return number // 1000
			return number
		except (TypeError, ValueError):
			return 25

	def _choice_values(self, element):
		try:
			return [str(value) for value in element.choices]
		except Exception:
			return []

	def _choice_value(self, element, requested=None):
		configured = str(element.value)
		if requested is None:
			return configured
		requested = str(requested)
		return requested if requested in self._choice_values(element) else configured

	def _video_bitrate(self, entry, requested=None):
		try:
			value = int(requested if requested is not None else entry.bitrate.value)
		except (TypeError, ValueError):
			value = 1500000
		# Dream-compatible URI values are in kbit/s; encoder settings are in bit/s.
		value_bps = value * 1000 if 0 < value <= 20000 else value
		allowed = []
		for choice in self._choice_values(entry.bitrate):
			try:
				choice = int(choice)
			except (TypeError, ValueError):
				continue
			if choice > 0:
				allowed.append(choice)
		if allowed and value_bps not in allowed:
			try:
				configured = int(entry.bitrate.value)
			except (TypeError, ValueError):
				configured = 0
			value_bps = configured if configured in allowed else min(allowed, key=lambda item: abs(item - 1500000))
		# enigma2-live555/eStreamServer accepts 256..20000 kbit/s.
		return max(256, min(20000, int(value_bps // 1000)))

	def _audio_bitrate(self, value):
		try:
			value = int(value)
		except (TypeError, ValueError):
			value = 96
		if value > 1000:
			value //= 1000
		return max(32, min(448, value))

	def _resolution(self, index, entry, requested=None):
		configured = str(entry.resolution.value)
		if requested:
			try:
				key = "%dx%d" % (int(requested[0]), int(requested[1]))
			except (TypeError, ValueError, IndexError):
				key = ""
			if key in self._choice_values(entry.resolution):
				configured = key
		return live_resolution_dimensions(index, configured)

	def _apply_encoder_values(self, index=None, overrides=None):
		if self.server is None:
			return
		preferred_index = self._selected_index() if index is None else encoder_preference_index(index)
		profile_index = encoder_profile_index(preferred_index)
		entry = get_encoder_config(profile_index)
		if entry is None:
			return
		overrides = overrides or {}
		bitrate = self._video_bitrate(entry, overrides.get("bitrate"))
		audio_bitrate = self._audio_bitrate(
			overrides.get("audioBitrate", config.plugins.transcodingsettings.live.audioBitrate.value)
		)
		width, height = self._resolution(profile_index, entry, overrides.get("resolution"))
		codec = str(overrides.get("videoCodec", config.plugins.transcodingsettings.live.videoCodec.value)).lower()
		capability = CAPABILITY_BY_INDEX.get(profile_index)
		if codec == "hevc":
			codec = "h265"
		live_codecs = self._choice_values(config.plugins.transcodingsettings.live.videoCodec)
		if codec not in live_codecs or not capability or not capability.supports_stream_codec(codec):
			codec = "h264"
		framerate_value = self._choice_value(entry.framerate, overrides.get("framerate"))
		framerate = self._framerate_value(framerate_value)
		aspectratio = int(self._choice_value(entry.aspectratio, overrides.get("aspectratio")))
		interlaced = int(self._choice_value(entry.interlaced, overrides.get("interlaced")))

		# Newer Enigma2 stream-server builds can reserve a requested physical
		# encoder. Older builds simply keep their first-free allocation policy.
		if CAPABILITIES.has_encoder_selection_api:
			self._call("setEncoderIndex", preferred_index)

		self._call("setVideoBitrate", bitrate)
		self._call("setAudioBitrate", audio_bitrate)
		self._call("setVideoCodec", codec)
		self._call("setResolution", int(width), int(height))
		self._call("setFramerate", framerate)
		self._call("setAspectRatio", aspectratio)
		self._call("setInterlaced", interlaced)
		self._call("setGopLength", int(config.plugins.transcodingsettings.live.gopLength.value))
		self._call("setGopOnSceneChange", bool(config.plugins.transcodingsettings.live.gopOnSceneChange.value))
		self._call("setOpenGop", bool(config.plugins.transcodingsettings.live.openGop.value))
		self._call("setBFrames", int(config.plugins.transcodingsettings.live.bFrames.value))
		self._call("setPFrames", int(config.plugins.transcodingsettings.live.pFrames.value))
		self._call("setSlices", int(config.plugins.transcodingsettings.live.slices.value))
		self._call("setLevel", int(config.plugins.transcodingsettings.live.level.value))
		self._call("setProfile", int(config.plugins.transcodingsettings.live.profile.value))

	def apply(self):
		if self.server is None:
			return
		effective = bool(live_streaming_enabled() and self.available)
		# Do not touch eStreamServer while both endpoints are disabled. A D-Bus
		# method call can activate the daemon, which would defeat on-demand mode.
		if not effective:
			self.stop_encoder_service()
			return
		self._apply_encoder_values()
		if self.uriServiceRef:
			service_ref = self.uriServiceRef
			input_mode = int(INPUT_MODE_BACKGROUND)
		else:
			input_mode, service_ref = self._configured_input()
		self._call("setInputMode", input_mode)
		self._call("setServiceRef", service_ref)
		self._call(
			"enableRTSP",
			bool(config.plugins.transcodingsettings.rtsp.enabled.value),
			config.plugins.transcodingsettings.rtsp.path.value,
			int(config.plugins.transcodingsettings.rtsp.port.value),
			config.plugins.transcodingsettings.rtsp.user.value,
			config.plugins.transcodingsettings.rtsp.password.value,
		)
		self._call(
			"enableHLS",
			bool(config.plugins.transcodingsettings.hls.enabled.value),
			config.plugins.transcodingsettings.hls.path.value,
			int(config.plugins.transcodingsettings.hls.port.value),
			config.plugins.transcodingsettings.hls.user.value,
			config.plugins.transcodingsettings.hls.password.value,
		)

	def disable(self):
		"""Disable both endpoints before the daemon is stopped."""
		if self.server is not None:
			self._call(
				"enableRTSP",
				False,
				config.plugins.transcodingsettings.rtsp.path.value,
				int(config.plugins.transcodingsettings.rtsp.port.value),
				config.plugins.transcodingsettings.rtsp.user.value,
				config.plugins.transcodingsettings.rtsp.password.value,
			)
			self._call(
				"enableHLS",
				False,
				config.plugins.transcodingsettings.hls.path.value,
				int(config.plugins.transcodingsettings.hls.port.value),
				config.plugins.transcodingsettings.hls.user.value,
				config.plugins.transcodingsettings.hls.password.value,
			)
		self.stop_encoder_service()

	def _availability_changed(self, available):
		if available:
			self.apply()
		else:
			self.stop_encoder_service()

	def _source_state_changed(self, state):
		if state and self.uriServiceRef and self._dream_backend():
			self._start_encoder_service(self.uriServiceRef)
		elif not state:
			self.stop_encoder_service()

	def _client_count_changed(self, unused_count, unused_client):
		# The HLS playlist request carries the service reference, while segment
		# requests normally do not. Keep the selected service until another URI
		# explicitly replaces it; clearing it at client-count zero breaks the
		# segment window between HTTP requests.
		pass

	def _dbus_error(self, error):
		self._log("Live555 D-Bus error: %s" % error)

	def _navigation_event(self, event):
		if iPlayableService is None or event != iPlayableService.evStart or self.uriServiceRef:
			return
		if str(config.plugins.transcodingsettings.live.source.value) != str(INPUT_MODE_LIVE):
			return
		if (
			self._endpoint_enabled(config.plugins.transcodingsettings.hls)
			or self._endpoint_enabled(config.plugins.transcodingsettings.rtsp)
		):
			service_ref = self._current_service_ref()
			if service_ref:
				self._call("setServiceRef", service_ref)

	def _parameter(self, parameters, *names):
		for name in names:
			value = parameters.get(name, [""])[0]
			if isinstance(value, bytes):
				value = value.decode("UTF-8", "ignore")
			value = str(value or "")
			if value:
				return value
		return ""

	def _integer_parameter(self, parameters, *names):
		try:
			return int(self._parameter(parameters, *names))
		except (TypeError, ValueError):
			return None

	def _uri_parameters_changed(self, parameters):
		params = parse_qs(str(parameters or "").lstrip("?"))
		encoder_value = self._parameter(params, "encoder").strip().lower()
		if encoder_value in (ENCODER_AUTO, "-1"):
			index = -1
		else:
			try:
				index = int(encoder_value)
			except (TypeError, ValueError):
				index = self._selected_index()
			if index not in CAPABILITY_BY_INDEX:
				index = self._selected_index()
		self.uriEncoder = index
		service_ref = self._parameter(params, "ref", "sref", "serviceref")
		if service_ref:
			ref = self._get_ref(eServiceReference(service_ref)) if eServiceReference else None
			if ref and ref.valid():
				self.uriServiceRef = ref.toString()

		overrides = {}
		bitrate = self._integer_parameter(params, "video_bitrate", "bitrate")
		if bitrate and bitrate > 0:
			overrides["bitrate"] = bitrate
		audio_bitrate = self._integer_parameter(params, "audio_bitrate", "abitrate")
		if audio_bitrate and audio_bitrate > 0:
			overrides["audioBitrate"] = audio_bitrate
		codec = self._parameter(params, "video_codec", "vcodec").lower()
		if codec in ("h264", "h265", "hevc"):
			overrides["videoCodec"] = codec
		width = self._integer_parameter(params, "width")
		height = self._integer_parameter(params, "height")
		resolution = self._parameter(params, "resolution")
		if (not width or not height) and "x" in resolution:
			try:
				width, height = [int(value) for value in resolution.split("x", 1)]
			except (TypeError, ValueError):
				width = height = None
		if width and height and width > 0 and height > 0:
			overrides["resolution"] = (width, height)
		framerate = self._parameter(params, "framerate")
		if framerate:
			overrides["framerate"] = framerate
		aspectratio = self._integer_parameter(params, "aspectratio")
		if aspectratio in (0, 1, 2):
			overrides["aspectratio"] = aspectratio
		interlaced = self._integer_parameter(params, "interlaced")
		if interlaced in (0, 1):
			overrides["interlaced"] = interlaced

		self._apply_encoder_values(index, overrides)
		if self.uriServiceRef:
			self._call("setInputMode", int(INPUT_MODE_BACKGROUND))
			self._call("setServiceRef", self.uriServiceRef)
			if self._dream_backend():
				self._start_encoder_service(self.uriServiceRef)

	def _dream_backend(self):
		return any(capability.is_dream for capability in CAPABILITIES.encoders)

	def _get_ref(self, service):
		if service and getBestPlayableServiceReference is not None and service.flags & eServiceReference.isGroup:
			return getBestPlayableServiceReference(service, eServiceReference())
		return service

	def _start_encoder_service(self, service_ref):
		if not self._dream_backend() or eServiceCenter is None or eServiceReference is None:
			return False
		try:
			if hasattr(self.server, "hasExternalEncoderClients") and self.server.hasExternalEncoderClients():
				self._log("Dream encoder is already used by another transcoding client")
				return False
			ref = self._get_ref(eServiceReference(service_ref))
			if not ref or not ref.valid():
				return False
			if self.encoderService and iServiceInformation is not None:
				info = self.encoderService.info()
				current = info and info.getInfoString(iServiceInformation.sServiceref)
				if current == ref.toString():
					return True
			self.stop_encoder_service()
			service = eServiceCenter.getInstance().play(ref)
			if service and not service.setTarget(self.ENCODER_TARGET):
				service.start()
				self.encoderService = service
				return True
		except Exception as error:
			self._log("Unable to start Dream encoder service: %s" % error)
		return False

	def stop_encoder_service(self):
		if self.encoderService:
			try:
				self.encoderService.stop()
			except Exception:
				pass
		self.encoderService = None


_controller = None


def get_live_stream_controller(session=None, create=True):
	global _controller
	if _controller is None and create and CAPABILITIES.has_live_streaming and eStreamServer is not None:
		_controller = LiveStreamController(session=session)
	elif _controller is not None and session is not None:
		_controller.session = session
		_controller._connect_navigation()
	return _controller


def stop_live_stream_controller():
	global _controller
	if _controller is not None:
		_controller.shutdown()
	_controller = None


def apply_live_streaming_state(session=None):
	"""Synchronize daemon state and HLS/RTSP endpoints with the plugin config."""
	errors = []
	if not live_streaming_enabled():
		running = live555_daemon_running()
		controller = get_live_stream_controller(session, create=False)
		if running:
			controller = controller or get_live_stream_controller(session, create=True)
			if controller is not None:
				controller.disable()
		stop_live_stream_controller()
		error = stop_live555_daemon()
		if error:
			errors.append(error)
		return errors

	if not CAPABILITIES.has_live555_binary:
		return ["HLS/RTSP requires /usr/bin/enigma2-live555."]
	if not CAPABILITIES.has_stream_server_api:
		return ["HLS/RTSP requires the Enigma2 eStreamServer API."]
	error = start_live555_daemon()
	if error:
		return [error]
	controller = get_live_stream_controller(session, create=True)
	if controller is None:
		return ["Unable to initialize the HLS/RTSP controller."]
	controller.apply()
	return errors


def shutdown_live_streaming():
	"""Stop live streaming on Enigma2 shutdown or GUI restart."""
	errors = []
	running = live555_daemon_running()
	controller = get_live_stream_controller(create=False)
	if running:
		controller = controller or get_live_stream_controller(create=True)
		if controller is not None:
			controller.disable()
	stop_live_stream_controller()
	error = stop_live555_daemon()
	if error:
		errors.append(error)
	return errors
