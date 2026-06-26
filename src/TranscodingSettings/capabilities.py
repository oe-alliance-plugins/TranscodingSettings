# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only

from glob import glob
from os import listdir
from os.path import basename, exists, isdir, isfile, join
from re import split as re_split

from Components.SystemInfo import BoxInfo


FEATURE_NODES = {
	"enable": ("enable",),
	"automode": ("automode",),
	"bitrate": ("bitrate",),
	"framerate": ("framerate",),
	"resolution": ("display_format", "resolution"),
	"width": ("width",),
	"height": ("height",),
	"aspectratio": ("aspectratio",),
	"interlaced": ("interlaced",),
	"audiocodec": ("audio_codec", "acodec"),
	"videocodec": ("video_codec", "vcodec"),
	"gopframeb": ("gop_frameb",),
	"gopframep": ("gop_framep",),
	"level": ("level",),
	"profile": ("profile",),
	"apply": ("apply",),
	"decoder": ("decoder", "demux"),
}

LIVE555_BINARY = "/usr/bin/enigma2-live555"

STREAM_SERVER_METHODS = (
	"enableHLS",
	"enableRTSP",
	"setAspectRatio",
	"setAudioBitrate",
	"setBFrames",
	"setFramerate",
	"setGopLength",
	"setGopOnSceneChange",
	"setInputMode",
	"setInterlaced",
	"setLevel",
	"setOpenGop",
	"setPFrames",
	"setProfile",
	"setResolution",
	"setServiceRef",
	"setSlices",
	"setVideoBitrate",
	"setVideoCodec",
)

STREAM_SERVER_OPTIONAL_METHODS = (
	"setEncoderIndex",
)

STREAM_SERVER_SIGNALS = (
	"availabilityChanged",
	"sourceStateChanged",
	"rtspClientCountChanged",
	"hlsClientCountChanged",
	"uriParametersChanged",
	"dbusError",
)

STREAM_SERVER_CONSTANTS = (
	"INPUT_MODE_LIVE",
	"INPUT_MODE_HDMI_IN",
	"INPUT_MODE_BACKGROUND",
)


class EncoderCapability:
	"""Description of one physical or virtual encoder exported by the receiver."""

	def __init__(self, index, proc_path, dev_root="/dev", dream=False):
		self.index = int(index)
		self.proc_path = proc_path
		self.dev_root = dev_root
		self.nodes = {}
		self.current = {}
		self.choices = {}
		self.choice_labels = {}
		self.is_dream = bool(dream)
		self.is_bcm = exists(join(dev_root, "bcm_enc%d" % self.index))
		self.is_native = exists(join(dev_root, "encoder%d" % self.index))
		self._probe()

	@property
	def backend(self):
		if self.is_dream:
			return "dream"
		if self.is_bcm:
			return "bcm"
		if self.is_native or self.has("videocodec") or self.has("width"):
			return "native"
		return "proc"

	@property
	def is_limited_bcm(self):
		return self.is_bcm and not any(self.has(feature) for feature in (
			"resolution", "width", "height", "aspectratio", "videocodec", "audiocodec"
		))

	def _read(self, path):
		try:
			with open(path, "r", encoding="UTF-8", errors="ignore") as handle:
				return handle.read().strip()
		except OSError:
			return ""

	def _parse_choices(self, value):
		values = []
		labels = {}
		for token in re_split(r"[\s,;|]+", value or ""):
			token = token.strip().strip("[](){}'\"")
			if not token:
				continue
			choice = token
			label = token
			if ":" in token:
				choice, label = token.split(":", 1)
				choice = choice.strip()
				label = label.strip() or choice
			if choice and choice not in values:
				values.append(choice)
				labels[choice] = label
		return values, labels

	def _probe(self):
		for feature, node_names in FEATURE_NODES.items():
			for node_name in node_names:
				path = join(self.proc_path, node_name)
				if exists(path):
					self.nodes[feature] = path
					self.current[feature] = self._read(path)
					choices_path = "%s_choices" % path
					if exists(choices_path):
						values, labels = self._parse_choices(self._read(choices_path))
						self.choices[feature] = values
						self.choice_labels[feature] = labels
					break

	def has(self, feature):
		return feature in self.nodes

	def node(self, feature):
		return self.nodes.get(feature)

	def values(self, feature):
		return list(self.choices.get(feature, ()))

	def labels(self, feature):
		return dict(self.choice_labels.get(feature, {}))

	def value(self, feature, default=""):
		return self.current.get(feature, default)

	def supports_stream_codec(self, codec):
		codec = str(codec).lower()
		if self.is_dream:
			return codec == "h264"
		values = [str(value).lower() for value in self.values("videocodec")]
		if values:
			return codec in values or (codec == "h265" and "hevc" in values)
		if self.has("videocodec") and not self.is_bcm:
			return codec in ("h264", "h265")
		return codec == "h264"

	@property
	def usable(self):
		"""Return whether this entry represents an actual transcoding encoder."""
		return bool(
			self.is_dream
			or self.is_bcm
			or self.is_native
			or self.has("bitrate")
			or self.has("videocodec")
			or (self.has("width") and self.has("height"))
		)


