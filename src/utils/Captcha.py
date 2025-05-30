# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
from abc import ABC, abstractmethod
from typing import override, Generic, TypeVar

import base64
import colorsys
import re
from io import BytesIO
from PIL import Image, ImageOps

_T_IN = TypeVar("_T_IN")
_T_OUT = TypeVar("_T_OUT")


class ImageUtils:
    @staticmethod
    def convert_to_saturation_map(img: Image.Image):
        img_rgb: Image.Image = img.convert("RGB")
        width, height = img_rgb.size

        saturation_map = Image.new("L", (width, height))
        pixels = saturation_map.load()
        assert pixels is not None
        for y in range(height):
            for x in range(width):
                r, g, b = img_rgb.getpixel((x, y))
                _, s, _ = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
                pixels[x, y] = int(s * 255.0)
        return saturation_map

    @staticmethod
    def apply_auto_contrast(img: Image.Image, cutoff: int = 0) -> Image.Image:
        return ImageOps.autocontrast(img, cutoff=cutoff)


class ImageCaptcha(ABC, Generic[_T_IN, _T_OUT]):
    @abstractmethod
    def __init__(self, data: _T_IN):
        raise NotImplementedError()

    @abstractmethod
    def show_image(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def solve_challenge(self) -> _T_OUT:
        raise NotImplementedError()


class QiangGuoXianFengCaptcha(ImageCaptcha[str, str]):
    def __init__(self, data):
        if search := re.match(r"data:image/(?P<ext>.*?);base64,(?P<data>.*)", data, re.DOTALL):
            decoded = base64.b64decode(search.groupdict()["data"])
            self.img: Image.Image = Image.open(BytesIO(decoded))
        else:
            raise ValueError("Unrecognized image data")

    @override
    def show_image(self):
        img = self.img
        img = ImageUtils.convert_to_saturation_map(img)
        img = ImageUtils.apply_auto_contrast(img, cutoff=5)
        img = img.resize((img.width * 2, img.height * 2), resample=Image.Resampling.BILINEAR)
        img.show()

    @override
    def solve_challenge(self):
        return input()
