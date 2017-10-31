import os
import sys
import ConfigParser


class OptionCfg(object):
    OPT_ADAS = 'adas'
    OPT_BORDER_MERGE = 'border_merge'
    OPT_CLIP = 'clip'
    OPT_SPEED_PATTERN = 'speed_pattern'

    OPTS = [OPT_ADAS, OPT_BORDER_MERGE, OPT_CLIP, OPT_SPEED_PATTERN]

    SECTION_DEFAULT = 'DEFAULT'

    def __init__(self, config_dir, version, region):
        self.config_dir = config_dir
        self.version = version
        self.region = region

        self.options = {}
        self.__load_config()

    def is_adas_enabled(self):
        return self.options.get(OptionCfg.OPT_ADAS, False) == True

    def is_border_merge_enabled(self):
        return self.options.get(OptionCfg.OPT_ADAS, False) == True

    def is_clip_enabled(self):
        return self.options.get(OptionCfg.OPT_ADAS, False) == True

    def is_speed_pattern_enabled(self):
        return self.options.get(OptionCfg.OPT_ADAS, False) == True

    def __load_config(self):
        self.__parse_options()

    def __get_config_file(self):
        config_file = os.path.join(self.config_dir, '%s.cfg' % self.version.lower())
        if os.path.exists(config_file):
            return config_file

        # Get default config if not found version specified config
        config_file = os.path.join(self.config_dir, 'default.cfg')
        if os.path.exists(config_file):
            return config_file
        else:
            sys.stderr.write('Error: no config file found for %s in %s\n' % (self.version, self.config_dir))
            return None

    def __parse_options(self):
        config_file = self.__get_config_file()
        if not config_file:
            return False

        cfg = ConfigParser.RawConfigParser()
        cfg.read(config_file)

        default_options = {}
        for opt in OptionCfg.OPTS:
            assert cfg.has_option(OptionCfg.SECTION_DEFAULT, opt)
            default_options[opt] = cfg.getboolean(OptionCfg.SECTION_DEFAULT, opt)

        region = self.region.upper()
        for opt in OptionCfg.OPTS:
            if cfg.has_option(region, opt):
                self.options[opt] = cfg.getboolean(region, opt)
            else:
                self.options[opt] = default_options[opt]

        return True