class TranscodingCapabilities:
	"""Probe encoders and optional streaming-server facilities.

	The probe reads hardware interfaces only. It does not inspect any other
	transcoding plugin, configuration namespace, inetd entry or proxy service.
	Port 8002 is exposed as a BCM hardware path; every setting belongs exclusively
	to this plugin.
	"""

	def __init__(self, proc_root="/proc/stb/encoder", dev_root="/dev", live555_binary=LIVE555_BINARY):
		self.proc_root = proc_root
		self.dev_root = dev_root
		self.live555_binary = live555_binary
		self.encoders = []
		self._probe_encoders()
		self.supported = bool(self.encoders)
		self.has_port_8001 = self.supported
		self.has_port_8002 = any(encoder.is_bcm for encoder in self.encoders)
		self.has_live555_binary = isfile(self.live555_binary)
		self.has_stream_server_api = self._probe_stream_server_api()
		self.has_encoder_selection_api = self._probe_optional_stream_server_method("setEncoderIndex")
		self.has_hdmi_input = self._probe_hdmi_input()
		self.has_live_streaming = self.has_port_8001 and self.has_live555_binary and self.has_stream_server_api
		self._publish_box_info()

	def _probe_encoders(self):
		indices = set()
		if isdir(self.proc_root):
			try:
				for entry in listdir(self.proc_root):
					if entry.isdigit() and isdir(join(self.proc_root, entry)):
						indices.add(int(entry))
			except OSError:
				pass
		for pattern in ("bcm_enc*", "encoder*"):
			for path in glob(join(self.dev_root, pattern)):
				name = basename(path)
				suffix = name[len("bcm_enc"):] if name.startswith("bcm_enc") else name[len("encoder"):]
				if suffix.isdigit():
					indices.add(int(suffix))
		dream = exists(join(self.dev_root, "venc0")) and exists(join(self.dev_root, "aenc0"))
		if dream:
			indices.add(0)
		for index in sorted(indices):
			# The supported receiver families expose at most encoder 0 and 1.
			# Do not advertise untested auxiliary devices as configurable encoders.
			if index > 1:
				continue
			encoder = EncoderCapability(index, join(self.proc_root, str(index)), self.dev_root, dream=dream and index == 0)
			if encoder.usable:
				self.encoders.append(encoder)

	def _probe_stream_server_api(self):
		try:
			from enigma import eStreamServer
			server = eStreamServer.getInstance()
			if server is None:
				return False
			if not all(hasattr(eStreamServer, name) for name in STREAM_SERVER_CONSTANTS):
				return False
			if not all(callable(getattr(server, method, None)) for method in STREAM_SERVER_METHODS):
				return False
			for signal in STREAM_SERVER_SIGNALS:
				value = getattr(server, signal, None)
				if value is None or not callable(getattr(value, "get", None)):
					return False
			return True
		except Exception:
			return False

	def _probe_optional_stream_server_method(self, method):
		if not self.has_stream_server_api:
			return False
		try:
			from enigma import eStreamServer
			server = eStreamServer.getInstance()
			return server is not None and callable(getattr(server, method, None))
		except Exception:
			return False

	def _probe_hdmi_input(self):
		return bool(BoxInfo.getItem("hdmifhdin", False) or BoxInfo.getItem("hdmihdin", False))

	def _publish_box_info(self):
		values = {
			"HasTranscodingSettings": self.supported,
			"TranscodingSettingsEncoderCount": len(self.encoders),
			"TranscodingSettingsPort8001": self.has_port_8001,
			"TranscodingSettingsPort8002": self.has_port_8002,
			"TranscodingSettingsLive555": self.has_live_streaming,
			"TranscodingSettingsHDMIInput": self.has_hdmi_input,
			"TranscodingSettingsEncoderSelection": self.has_encoder_selection_api,
		}
		for key, value in values.items():
			BoxInfo.setMutableItem(key, value)

	def encoder(self, index):
		index = int(index)
		for encoder in self.encoders:
			if encoder.index == index:
				return encoder
		return None

	def encoder_indices(self):
		return [encoder.index for encoder in self.encoders]

	def port_choices(self):
		choices = []
		if self.has_port_8001:
			choices.append(("8001", "8001 - Enigma2 stream server"))
		if self.has_port_8002:
			choices.append(("8002", "8002 - BCM transcoding proxy"))
		return choices
