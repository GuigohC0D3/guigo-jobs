from rich.style import Style
from rich.theme import Theme

GUIGO_THEME = Theme({
    "primary": Style(color="#00D4FF", bold=True),
    "secondary": Style(color="#7C3AED"),
    "accent": Style(color="#F59E0B", bold=True),
    "success": Style(color="#10B981", bold=True),
    "danger": Style(color="#EF4444", bold=True),
    "muted": Style(color="#6B7280"),
    "title": Style(color="#00D4FF", bold=True),
    "company": Style(color="#A78BFA"),
    "salary": Style(color="#34D399", bold=True),
    "tag": Style(color="#FCD34D"),
    "source": Style(color="#60A5FA"),
    "border": Style(color="#374151"),
    "highlight": Style(color="#FFFFFF", bold=True),
    "panel.border": Style(color="#1F2937"),
})

LOGO = r"""
[primary]
   ██████╗ ██╗   ██╗██╗ ██████╗  ██████╗
  ██╔════╝ ██║   ██║██║██╔════╝ ██╔═══██╗
  ██║  ███╗██║   ██║██║██║  ███╗██║   ██║
  ██║   ██║██║   ██║██║██║   ██║██║   ██║
  ╚██████╔╝╚██████╔╝██║╚██████╔╝╚██████╔╝
   ╚═════╝  ╚═════╝ ╚═╝ ╚═════╝  ╚═════╝[/primary]
[muted]  Remote Job Hunter — Junior Edition[/muted]
"""

LOGO_COMPACT = "[primary]⬡ GUIGO[/primary] [muted]Remote Jobs[/muted]"
