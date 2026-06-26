from setuptools import setup
import setup_translate

pkg = 'SystemPlugins.TranscodingSettings'
setup(name='enigma2-plugin-systemplugins-transcodingsettings',
       version='1.0',
       description='systemplugins-transcodingsettings',
       package_dir={pkg: 'TranscodingSettings'},
       packages=[pkg],
       package_data={pkg: ['*.png', '*.xml', 'locale/*/LC_MESSAGES/*.mo']},
       cmdclass=setup_translate.cmdclass,  # for translation
      )
