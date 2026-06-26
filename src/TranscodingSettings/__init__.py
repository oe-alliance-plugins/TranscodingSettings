# -*- coding: utf-8 -*-
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext

PluginLanguageDomain = "TranscodingSettings"
PluginLanguagePath = "SystemPlugins/TranscodingSettings/locale"


def localeInit():
	gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
	translated = gettext.dgettext(PluginLanguageDomain, txt)
	if translated != txt:
		return translated
	return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)

__version__ = "1.0"
