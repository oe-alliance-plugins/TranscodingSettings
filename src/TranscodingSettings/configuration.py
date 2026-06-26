# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only

from Components.config import (
	ConfigInteger,
	ConfigPassword,
	ConfigSelection,
	ConfigSubsection,
	ConfigText,
	ConfigYesNo,
	config,
)

from . import _
from .capabilities import TranscodingCapabilities


CAPABILITIES = TranscodingCapabilities()
CAPABILITY_BY_INDEX = {encoder.index: encoder for encoder in CAPABILITIES.encoders}
ENCODER_AUTO = "auto"
RESOLUTION_DRIVER_VALUES = {}
_PRESET_APPLYING = set()

RESOLUTION_DIMENSIONS = {
	"160x120": (160, 120),
	"320x240": (320, 240),
	"640x360": (640, 360),
	"720x480": (720, 480),
	"854x480": (854, 480),
	"720x576": (720, 576),
	"768x576": (768, 576),
	"1024x576": (1024, 576),
	"1280x720": (1280, 720),
	"1440x1080": (1440, 1080),
	"1920x1080": (1920, 1080),
}

DRIVER_RESOLUTION_KEYS = {
	"160x120": "160x120",
	"320x240": "320x240",
	"360p": "640x360",
	"480p": "720x480",
	"576p": "720x576",
	"720p": "1280x720",
	"1080p": "1920x1080",
	"720x480": "720x480",
	"854x480": "854x480",
	"720x576": "720x576",
	"768x576": "768x576",
	"1024x576": "1024x576",
	"1280x720": "1280x720",
	"1440x1080": "1440x1080",
	"1920x1080": "1920x1080",
}

RESOLUTION_LABELS = {
	"160x120": "160x120",
	"320x240": "320x240",
	"640x360": "360p (640x360)",
	"720x480": "480p (720x480)",
	"854x480": "480p (854x480)",
	"720x576": "576p (720x576)",
	"768x576": "576p (768x576)",
	"1024x576": "576p wide (1024x576)",
	"1280x720": "720p (1280x720)",
	"1440x1080": "1080p (1440x1080)",
	"1920x1080": "1080p (1920x1080)",
}

BITRATE_CHOICES_BCM_LIMITED = (
	-1, 50000, 100000, 150000, 200000, 250000, 300000, 350000, 400000,
	450000, 500000, 600000, 700000, 800000, 900000, 1000000,
)
BITRATE_CHOICES_BCM = (
	-1, 100000, 150000, 200000, 250000, 300000, 350000, 400000,
	450000, 500000, 750000, 1000000, 1500000, 2000000, 2500000,
	3000000, 3500000, 4000000, 4500000, 5000000, 10000000,
)
BITRATE_CHOICES_DREAM = (800000, 1000000, 1500000, 2000000, 2500000, 3000000, 4000000, 5000000)
BITRATE_CHOICES_NATIVE = (
	100000, 300000, 500000, 800000, 1000000, 1200000, 1500000, 2000000,
	2500000, 3000000, 3500000, 4000000, 5000000,
)
FRAMERATE_CHOICES_BCM = ("-1", "23976", "24000", "25000", "29970", "30000", "50000", "59940", "60000")
FRAMERATE_CHOICES_NATIVE = ("23976", "24000", "25000", "30000")
DREAM_FRAMERATE_CHOICES = ("25000", "30000", "50000", "60000")

PRESETS = {
	"verylow": {"bitrate": 800000, "audioBitrate": 64, "resolution": "720x576", "framerate": "25000", "videocodec": "h264"},
	"low": {"bitrate": 1200000, "audioBitrate": 96, "resolution": "720x576", "framerate": "25000", "videocodec": "h264"},
	"medium": {"bitrate": 2000000, "audioBitrate": 96, "resolution": "1280x720", "framerate": "25000", "videocodec": "h264"},
	"high": {"bitrate": 2500000, "audioBitrate": 128, "resolution": "1280x720", "framerate": "25000", "videocodec": "h264"},
	"higher": {"bitrate": 4000000, "audioBitrate": 192, "resolution": "1920x1080", "framerate": "25000", "videocodec": "h264"},
	"best": {"bitrate": 6000000, "audioBitrate": 256, "resolution": "1920x1080", "framerate": "25000", "videocodec": "h264"},
	"maximum": {"bitrate": 8000000, "audioBitrate": 256, "resolution": "1920x1080", "framerate": "25000", "videocodec": "h264"},
}
PRESET_CHOICES = [
	("verylow", _("Very Low")),
	("low", _("Low")),
	("medium", _("Medium")),
	("high", _("High")),
	("higher", _("Higher")),
	("best", _("Best")),
	("maximum", _("Maximum")),
	("custom", _("Custom")),
]


