"""Pillow advanced image resizing and various utilities.

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
import pathlib

from PIL import Image
from PIL import ImageDraw
from PIL import ImageOps
from PIL import ImageSequence

SIZE = (512, 512)
WEBP_COMPRESSION = (4, 80)


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
    if im.mode != 'RGBA':
        im = im.convert('RGBA')

    if im.size[0] > size[0] or im.size[1] > size[1]:
        im.thumbnail(size)
    if im.size[0] < size[0] or im.size[1] < size[1]:
        # Upscale the image to the correct size, while trying to keep the aspect ratio
        im = ImageOps.contain(im, size)
    # Thumbnails are resized to keep an aspect ratio, so paste the thumbnail onto a transparent image
    new_image = Image.new("RGBA", size, (255, 0, 0, 0))
    padding_x = (size[0] - im.size[0]) // 2
    padding_y = (size[1] - im.size[1]) // 2
    new_image.paste(im, (padding_x, padding_y), im)
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
        frames.append(thumbpaste(frame, size, border_c=border_c))
    return frames, im.info


def average_animation_duration(durations: list[list[int] | int], frames: int) -> list[int]:
    """Calculates the average duration for each frame of the animation in milliseconds.

    Args:
        durations: The durations of the animation in milliseconds, for every animation.
            Either a list of specific durations or a global one.
        frames: Maximum number of frames for the animation.
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


def magicsave(image: Image.Image | tuple[list[Image.Image], dict],
              path: pathlib.Path,
              durs: list[int] | int | None = None) -> None:
    """Saves the image to the given path with format-specific optimizations.

    Supports PNG, GIF, and both static and animated lossless WebP.

    Args:
        image: The image or animated image tuple to save.
        path: The path to save the image to. Its extension determines the format.
        durs: The duration(s) for animation frames in milliseconds.
    """
    if path.suffix.lower() == ".webp":
        if isinstance(image, tuple):
            frames, info = image
            background = info.get("background", (0, 0, 0, 0))
            if not isinstance(background, tuple):
                background = (0, 0, 0, 0)
            loop = info.get("loop", 0)
            frames[0].save(
                path,
                "WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=durs or info.get("duration", 100),
                loop=loop,
                background=background,
                lossless=True,
                method=WEBP_COMPRESSION[0],
                quality=WEBP_COMPRESSION[1],
            )
        else:
            image.save(path, "WEBP", lossless=True, method=WEBP_COMPRESSION[0], quality=WEBP_COMPRESSION[1])
    else:
        if isinstance(image, tuple):
            frames, info = image
            frames[0].save(path,
                           save_all=True,
                           append_images=frames[1:],
                           **info,
                           loop=0,
                           duration=durs or info.get("duration", 100),
                           optimize=True,
                           disposal=2)
        else:
            image.save(path, optimize=True)


def save_composite_image(path: pathlib.Path, base_image: Image.Image,
                         animated_elements: list[tuple[Image.Image, tuple[int, int]]]) -> None:
    """
    Saves a composite image. If animated elements are present, it creates
    an optimized animation; otherwise, it saves the static base image.

    Args:
        path: The file path to save the image to.
        base_image: The static background image, potentially with other
                    non-animated elements already pasted onto it.
        animated_elements: A list of tuples, where each tuple contains:
                           (Image.Image object of the Animation, (x, y location to paste)).
    """
    if not animated_elements:
        magicsave(base_image, path)
        return

    # --- Animation Compositing Logic ---
    max_frames = max(getattr(ani, "n_frames", 1) for ani, _ in animated_elements)

    ani_frame_iterators = [itertools.cycle(ImageSequence.Iterator(ani)) for ani, _ in animated_elements]

    final_frames = []
    for _ in range(max_frames):
        frame = base_image.copy()

        for i, (_, location) in enumerate(animated_elements):
            ani_frame = next(ani_frame_iterators[i])
            if ani_frame.mode != "RGBA":
                ani_frame = ani_frame.convert("RGBA")
            frame.paste(ani_frame, location, ani_frame)

        final_frames.append(frame)

    info = animated_elements[0][0].info
    durations = [ani.info.get("duration", 50) for ani, _ in animated_elements]
    info["duration"] = average_animation_duration(durations, max_frames)

    magicsave((final_frames, info), path)
