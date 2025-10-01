"""Pillow advanced image resizing.

This module contains the advanced image resizing functions for Pillow.
This is to resize user-provided images to the correct size for the simulation.

Typical usage example:
    image = Image.open("image.png")
    image = resize(image, (200, 200))
    image.save("image.png")
"""
# License: EPL-2.0
# SPDX-License-Identifier: EPL-2.0
# Copyright (c) 2023-present Tech. TTGames
import itertools

from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps
from PIL import ImageSequence

SIZE = (512, 512)


def thumbpaste(
    im: Image.Image,
    size: tuple[int, int] = SIZE,
    border_c: str | None = None,
) -> Image.Image:
    """Resizes an image to the size and pastes it onto a transparent image.

    Args:
        im: The image to resize.
        size: The size to resize the image to.
        border_c: An optional string of the color for the border to use for the image
    """
    if im.size[0] > size[0] or im.size[1] > size[1]:
        im.thumbnail(size)
    if im.size[0] < size[0] or im.size[1] < size[1]:
        # Upscale the image to the correct size, while trying to keep the aspect ratio
        im = ImageOps.contain(im, size)
    # Thumbnails are resized to keep an aspect ratio, so paste the thumbnail onto a transparent image
    new_image = Image.new("RGBA", size, (255, 0, 0, 0))
    padding_x = (size[0] - im.size[0]) // 2
    padding_y = (size[1] - im.size[1]) // 2
    new_image.paste(im, (padding_x, padding_y))
    if border_c:
        border(new_image, border_c)
    return new_image


def resize(
    im: Image.Image,
    size: tuple[int, int] = SIZE,
    border_c: str | None = None,
) -> tuple[list[Image.Image], dict] | Image.Image:
    """Resizes an image to the correct size for the simulation.

    This function resizes an image to the correct size for the simulation.
    This is done by resizing the image to the given size, and then pasting
    the resized image onto a blank image of the correct size.

    Args:
        im: The image to resize.
        size: The size to resize the image to.
        border_c: An optional string of the color for the border to use for the image

    Returns:
        The resized image.
    """
    if getattr(im, "n_frames", 1) == 1:
        # Not an animated image
        return thumbpaste(im, size, border_c=border_c)
    # Now do the same but for each frame in the animated image
    frames = []
    for frame in ImageSequence.Iterator(im):
        frame = frame.convert("RGBA")
        frames.append(thumbpaste(frame, size, border_c=border_c))
    return frames, im.info


def average_gif_durations(durations: list[list[int] | int], frames: int) -> list[int]:
    """Calculates the average duration for each frame of the gif in milliseconds.

    Args:
        durations: The durations of the gif in milliseconds, for every gif.
            Either a list of specific durations or a global one.
        frames: Maximum number of frames for the gif.
    """
    for list_d in range(len(durations)):
        if isinstance(durations[list_d], int):
            durations[list_d] = [durations[list_d] for _ in range(frames)]
        elif len(durations[list_d]) < frames:
            dur_cycle = itertools.cycle(iter(durations[list_d].copy()))
            for _ in range(frames - len(durations[list_d])):
                durations[list_d].append(next(dur_cycle))
    return [sum(packaged_dur) // len(packaged_dur) for packaged_dur in zip(*durations)]


def border(im: Image.Image, color: str):
    """Adds a border around the image of 1 px width.

    Args:
        im: The image to add the border to
        color: The color of the border to add
    """
    draw = ImageDraw.Draw(im)
    draw.rectangle((0, 0, im.width - 1, im.height - 1), outline=color, width=5)