def _stream_server_constants():
	try:
		from enigma import eStreamServer
		return {
			"gop_default": eStreamServer.GOP_LENGTH_DEFAULT,
			"gop_min": eStreamServer.GOP_LENGTH_MIN,
			"gop_max": eStreamServer.GOP_LENGTH_MAX,
			"b_default": eStreamServer.BFRAMES_DEFAULT,
			"b_min": eStreamServer.BFRAMES_MIN,
			"b_max": eStreamServer.BFRAMES_MAX,
			"p_default": eStreamServer.PFRAMES_DEFAULT,
			"p_min": eStreamServer.PFRAMES_MIN,
			"p_max": eStreamServer.PFRAMES_MAX,
			"slices_default": eStreamServer.SLICES_DEFAULT,
			"slices_min": eStreamServer.SLICES_MIN,
			"slices_max": eStreamServer.SLICES_MAX,
			"level_default": str(eStreamServer.LEVEL_DEFAULT),
			"levels": [
				(str(eStreamServer.LEVEL1_1), "1.1"), (str(eStreamServer.LEVEL1_2), "1.2"),
				(str(eStreamServer.LEVEL1_3), "1.3"), (str(eStreamServer.LEVEL2_0), "2.0"),
				(str(eStreamServer.LEVEL2_1), "2.1"), (str(eStreamServer.LEVEL2_2), "2.2"),
				(str(eStreamServer.LEVEL3_0), "3.0"), (str(eStreamServer.LEVEL3_1), "3.1"),
				(str(eStreamServer.LEVEL3_2), "3.2"), (str(eStreamServer.LEVEL4_0), "4.0"),
				(str(eStreamServer.LEVEL4_1), "4.1"), (str(eStreamServer.LEVEL4_2), "4.2"),
			],
			"profile_default": str(eStreamServer.PROFILE_DEFAULT),
			"profiles": [(str(eStreamServer.PROFILE_MAIN), _("Main")), (str(eStreamServer.PROFILE_HIGH), _("High"))],
		}
	except Exception:
		return {
			"gop_default": 0, "gop_min": 0, "gop_max": 15000,
			"b_default": 0, "b_min": 0, "b_max": 2,
			"p_default": 4, "p_min": 0, "p_max": 14,
			"slices_default": 0, "slices_min": 0, "slices_max": 16,
			"level_default": "7",
			"levels": [(str(index), label) for index, label in enumerate(("1.1", "1.2", "1.3", "2.0", "2.1", "2.2", "3.0", "3.1", "3.2", "4.0", "4.1", "4.2"))],
			"profile_default": "0", "profiles": [("0", _("Main")), ("1", _("High"))],
		}


SERVER_CONSTANTS = _stream_server_constants()


def _input_mode_values():
	try:
		from enigma import eStreamServer
		return str(eStreamServer.INPUT_MODE_LIVE), str(eStreamServer.INPUT_MODE_HDMI_IN), str(eStreamServer.INPUT_MODE_BACKGROUND)
	except Exception:
		return "0", "1", "2"


INPUT_MODE_LIVE, INPUT_MODE_HDMI_IN, INPUT_MODE_BACKGROUND = _input_mode_values()


def live_source_choices():
	choices = [(INPUT_MODE_LIVE, _("Follow Live"))]
	if CAPABILITIES.has_hdmi_input:
		choices.append((INPUT_MODE_HDMI_IN, _("HDMI Input")))
	return choices


