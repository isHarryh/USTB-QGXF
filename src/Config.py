# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import json
import os.path as osp


class Config:
    """Configuration class for USTB-QGXF."""

    __instance = None
    __config_path = "USTB-QGXF-Config.json"
    __file_encoding = "UTF-8"
    __default_config = {
        "connection": {"baseUrl": "", "token": ""},
        # WIP
        "memory": {
            "0": {
                "title": "This is an example multiple-selection question record.",
                "type": 2,
                "answers": {
                    "1": {"title": "Example option 1."},
                    "2": {"title": "Example option 2."},
                    "3": {"title": "Example option 3."},
                },
                "rightAnswer": "1|2|3",
            }
        },
        "version": 2,
    }

    def __init__(self):
        """Not recommended to use. Please use the static methods."""
        self._config = {}

    def _get(self, key: str):
        return self._config[key]

    def _set(self, key: str, value):
        self._config[key] = value

    def _read_config(self):
        if osp.isfile(Config.__config_path):
            try:
                loaded_config = json.load(open(Config.__config_path, "r", encoding=Config.__file_encoding))
                if isinstance(loaded_config, dict):
                    for k in Config.__default_config.keys():
                        default_val = Config.__default_config[k]
                        self._config[k] = (
                            loaded_config[k]
                            if isinstance(loaded_config.get(k, None), type(default_val))
                            else default_val
                        )
            except Exception as arg:
                self._config = Config.__default_config
        else:
            self._config = Config.__default_config
            self.save_config()

    def _save_config(self):
        try:
            json.dump(
                self._config,
                open(self.__config_path, "w", encoding=Config.__file_encoding),
                indent=4,
                ensure_ascii=False,
            )
        except Exception as arg:
            pass

    @staticmethod
    def _get_instance():
        if not Config.__instance:
            Config.__instance = Config()
            Config.__instance._read_config()
        return Config.__instance

    @staticmethod
    def get(key):
        """Gets the specified config field.

        :param key: The JSON key to the field;
        :returns: The value of the field, `None` if the key doesn't exist;
        :rtype: Any;
        """
        return Config._get_instance()._get(key)

    @staticmethod
    def set(key, value):
        """Sets the specified config field.

        :param key: The JSON key to the field;
        :param value: The new value;
        :rtype: None;
        """
        return Config._get_instance()._set(key, value)

    @staticmethod
    def read_config():
        """Reads the config from file, aka. deserialize the config.
        The default config will be used if the config file doesn't exist or an error occurs.
        The logging level of `Logger` class will be updated according to the config.
        """
        return Config._get_instance()._read_config()

    @staticmethod
    def save_config():
        """Saves the config to file, aka. serialize the config."""
        return Config._get_instance()._save_config()
