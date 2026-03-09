"""Base banner renderer — shared image lifecycle utilities."""

from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw

from .components import create_f1_header, paste_with_alpha
from .design_system import BANNER_SIZES, F1Colors


class BannerRenderer:
    """Thin helper that wraps common Pillow operations for banner images."""

    # ------------------------------------------------------------------ #
    #  Image creation                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def create_base(
        banner_type: str,
        bg_color: str = F1Colors.BG_DARK,
    ) -> Image.Image:
        """Create a new RGBA image at the size defined for *banner_type*.

        Falls back to 1200x630 if *banner_type* is not in
        :data:`BANNER_SIZES`.
        """
        w, h = BANNER_SIZES.get(banner_type, (1200, 630))
        return Image.new("RGBA", (w, h), bg_color)

    # ------------------------------------------------------------------ #
    #  Header                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def add_header(
        img: Image.Image,
        title: str,
        subtitle: str | None = None,
    ) -> int:
        """Paste the standard F1 header at the top of *img*.

        Returns the y‑coordinate of the bottom edge of the header so
        callers know where to start drawing content.
        """
        header = create_f1_header(img.width, title, subtitle)
        paste_with_alpha(img, header, (0, 0))
        return header.height

    # ------------------------------------------------------------------ #
    #  Compositing                                                        #
    # ------------------------------------------------------------------ #

    @staticmethod
    def composite(
        base: Image.Image,
        overlay: Image.Image,
        position: tuple[int, int],
        mask: Image.Image | None = None,
    ) -> None:
        """Paste *overlay* onto *base* with optional *mask*.

        If no *mask* is given, the overlay's own alpha channel is used.
        """
        if mask is not None:
            base.paste(overlay, position, mask)
        else:
            paste_with_alpha(base, overlay, position)

    # ------------------------------------------------------------------ #
    #  Serialisation                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def to_bytes(img: Image.Image, fmt: str = "PNG") -> BytesIO:
        """Render the image to an in‑memory :class:`BytesIO` buffer.

        The buffer's position is reset to 0 so it can be sent directly
        as a file upload.
        """
        buf = BytesIO()
        # PNG requires RGBA; JPEG needs RGB
        if fmt.upper() == "JPEG" and img.mode == "RGBA":
            img = img.convert("RGB")
        img.save(buf, format=fmt)
        buf.seek(0)
        return buf

    # ------------------------------------------------------------------ #
    #  Image loading                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def load_image_from_bytes(data: bytes) -> Image.Image:
        """Decode raw bytes (PNG / JPEG / …) into an RGBA PIL Image."""
        img = Image.open(BytesIO(data))
        return img.convert("RGBA")