def encoder_selection_choices():
	"""Return Auto followed by every detected physical encoder."""
	return [(ENCODER_AUTO, _("Auto (first free)"))] + [
		(str(index), _("Encoder %d") % index) for index in CAPABILITIES.encoder_indices()
	]


def encoder_selection_value(value=None):
	"""Normalize a selector to ``auto`` or a valid encoder index string."""
	if value is None:
		value = config.plugins.transcodingsettings.encoder.value
	value = str(ENCODER_AUTO if value is None else value).strip().lower()
	if value in (ENCODER_AUTO, "-1"):
		return ENCODER_AUTO
	try:
		index = int(value)
	except (TypeError, ValueError):
		return ENCODER_AUTO
	return str(index) if index in CAPABILITY_BY_INDEX else ENCODER_AUTO


def encoder_preference_index(value=None):
	"""Return -1 for automatic first-free allocation or a physical index."""
	value = encoder_selection_value(value)
	return -1 if value == ENCODER_AUTO else int(value)


def encoder_profile_index(value=None):
	"""Return the profile used to build URL values for a selector.

	Automatic allocation cannot know the free physical encoder before Enigma2
	accepts the request. It therefore uses the first detected encoder profile
	while leaving physical allocation automatic.
	"""
	preferred = encoder_preference_index(value)
	if preferred in CAPABILITY_BY_INDEX:
		return preferred
	indices = CAPABILITIES.encoder_indices()
	return indices[0] if indices else 0


def encoder_capabilities_for_selection(value=None):
	"""Return all possible encoders for Auto, otherwise the selected encoder."""
	preferred = encoder_preference_index(value)
	if preferred >= 0:
		capability = CAPABILITY_BY_INDEX.get(preferred)
		return [capability] if capability else []
	return list(CAPABILITIES.encoders)



def _selection(default, choices):
	choices = [
		(str(choice[0]), choice[1]) if isinstance(choice, tuple) else str(choice)
		for choice in choices
	]
	values = [choice[0] if isinstance(choice, tuple) else choice for choice in choices]
	default = str(default)
	if default not in values and values:
		default = values[0]
	return ConfigSelection(default=default, choices=choices)


