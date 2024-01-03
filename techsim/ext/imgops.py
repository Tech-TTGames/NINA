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

from PIL import Image, ImageSequence, ImageOps

SIZE = (512, 512)


def thumbpaste(im: Image.Image, size: tuple[int, int] = SIZE) -> Image.Image:
    """Resizes an image to the size and pastes it onto a transparent image.

    Args:
        im: The image to resize.
        size: The size to resize the image to.
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
    return new_image


def resize(im: Image.Image, size: tuple[int, int] = SIZE) -> tuple[list[Image.Image], dict] | Image.Image:
    """Resizes an image to the correct size for the simulation.

    This function resizes an image to the correct size for the simulation.
    This is done by resizing the image to the given size, and then pasting
    the resized image onto a blank image of the correct size.

    Args:
        im: The image to resize.
        size: The size to resize the image to.

    Returns:
        The resized image.
    """
    if getattr(im, 'n_frames', 1) == 1:
        # Not an animated image
        return thumbpaste(im, size)
    # Now do the same but for each frame in the animated image
    frames = []
    for frame in ImageSequence.Iterator(im):
        frame = frame.convert("RGBA")
        frames.append(thumbpaste(frame, size))
    return frames, im.info
