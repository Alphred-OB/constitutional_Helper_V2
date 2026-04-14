"""
Inline SVG icon system — Lucide-style icons for GhanaLex.
Replaces all emoji usage with clean, professional SVG icons.
"""


def svg(name, size=16, color="currentColor"):
    """Return inline SVG icon HTML string."""
    paths = {
        "scale": (
            '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
            '<path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/>'
            '<path d="M7 21h10"/><path d="M12 3v18"/>'
            '<path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>'
        ),
        "user": (
            '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/>'
            '<circle cx="12" cy="7" r="4"/>'
        ),
        "book": (
            '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>'
            '<path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
        ),
        "volume": (
            '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>'
            '<path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
            '<path d="M19.07 4.93a10 10 0 0 1 0 14.14"/>'
        ),
        "thumbs-up": (
            '<path d="M7 10v12"/>'
            '<path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 '
            '17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 '
            '1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/>'
        ),
        "thumbs-down": (
            '<path d="M17 14V2"/>'
            '<path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 '
            '6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-'
            '1.79 1.11L12 22h0a3.13 3.13 0 0 1-3-3.88Z"/>'
        ),
        "sun": (
            '<circle cx="12" cy="12" r="4"/>'
            '<path d="M12 2v2"/><path d="M12 20v2"/>'
            '<path d="m4.93 4.93 1.41 1.41"/>'
            '<path d="m17.66 17.66 1.41 1.41"/>'
            '<path d="M2 12h2"/><path d="M20 12h2"/>'
            '<path d="m6.34 17.66-1.41 1.41"/>'
            '<path d="m19.07 4.93-1.41 1.41"/>'
        ),
        "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
        "globe": (
            '<circle cx="12" cy="12" r="10"/>'
            '<path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/>'
            '<path d="M2 12h20"/>'
        ),
        "settings": (
            '<line x1="4" x2="4" y1="21" y2="14"/>'
            '<line x1="4" x2="4" y1="10" y2="3"/>'
            '<line x1="12" x2="12" y1="21" y2="12"/>'
            '<line x1="12" x2="12" y1="8" y2="3"/>'
            '<line x1="20" x2="20" y1="21" y2="16"/>'
            '<line x1="20" x2="20" y1="12" y2="3"/>'
            '<line x1="2" x2="6" y1="14" y2="14"/>'
            '<line x1="10" x2="14" y1="8" y2="8"/>'
            '<line x1="18" x2="22" y1="16" y2="16"/>'
        ),
        "library": (
            '<path d="m16 6 4 14"/><path d="M12 6v14"/>'
            '<path d="M8 8v12"/><path d="M4 4v16"/>'
        ),
        "trash": (
            '<path d="M3 6h18"/>'
            '<path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>'
            '<path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>'
        ),
        "shield": (
            '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 '
            '20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 '
            '1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'
        ),
        "lock": (
            '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/>'
            '<path d="M7 11V7a5 5 0 0 1 10 0v4"/>'
        ),
        "briefcase": (
            '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>'
            '<rect width="20" height="14" x="2" y="6" rx="2"/>'
        ),
        "landmark": (
            '<line x1="3" x2="21" y1="22" y2="22"/>'
            '<line x1="6" x2="6" y1="18" y2="11"/>'
            '<line x1="10" x2="10" y1="18" y2="11"/>'
            '<line x1="14" x2="14" y1="18" y2="11"/>'
            '<line x1="18" x2="18" y1="18" y2="11"/>'
            '<polygon points="12 2 20 7 4 7"/>'
        ),
        "gavel": (
            '<path d="m14 13-7.5 7.5c-.83.83-2.17.83-3 0 0 0 0 0 0 0a2.12 '
            '2.12 0 0 1 0-3L11 10"/>'
            '<path d="m16 16 6-6"/><path d="m8 8 6-6"/>'
            '<path d="m9 7 8 8"/><path d="m21 11-8-8"/>'
        ),
        "vote": (
            '<path d="m9 12 2 2 4-4"/>'
            '<path d="M5 7c0-1.1.9-2 2-2h10a2 2 0 0 1 2 2v12H5V7Z"/>'
            '<path d="M22 19H2"/>'
        ),
        "file-text": (
            '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>'
            '<path d="M14 2v4a2 2 0 0 0 2 2h4"/>'
            '<path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
        ),
        "graduation": (
            '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 '
            '0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/>'
            '<path d="M22 10v6"/>'
            '<path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>'
        ),
        "users": (
            '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
            '<circle cx="9" cy="7" r="4"/>'
            '<path d="M22 21v-2a4 4 0 0 0-3-3.87"/>'
            '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
        ),
        "crown": (
            '<path d="m2 4 3 12h14l3-12-6 7-4-7-4 7-6-7z"/>'
            '<path d="M5 16h14v3H5z"/>'
        ),
        "map-pin": (
            '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/>'
            '<circle cx="12" cy="10" r="3"/>'
        ),
        "search": (
            '<circle cx="11" cy="11" r="8"/>'
            '<path d="m21 21-4.3-4.3"/>'
        ),
        "mic": (
            '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>'
            '<path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
            '<line x1="12" x2="12" y1="19" y2="22"/>'
        ),
        "square": '<rect width="18" height="18" x="3" y="3" rx="2"/>',
        "clipboard": (
            '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/>'
            '<path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6'
            'a2 2 0 0 1 2-2h2"/>'
        ),
        "lightbulb": (
            '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8'
            'c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
            '<path d="M9 18h6"/><path d="M10 22h4"/>'
        ),
        "message": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
        "check": '<path d="M20 6 9 17l-5-5"/>',
        "info": (
            '<circle cx="12" cy="12" r="10"/>'
            '<path d="M12 16v-4"/><path d="M12 8h.01"/>'
        ),
        "brain": (
            '<path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 '
            '.556 6.588A4 4 0 1 0 12 18Z"/>'
            '<path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-'
            '.556 6.588A4 4 0 1 1 12 18Z"/>'
            '<path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/>'
            '<path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/>'
            '<path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/>'
            '<path d="M3.477 10.896a4 4 0 0 1 .585-.396"/>'
            '<path d="M19.938 10.5a4 4 0 0 1 .585.396"/>'
            '<path d="M6 18a4 4 0 0 1-1.967-.516"/>'
            '<path d="M19.967 17.484A4 4 0 0 1 18 18"/>'
        ),
        "bar-chart": (
            '<line x1="12" x2="12" y1="20" y2="10"/>'
            '<line x1="18" x2="18" y1="20" y2="4"/>'
            '<line x1="6" x2="6" y1="20" y2="14"/>'
        ),
    }
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{paths.get(name, "")}</svg>'
    )