def _bitrate_label(value):
	value = int(value)
	if value < 0:
		return _("Automatic")
	if value >= 1000000:
		return "%g Mbit/s" % (value / 1000000.0)
	return "%d kbit/s" % (value // 1000)


def _framerate_label(value):
	try:
		value = int(value)
		if value < 0:
			return _("Automatic")
		return "%g fps" % (value / 1000.0)
	except (TypeError, ValueError):
		return str(value)


def _codec_label(value):
	labels = {
		"h264": "H.264 / AVC", "h265": "H.265 / HEVC", "hevc": "H.265 / HEVC",
		"mpeg2": "MPEG-2", "mpeg4p2": "MPEG-4 Part 2", "aac": "AAC", "mpg": "MPEG audio",
		"mp3": "MP3", "ac3": "AC-3", "aac+": "HE-AAC", "aac+loas": "HE-AAC LOAS", "aac+adts": "HE-AAC ADTS",
	}
	return labels.get(str(value).lower(), str(value))


def _unique(values):
	result = []
	for value in values:
		value = str(value)
		if value and value not in result:
			result.append(value)
	return result


def _nearest_numeric(target, values):
	values = list(values)
	if not values:
		return str(target)
	try:
		return str(min(values, key=lambda value: abs(int(value) - int(target))))
	except (TypeError, ValueError):
		return str(values[0])


def _nearest_resolution(target, values):
	values = list(values)
	if not values:
		return str(target)
	target_dimensions = RESOLUTION_DIMENSIONS.get(str(target), (1280, 720))
	target_pixels = target_dimensions[0] * target_dimensions[1]
	return min(values, key=lambda value: abs((RESOLUTION_DIMENSIONS.get(str(value), target_dimensions)[0] * RESOLUTION_DIMENSIONS.get(str(value), target_dimensions)[1]) - target_pixels))


def _bitrate_values(capability):
	values = capability.values("bitrate")
	if values:
		return _unique(values)
	if capability.is_limited_bcm:
		values = BITRATE_CHOICES_BCM_LIMITED
	elif capability.is_bcm:
		values = BITRATE_CHOICES_BCM
	elif capability.is_dream:
		values = BITRATE_CHOICES_DREAM
	else:
		values = BITRATE_CHOICES_NATIVE
	return [str(value) for value in values]


def _framerate_values(capability):
	values = capability.values("framerate")
	if values:
		values = _unique(values)
		# Older BCM drivers expose automatic mode as a valid runtime value but
		# omit it from framerate_choices.
		if capability.is_bcm and "-1" not in values:
			values.insert(0, "-1")
		return values
	if capability.is_dream:
		return list(DREAM_FRAMERATE_CHOICES)
	if capability.is_bcm:
		return list(FRAMERATE_CHOICES_BCM)
	return list(FRAMERATE_CHOICES_NATIVE)


def _resolution_values(capability):
	mapping = {}
	values = []
	for raw in capability.values("resolution"):
		canonical = DRIVER_RESOLUTION_KEYS.get(str(raw).lower(), str(raw) if "x" in str(raw) else "")
		if canonical in RESOLUTION_DIMENSIONS and canonical not in values:
			values.append(canonical)
			mapping[canonical] = str(raw)
	# BCM drivers with width/height controls traditionally support these two
	# custom formats even when display_format_choices lists only broadcast sizes.
	if values and capability.has("width") and capability.has("height"):
		for custom in ("320x240", "160x120"):
			if custom not in values:
				values.append(custom)
				mapping[custom] = "custom" if capability.has("resolution") else custom
	if not values:
		if capability.is_dream:
			values = ["720x576", "1280x720", "1920x1080"]
		elif capability.is_limited_bcm:
			values = ["854x480", "768x576", "1280x720", "320x240", "160x120"]
		elif capability.is_bcm:
			values = ["720x480", "720x576", "1280x720", "1920x1080"]
		else:
			values = ["320x240", "640x360", "720x480", "720x576", "768x576", "1024x576", "1280x720", "1440x1080", "1920x1080"]
		for value in values:
			mapping[value] = value
	RESOLUTION_DRIVER_VALUES[capability.index] = mapping
	return values


def _video_codec_values(capability):
	values = _unique(capability.values("videocodec"))
	if not values:
		if capability.is_dream:
			values = ["h264"]
		elif capability.has("videocodec") and not capability.is_bcm:
			values = ["h264", "h265"]
		else:
			values = ["h264"]
	return values


def _audio_codec_values(capability):
	return _unique(capability.values("audiocodec")) or ["aac"]


def _aspect_choices(capability):
	values = capability.values("aspectratio")
	labels = capability.labels("aspectratio")
	if values:
		return [(value, labels.get(value, value)) for value in values]
	# Receivers without an aspectratio_choices node use the plugin's conservative
	# hardware profile. The values are owned by this plugin and are independent
	# from every other transcoding configuration namespace.
	return [("0", _("Automatic")), ("1", "4:3"), ("2", "16:9")]


def _interlace_choices(capability):
	values = capability.values("interlaced")
	labels = capability.labels("interlaced")
	if values:
		return [(value, labels.get(value, value)) for value in values]
	return [("0", _("Progressive")), ("1", _("Interlaced"))]


def _feature_choices(capability, feature, fallback):
	values = _unique(capability.values(feature))
	labels = capability.labels(feature)
	if values:
		return [(value, labels.get(value, value)) for value in values]
	return list(fallback)


def _choice_keys(choices):
	return [str(choice[0] if isinstance(choice, tuple) else choice) for choice in choices]


def _choice_by_label(choices, words, default=None):
	words = tuple(str(word).lower() for word in words)
	for choice in choices:
		value, label = choice if isinstance(choice, tuple) else (choice, choice)
		if any(word in str(label).lower() for word in words):
			return str(value)
	keys = _choice_keys(choices)
	if default is not None and str(default) in keys:
		return str(default)
	return keys[0] if keys else ""


def _default_preset(capability):
	return "verylow" if capability.is_limited_bcm else "medium"


def _create_encoder_config(capability):
	entry = ConfigSubsection()
	bitrate_values = _bitrate_values(capability)
	framerate_values = _framerate_values(capability)
	resolution_values = _resolution_values(capability)
	video_values = _video_codec_values(capability)
	audio_values = _audio_codec_values(capability)
	preset_default = _default_preset(capability)
	preset_values = PRESETS[preset_default]

	# This is a new configuration namespace. Current proc values are deliberately
	# not used as defaults because they may have been written by another plugin
	# before this plugin was installed. Only hardware choice lists are probed.
	bitrate_default = _nearest_numeric(preset_values["bitrate"], bitrate_values)
	framerate_default = _nearest_numeric(preset_values["framerate"], framerate_values)
	resolution_default = _nearest_resolution(preset_values["resolution"], resolution_values)
	video_default = "h264" if "h264" in video_values else video_values[0]
	audio_default = "aac" if "aac" in audio_values else audio_values[0]
	aspect_choices = _aspect_choices(capability)
	interlace_choices = _interlace_choices(capability)
	level_choices = _feature_choices(capability, "level", [
		("1.0", "1.0"), ("2.0", "2.0"), ("2.1", "2.1"), ("2.2", "2.2"),
		("3.0", "3.0"), ("3.1", "3.1"), ("3.2", "3.2"), ("4.0", "4.0"),
		("4.1", "4.1"), ("4.2", "4.2"), ("5.0", "5.0"),
	])
	profile_choices = _feature_choices(capability, "profile", [
		("baseline", _("Baseline")), ("main", _("Main")), ("high", _("High")),
	])

	entry.preset = _selection(preset_default, PRESET_CHOICES)
	entry.bitrate = _selection(bitrate_default, [(value, _bitrate_label(value)) for value in bitrate_values])
	entry.framerate = _selection(framerate_default, [(value, _framerate_label(value)) for value in framerate_values])
	entry.resolution = _selection(resolution_default, [(value, RESOLUTION_LABELS.get(value, value)) for value in resolution_values])
	entry.aspectratio = _selection(_choice_by_label(aspect_choices, ("auto", "automatic"), "0"), aspect_choices)
	entry.interlaced = _selection(_choice_by_label(interlace_choices, ("progressive", "no"), "0"), interlace_choices)
	entry.videocodec = _selection(video_default, [(value, _codec_label(value)) for value in video_values])
	entry.audiocodec = _selection(audio_default, [(value, _codec_label(value)) for value in audio_values])
	entry.automode = _selection("Off", [("Off", _("Off")), ("On", _("On"))])
	entry.gopframeb = ConfigInteger(default=0, limits=(0, 60))
	entry.gopframep = ConfigInteger(default=29, limits=(0, 60))
	entry.level = _selection("3.1", level_choices)
	entry.profile = _selection("main", profile_choices)
	return entry


def _apply_preset(index, preset_name):
	if preset_name == "custom" or index in _PRESET_APPLYING:
		return
	entry = get_encoder_config(index)
	try:
		preset = PRESETS[preset_name]
	except KeyError:
		return
	if entry is None:
		return
	_PRESET_APPLYING.add(index)
	try:
		entry.bitrate.value = _nearest_numeric(preset["bitrate"], entry.bitrate.choices)
		entry.framerate.value = _nearest_numeric(preset["framerate"], entry.framerate.choices)
		entry.resolution.value = _nearest_resolution(preset["resolution"], entry.resolution.choices)
		if preset["videocodec"] in entry.videocodec.choices:
			entry.videocodec.value = preset["videocodec"]
		entry.interlaced.value = "0"
		capability = CAPABILITY_BY_INDEX.get(index)
		if capability and capability.is_dream:
			config.plugins.transcodingsettings.live.audioBitrate.value = preset["audioBitrate"]
	finally:
		_PRESET_APPLYING.discard(index)


def _preset_changed(element, index):
	_apply_preset(index, str(element.value))


def _manual_value_changed(unused_element, index):
	if index in _PRESET_APPLYING:
		return
	entry = get_encoder_config(index)
	if entry is not None and entry.preset.value != "custom":
		entry.preset.value = "custom"


def _attach_encoder_notifiers(index, entry):
	entry.preset.addNotifier(lambda element, idx=index: _preset_changed(element, idx), initial_call=False)
	for name in ("bitrate", "framerate", "resolution", "aspectratio", "interlaced", "videocodec", "audiocodec", "automode", "gopframeb", "gopframep", "level", "profile"):
		getattr(entry, name).addNotifier(lambda element, idx=index: _manual_value_changed(element, idx), initial_call=False)


def stream_video_codec_choices(selection=None):
	if selection is None:
		selection = config.plugins.transcodingsettings.encoder.value
	capabilities = encoder_capabilities_for_selection(selection)
	values = []
	for codec in ("h264", "h265"):
		# Auto can allocate any free encoder, so only advertise codecs supported
		# by every possible target. This prevents a second stream from failing.
		if capabilities and all(capability.supports_stream_codec(codec) for capability in capabilities):
			values.append(codec)
	return [(value, _codec_label(value)) for value in values or ["h264"]]


def update_stream_video_codec_choices(unused_element=None):
	choices = stream_video_codec_choices()
	config.plugins.transcodingsettings.live.videoCodec.setChoices(choices, default=choices[0][0])


def get_encoder_config(index=None):
	if index is None:
		index = config.plugins.transcodingsettings.encoder.value
	index = encoder_profile_index(index)
	if index == 0 and hasattr(config.plugins.transcodingsettings, "encoder0"):
		return config.plugins.transcodingsettings.encoder0
	if index == 1 and hasattr(config.plugins.transcodingsettings, "encoder1"):
		return config.plugins.transcodingsettings.encoder1
	return None


def preset_choice_list(index):
	"""Return device-adapted preset labels for the yellow-button selector."""
	entry = get_encoder_config(index)
	if entry is None:
		return []
	labels = dict(PRESET_CHOICES)
	result = []
	for name, values in PRESETS.items():
		bitrate = _nearest_numeric(values["bitrate"], entry.bitrate.choices)
		resolution = _nearest_resolution(values["resolution"], entry.resolution.choices)
		framerate = _nearest_numeric(values["framerate"], entry.framerate.choices)
		description = "%s - %s, %s, %s" % (
			labels.get(name, name),
			_bitrate_label(bitrate),
			RESOLUTION_LABELS.get(str(resolution), str(resolution)),
			_framerate_label(framerate),
		)
		capability = CAPABILITY_BY_INDEX.get(int(index))
		if capability and capability.is_dream:
			description += ", AAC %d kbit/s" % values["audioBitrate"]
		result.append((description, name))
	return result


def get_encoder_capability(index=None):
	if index is None:
		index = config.plugins.transcodingsettings.encoder.value
	return CAPABILITY_BY_INDEX.get(encoder_profile_index(index))


def resolution_dimensions(value):
	return RESOLUTION_DIMENSIONS.get(str(value), (1280, 720))


def live_resolution_dimensions(index, value):
	"""Return dimensions accepted by the active live555 source backend.

	The generic BCM port-8001 implementation accepts only its broadcast
	display formats even when the classic port-8002 driver exposes custom or
	1080p modes. Native HiSilicon/WTE encoders use their width/height controls.
	Dreamsource has three exact caps and the daemon normalizes to these modes.
	"""
	width, height = resolution_dimensions(value)
	capability = CAPABILITY_BY_INDEX.get(int(index))
	if capability is None:
		return width, height
	if capability.is_bcm:
		if height > 576:
			return 1280, 720
		if height > 480:
			return 720, 576
		return 720, 480
	if capability.is_dream:
		modes = ((720, 576), (1280, 720), (1920, 1080))
		return min(modes, key=lambda mode: abs((mode[0] * mode[1]) - (width * height)))
	return width, height


def driver_resolution_value(index, value):
	return RESOLUTION_DRIVER_VALUES.get(int(index), {}).get(str(value), str(value))


# The plugin owns a new, isolated configuration namespace.  It deliberately
# does not import, alias or migrate any value from the legacy transcoding
# plugins.
config.plugins.transcodingsettings = ConfigSubsection()
config.plugins.transcodingsettings.enabled = ConfigYesNo(default=True)
config.plugins.transcodingsettings.port = _selection(
	"8001",
	CAPABILITIES.port_choices() or [("8001", "8001 - Enigma2 stream server")],
)
config.plugins.transcodingsettings.encoder = _selection(ENCODER_AUTO, encoder_selection_choices())

if 0 in CAPABILITY_BY_INDEX:
	config.plugins.transcodingsettings.encoder0 = _create_encoder_config(CAPABILITY_BY_INDEX[0])
if 1 in CAPABILITY_BY_INDEX:
	config.plugins.transcodingsettings.encoder1 = _create_encoder_config(CAPABILITY_BY_INDEX[1])

config.plugins.transcodingsettings.live = ConfigSubsection()
config.plugins.transcodingsettings.live.source = _selection(INPUT_MODE_LIVE, live_source_choices())
config.plugins.transcodingsettings.live.videoCodec = _selection("h264", stream_video_codec_choices(ENCODER_AUTO))
config.plugins.transcodingsettings.live.audioCodec = _selection("aac", [("aac", "AAC")])
config.plugins.transcodingsettings.live.audioBitrate = ConfigInteger(default=96, limits=(32, 448))
config.plugins.transcodingsettings.live.gopLength = ConfigInteger(
	default=SERVER_CONSTANTS["gop_default"],
	limits=(SERVER_CONSTANTS["gop_min"], SERVER_CONSTANTS["gop_max"]),
)
config.plugins.transcodingsettings.live.gopOnSceneChange = ConfigYesNo(default=False)
config.plugins.transcodingsettings.live.openGop = ConfigYesNo(default=False)
config.plugins.transcodingsettings.live.bFrames = ConfigInteger(
	default=SERVER_CONSTANTS["b_default"],
	limits=(SERVER_CONSTANTS["b_min"], SERVER_CONSTANTS["b_max"]),
)
config.plugins.transcodingsettings.live.pFrames = ConfigInteger(
	default=SERVER_CONSTANTS["p_default"],
	limits=(SERVER_CONSTANTS["p_min"], SERVER_CONSTANTS["p_max"]),
)
config.plugins.transcodingsettings.live.slices = ConfigInteger(
	default=SERVER_CONSTANTS["slices_default"],
	limits=(SERVER_CONSTANTS["slices_min"], SERVER_CONSTANTS["slices_max"]),
)
config.plugins.transcodingsettings.live.level = _selection(SERVER_CONSTANTS["level_default"], SERVER_CONSTANTS["levels"])
config.plugins.transcodingsettings.live.profile = _selection(SERVER_CONSTANTS["profile_default"], SERVER_CONSTANTS["profiles"])

config.plugins.transcodingsettings.hls = ConfigSubsection()
config.plugins.transcodingsettings.hls.enabled = ConfigYesNo(default=False)
config.plugins.transcodingsettings.hls.port = ConfigInteger(default=8090, limits=(1, 65535))
config.plugins.transcodingsettings.hls.path = ConfigText(default="stream", fixed_size=False)
config.plugins.transcodingsettings.hls.user = ConfigText(default="", fixed_size=False)
config.plugins.transcodingsettings.hls.password = ConfigPassword(default="", fixed_size=False)

config.plugins.transcodingsettings.rtsp = ConfigSubsection()
config.plugins.transcodingsettings.rtsp.enabled = ConfigYesNo(default=False)
config.plugins.transcodingsettings.rtsp.port = ConfigInteger(default=5554, limits=(1, 65535))
config.plugins.transcodingsettings.rtsp.path = ConfigText(default="stream", fixed_size=False)
config.plugins.transcodingsettings.rtsp.user = ConfigText(default="", fixed_size=False)
config.plugins.transcodingsettings.rtsp.password = ConfigPassword(default="", fixed_size=False)

if 0 in CAPABILITY_BY_INDEX:
	_attach_encoder_notifiers(0, config.plugins.transcodingsettings.encoder0)
if 1 in CAPABILITY_BY_INDEX:
	_attach_encoder_notifiers(1, config.plugins.transcodingsettings.encoder1)

config.plugins.transcodingsettings.encoder.addNotifier(update_stream_video_codec_choices, initial_call=False)
