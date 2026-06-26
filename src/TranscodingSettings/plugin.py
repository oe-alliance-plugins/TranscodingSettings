# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only

from Components.ActionMap import HelpableActionMap
from Components.Sources.StaticText import StaticText
from Components.config import config, configfile, setOnSaveCallback
from Plugins.Plugin import PluginDescriptor
from Screens.ChoiceBox import ChoiceBox
from Screens.MessageBox import MessageBox
from Screens.Setup import Setup

from . import _, PluginLanguageDomain
from .backend import backend
from .configuration import (
	CAPABILITIES,
	CAPABILITY_BY_INDEX,
	encoder_profile_index,
	get_encoder_config,
	preset_choice_list,
	update_stream_video_codec_choices,
)
from .live555 import apply_live_streaming_state, shutdown_live_streaming


PLUGIN_NAME = _("Transcoding Settings")
PLUGIN_DESCRIPTION = _("Configure hardware transcoding, HLS and RTSP")
PLUGIN_PATH = "SystemPlugins/TranscodingSettings"


class TranscodingSettingsSetup(Setup):
	def __init__(self, session):
		config.plugins.transcodingsettings.advanced.value = False
		Setup.__init__(self, session, "transcodingsettings", plugin=PLUGIN_PATH, PluginLanguageDomain=PluginLanguageDomain)
		if "key_yellow" not in self:
			self["key_yellow"] = StaticText()
		if "key_blue" not in self:
			self["key_blue"] = StaticText()
		self["key_yellow"].setText(_("Presets"))
		self["key_blue"].setText(_("Advanced"))
		self["advancedActions"] = HelpableActionMap(self, ["ColorActions"], {
			"yellow": (self.keyYellow, _("Select a ready-to-use preset for the highlighted encoder")),
			"blue": (self.keyBlue, _("Show or hide advanced transcoding settings")),
		}, prio=1, description=_("Transcoding Settings Actions"))

	def supportsFeature(self, index, feature):
		capability = CAPABILITY_BY_INDEX.get(int(index))
		return bool(capability and capability.has(feature))

	def showFeature(self, index, feature):
		"""Return whether a setting has an effect on this encoder backend."""
		capability = CAPABILITY_BY_INDEX.get(int(index))
		if capability is None:
			return False
		# These common URL parameters remain useful on older BCM encoders even
		# when the driver does not publish matching proc nodes or *_choices files.
		if feature in ("bitrate", "framerate", "resolution", "aspectratio", "interlaced"):
			return True
		if capability.is_dream and feature == "videocodec":
			return True
		return capability.has(feature)

	def _validationFootnote(self):
		errors = backend.validate()
		return errors[0] if errors else ""

	def changedEntry(self):
		Setup.changedEntry(self)
		update_stream_video_codec_choices()
		self.setFootnote(self._validationFootnote() or None)

	def selectionChanged(self):
		Setup.selectionChanged(self)
		error = self._validationFootnote()
		if error:
			self.setFootnote(error)

	def _currentEncoderIndex(self):
		current = self["config"].getCurrent()
		current_element = current[1] if current and len(current) > 1 else None
		for index in CAPABILITIES.encoder_indices():
			entry = get_encoder_config(index)
			if entry and current_element in entry.content.items.values():
				return index
		return encoder_profile_index(config.plugins.transcodingsettings.encoder.value)

	def keyYellow(self):
		index = self._currentEncoderIndex()
		choices = preset_choice_list(index)
		if not choices:
			return
		entry = get_encoder_config(index)
		values = [choice[1] for choice in choices]
		selection = values.index(entry.preset.value) if entry.preset.value in values else 0
		self.presetEncoder = index
		self.session.openWithCallback(
			self.presetSelected,
			ChoiceBox,
			text=_("Select a preset for Encoder %d. The values are adapted to this device.") % index,
			choiceList=choices,
			selection=selection,
			buttonList=[],
			windowTitle=_("Encoder Presets"),
		)

	def presetSelected(self, choice):
		if not choice:
			return
		entry = get_encoder_config(getattr(self, "presetEncoder", 0))
		if entry is not None:
			entry.preset.value = choice[1]
			self.createSetup()

	def keyBlue(self):
		advanced = not config.plugins.transcodingsettings.advanced.value
		self["key_blue"].setText(_("Basic") if advanced else _("Advanced"))
		config.plugins.transcodingsettings.advanced.value = advanced
		self.createSetup()

	def keySave(self):
		errors = backend.apply(validate=False)
		if errors:
			self.session.open(MessageBox, "\n".join(errors), MessageBox.TYPE_ERROR, windowTitle=PLUGIN_NAME)
			return
		config.plugins.transcodingsettings.save()
		configfile.save()
		errors = apply_live_streaming_state(self.session)
		if errors:
			self.session.open(MessageBox, "\n".join(errors), MessageBox.TYPE_ERROR, windowTitle=PLUGIN_NAME)
			return
		self.close()

	@classmethod
	def applyConfig(cls):
		errors = backend.apply(validate=False)
		errors += apply_live_streaming_state(None)
		for error in errors:
			print(f"[TranscodingSettings] {error}")


def openSetup(session, **kwargs):
	session.open(TranscodingSettingsSetup)


def sessionStart(reason, session=None, **kwargs):
	if reason == 0:
		errors = backend.apply(validate=False)
		errors.extend(apply_live_streaming_state(session))
		setOnSaveCallback("transcodingsettings", TranscodingSettingsSetup.applyConfig)
	else:
		errors = shutdown_live_streaming()
	for error in errors:
		print(f"[TranscodingSettings] {error}")


def Plugins(**kwargs):
	if not CAPABILITIES.supported:
		return []
	return [
		PluginDescriptor(
			name=PLUGIN_NAME,
			description=PLUGIN_DESCRIPTION,
			where=PluginDescriptor.WHERE_PLUGINMENU,
			icon="plugin.png",
			fnc=openSetup,
		),
		PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionStart),
	]
