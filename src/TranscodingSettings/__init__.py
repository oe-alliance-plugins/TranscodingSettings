# PYTHON IMPORTS
from gettext import bindtextdomain, dgettext, gettext
from os.path import join

# ENIGMA IMPORTS
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "TranscodingSettings"
PLUGINPATH = resolveFilename(SCOPE_PLUGINS, f"SystemPlugins/{PluginLanguageDomain}/")


def localeInit():
    bindtextdomain(PluginLanguageDomain, join(PLUGINPATH, "locale"))


def _(txt):
    t = dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext(txt)
    return t


localeInit()
language.addCallback(localeInit)

__version__ = "1.0"
