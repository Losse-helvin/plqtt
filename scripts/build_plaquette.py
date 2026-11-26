"""Build the corrected HelloLead cash-register brochure.

The layout follows the original "Panneaux solaires" brochure:
  * pages 1, 2, 6, 8 and 9 are left untouched;
  * pages 3, 4, 5 and 7 keep the original grid, while their centre visuals and
    right-hand "Modération & Enrichissement" lead examples are adapted to
    touchscreen cash registers.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Plaquette HelloLead - Panneaux solaires final.pdf"
OUTPUT = ROOT / "Plaquette HelloLead - Caisses enregistreuses tactiles - corrigee.pdf"
ASSETS = ROOT / "assets"
TMP = Path("/tmp/plqtt_center")
TMP.mkdir(exist_ok=True)

S = 3  # PDF point -> pixel ratio for the replacement centre visuals
PANEL = (244, 245, 251)
BLUE = (10, 91, 255)
DARK = (23, 52, 85)
GRAY = (89, 100, 117)
LIGHT_GRAY = (241, 241, 242)
WHITE = (255, 255, 255)
BLUEHEX = 0x0A5BFF

FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
OFFSET = (0, 0)  # set by new_canvas: PDF coordinates of the centre crop origin


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = (FONT_BOLD if bold else FONT_REG, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(key[0], size)
    return _font_cache[key]


def pt(value: float) -> int:
    return round(value * S)


def A(point):
    """Absolute PDF point -> pixel coordinate inside the current canvas."""
    return (pt(point[0] - OFFSET[0]), pt(point[1] - OFFSET[1]))


def AB(box):
    """Absolute PDF rectangle -> pixel rectangle inside the current canvas."""
    return [A((box[0], box[1])), A((box[2], box[3]))]


def rr(draw: ImageDraw.ImageDraw, box, radius=8, fill=WHITE, outline=None, width=1):
    draw.rounded_rectangle(
        [pt(v) for v in box], radius=pt(radius), fill=fill, outline=outline, width=pt(width)
    )


def txt(draw, xy, text, size, fill=DARK, bold=False, max_width=None, anchor=None):
    f = font(pt(size), bold)
    s = size
    while max_width and draw.textlength(text, font=f) > pt(max_width) and s > 6:
        s -= 0.3
        f = font(pt(s), bold)
    draw.text([pt(v) for v in xy], text, font=f, fill=fill, anchor=anchor)
    return s


def wrap(draw, text, size, max_width, bold=False):
    f = font(pt(size), bold)
    result = []
    for segment in text.split("\n"):
        words, current = segment.split(), ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if draw.textlength(candidate, font=f) <= pt(max_width) or not current:
                current = candidate
            else:
                result.append(current)
                current = word
        result.append(current)
    return result


def paragraph(draw, xy, text, size, max_width, fill=GRAY, bold=False, leading=None, max_lines=None):
    lines = wrap(draw, text, size, max_width, bold)
    if max_lines:
        lines = lines[:max_lines]
    leading = leading or size * 1.45
    for i, line in enumerate(lines):
        txt(draw, (xy[0], xy[1] + i * leading), line, size, fill, bold)
    return len(lines) * leading


def photo(image, box, path, focus=(0.5, 0.5)):
    x0, y0, x1, y1 = [pt(v) for v in box]
    src = Image.open(ASSETS / path).convert("RGB")
    target_ratio = (x1 - x0) / (y1 - y0)
    if src.width / src.height > target_ratio:
        new_w = round(src.height * target_ratio)
        left = round((src.width - new_w) * focus[0])
        src = src.crop((left, 0, left + new_w, src.height))
    else:
        new_h = round(src.width / target_ratio)
        top = round((src.height - new_h) * focus[1])
        src = src.crop((0, top, src.width, top + new_h))
    image.paste(src.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))


def new_canvas(box):
    global OFFSET
    x0, y0, x1, y1 = box
    OFFSET = (x0, y0)
    im = Image.new("RGB", (pt(x1 - x0), pt(y1 - y0)), PANEL)
    def p(v):
        if len(v) == 2:
            return (v[0] - x0, v[1] - y0)
        return tuple(a - b for a, b in zip(v, (x0, y0, x0, y0)))
    return im, p


def checkbox(draw, x, y, size=11, checked=False):
    draw.rectangle(AB((x, y, x + size, y + size)), outline=(150, 160, 175), width=pt(0.7))
    if checked:
        draw.line([A((x + 2, y + size / 2)), A((x + size * .45, y + size - 2)),
                   A((x + size - 1.5, y + 1.5))], fill=BLUE, width=pt(1.5), joint="curve")


def radio(draw, x, y, size=11):
    draw.ellipse(AB((x, y, x + size, y + size)), outline=(150, 165, 190), width=pt(.8))


def chevron(draw, x, y, size=7, color=(130, 145, 165)):
    draw.line([A((x, y)), A((x + size / 2, y + size / 2)), A((x + size, y))],
              fill=color, width=pt(1.2))


# --------------------------------------------------------------------------- page 3
def make_page3() -> Path:
    box = (505, 130, 1045, 755)
    im, p = new_canvas(box)
    d = ImageDraw.Draw(im)

    for x, y, w, h, pic, headline, desc, cta in [
        (517, 141, 248, 298, "caisse_restaurant.jpg", "Caisse tactile pour restaurant",
         "Encaissez plus vite, suivez vos ventes en temps réel et simplifiez le quotidien de vos équipes.",
         "Ça m'intéresse !"),
        (521, 441, 240, 307, "caisse_boutique.jpg", "Caisse tactile pour commerces",
         "Une solution adaptée à votre point de vente, à votre activité et à vos équipes.",
         "Obtenir une offre !"),
    ]:
        rr(d, p((x, y, x + w, y + h)), 6, (248, 248, 249))
        photo(im, p((x + 3, y + 3, x + w - 3, y + 124)), pic)
        d.rectangle(AB((x + 3, y + 3, x + w - 3, y + 22)), fill=(35, 52, 70))
        txt(d, p((x + 10, y + 7)), "CAISSE TACTILE  ·  COMMERCES & RESTAURANTS", 6.2, WHITE, True)
        d.rectangle(AB((x + 3, y + 124, x + w - 3, y + h - 3)), fill=LIGHT_GRAY)
        txt(d, p((x + 13, y + 136)), headline, 13.2, (25, 25, 30), True, w - 26)
        paragraph(d, p((x + 13, y + 164)), desc, 11, w - 30, (115, 115, 120), False, 15.5, 3)
        rr(d, p((x + 13, y + h - 74, x + w - 13, y + h - 41)), 16, WHITE)
        txt(d, p((x + 24, y + h - 64)), cta, 11.3, BLUE, True)
        txt(d, p((x + w - 34, y + h - 64)), "›", 14, BLUE, True)

    rr(d, p((755, 151, 1041, 618)), 7, WHITE)
    txt(d, p((767, 162)), "HelloLead", 13, (25, 25, 30), True)
    txt(d, p((850, 165)), "PRO", 7, BLUE, True)
    photo(im, p((761, 184, 1035, 258)), "caffe_terrasse.jpg")
    paragraph(d, p((775, 276)), "Trouvez la meilleure caisse pour votre commerce !",
              13.2, 248, BLUE, True, 18, 2)
    paragraph(d, p((775, 322)),
              "Comparez les offres de caisses tactiles adaptées à votre activité.",
              10, 240, (60, 65, 75), False, 14, 3)
    txt(d, p((775, 378)), "Concernant votre projet, vous êtes :", 9.5, (60, 65, 75))
    for yy, label in [(399, "Professionnel"), (431, "Responsable de point de vente")]:
        d.rectangle(AB((775, yy, 1025, yy + 25)), outline=(160, 180, 215), width=pt(.8))
        radio(d, 783, yy + 7)
        txt(d, p((797, yy + 7)), label, 9.5, (70, 80, 95))
    for yy, label in [(470, "Votre activité :"), (524, "Nombre de points de vente :")]:
        txt(d, p((775, yy)), label, 9.2, (60, 65, 75))
        d.rectangle(AB((775, yy + 14, 1025, yy + 42)), outline=(160, 180, 215), width=pt(.8))
        txt(d, p((785, yy + 22)), "Sélectionner", 9, (150, 155, 165))
        chevron(d, 1008, yy + 26)
    rr(d, p((775, 581, 818, 608)), 2, BLUE)
    txt(d, p((790, 586)), "«", 10, WHITE, True)
    rr(d, p((978, 581, 1025, 608)), 2, (105, 160, 230))
    txt(d, p((996, 586)), "»", 10, WHITE, True)

    out = TMP / "center3.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------- page 4
def make_page4() -> Path:
    box = (470, 85, 970, 760)
    im, p = new_canvas(box)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, im.height], fill=WHITE)

    rr(d, p((477, 89, 962, 403)), 4, WHITE, (235, 235, 240), .6)
    photo(im, p((483, 89, 956, 403)), "caisse_restaurant.jpg")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle(AB((483, 89, 700, 403)), fill=(8, 20, 35, 145))
    im.paste(Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB"))
    d = ImageDraw.Draw(im)
    txt(d, p((497, 265)), "Caisse tactile", 17, WHITE, True)
    paragraph(d, p((497, 292)), "Des offres adaptées\nà votre restaurant", 10, 175, WHITE, False, 15, 2)

    rr(d, p((700, 150, 950, 360)), 7, WHITE)
    txt(d, p((717, 154)), "Comparez les offres", 12, BLUE, True)
    txt(d, p((717, 171)), "pour votre projet caisse", 11, (30, 45, 70), True)
    paragraph(d, p((717, 190)), "Quel est votre besoin principal ?", 8.6, 215, (100, 110, 125), False, 11, 2)
    for yy, label in [(235, "Renouveler ma caisse"), (270, "Équiper un nouveau point de vente"),
                      (305, "Ajouter des terminaux")]:
        checkbox(d, 739, yy, 10)
        txt(d, p((755, yy - 1)), label, 8.5, (40, 50, 65))
    rr(d, p((867, 340, 930, 358)), 3, (0, 165, 195))
    txt(d, p((887, 343)), "Suivant", 9, WHITE, True)

    d.line(AB((484, 410, 955, 410)), fill=(225, 228, 235), width=pt(.7))
    txt(d, p((720, 421)), "Cafés · Restaurants · Boulangeries · Commerces", 9, (45, 50, 60), True,
        355, "ma")

    rr(d, p((477, 495, 962, 756)), 7, (241, 247, 253), (228, 234, 243), .6)
    rr(d, p((493, 506, 946, 549)), 5, (17, 43, 72))
    txt(d, p((515, 515)), "Extrait du formulaire", 17, WHITE, True)
    txt(d, p((515, 538)), "Étape 2 · Préciser votre projet", 8.5, (220, 235, 245))
    rr(d, p((497, 558, 942, 742)), 6, WHITE)
    txt(d, p((525, 571)), "Quel est votre besoin principal ?", 11.5, BLUE, True)
    options = ["Renouveler ma caisse actuelle", "Équiper un nouveau point de vente",
               "Ajouter des terminaux de paiement", "Moderniser mon encaissement",
               "Gérer mes ventes sur plusieurs sites", "Autre projet"]
    for i, label in enumerate(options):
        yy = 597 + i * 21
        checkbox(d, 549, yy, 10, i == 0)
        txt(d, p((565, yy - 2)), label, 10.5, (40, 50, 65))
    rr(d, p((860, 714, 924, 734)), 3, (0, 165, 195))
    txt(d, p((880, 717)), "Suivant", 9, WHITE, True)

    out = TMP / "center4.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------- page 5
def make_page5() -> Path:
    box = (402, 170, 1062, 645)
    im, p = new_canvas(box)
    d = ImageDraw.Draw(im)

    rr(d, p((408, 209, 723, 638)), 6, WHITE, (230, 232, 240), .6)
    d.line(AB((408, 240, 723, 240)), fill=(235, 235, 240), width=pt(.6))
    txt(d, p((418, 224)), "‹   ›      0:07 / 0:17     2,4 K commentaires     3,5 K partages     22 M vues",
        7.5, (115, 120, 130))
    d.ellipse(AB((422, 243, 454, 275)), fill=(23, 52, 85))
    txt(d, p((438, 263)), "HL", 9, WHITE, True, anchor="mm")
    txt(d, p((462, 246)), "HelloLead", 8.6, (30, 35, 45), True)
    txt(d, p((462, 259)), "Sponsorisé", 7.5, (120, 125, 135))
    txt(d, p((705, 248)), "···  ×", 9, (110, 115, 125))
    paragraph(d, p((422, 287)),
              "CAISSE 2026 — La sérénité de votre encaissement, sans compromis. Solution adaptée à votre point de vente.",
              8.5, 290, (35, 40, 50), False, 11.5, 2)
    photo(im, p((419, 309, 710, 597)), "caisse_installation.jpg")
    txt(d, p((421, 604)), "FORMULAIRE", 7, (110, 115, 125), True)
    txt(d, p((421, 615)), "Simple. Rapide. Sans engagement.", 7.5, (35, 40, 50), True)
    rr(d, p((640, 605, 704, 625)), 2, (240, 241, 243))
    txt(d, p((672, 615)), "En savoir plus", 7.5, (45, 50, 60), True, anchor="ma")

    rr(d, p((710, 172, 1058, 638)), 8, (234, 241, 250))
    photo(im, p((716, 178, 1052, 258)), "caisse_boutique.jpg")
    d.ellipse(AB((850, 168, 912, 230)), fill=(25, 40, 65))
    txt(d, p((881, 199)), "HelloLead", 7.5, WHITE, True, anchor="mm")
    rr(d, p((748, 205, 1020, 264)), 7, WHITE)
    txt(d, p((758, 212)), "DEVIS CAISSE TACTILE", 13, (20, 25, 35), True)
    txt(d, p((758, 231)), "Plusieurs devis gratuits pour votre équipement", 8.5, (80, 90, 105))
    for yy, label in [(276, "Quel type de caisse ?"), (367, "Quel est votre type de commerce ?"),
                      (459, "Quand souhaitez-vous être équipé ?")]:
        rr(d, p((748, yy, 1023, yy + 76)), 7, WHITE)
        txt(d, p((762, yy + 10)), label, 10.5, (25, 35, 55), True)
        d.rectangle(AB((762, yy + 34, 1009, yy + 62)), outline=(195, 200, 210), width=pt(.7))
        txt(d, p((772, yy + 42)), "Sélectionner", 9, (150, 155, 165))
        chevron(d, 993, yy + 46)
    rr(d, p((748, 582, 1023, 614)), 3, BLUE)
    txt(d, p((885, 598)), "Continuer", 10, WHITE, True, anchor="ma")

    out = TMP / "center5.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------- page 7
def make_page7() -> Path:
    box = (425, 90, 1010, 795)
    im, p = new_canvas(box)
    d = ImageDraw.Draw(im)

    rr(d, p((432, 97, 724, 792)), 4, WHITE, (235, 235, 240), .6)
    txt(d, p((443, 106)), "Comparateur", 13, (35, 40, 50), True)
    txt(d, p((548, 108)), "pro", 13, BLUE, True)
    paragraph(d, p((443, 135)), "Installation de caisse tactile\nQuel projet choisir ?",
              15.5, 265, (25, 30, 40), True, 21, 2)
    photo(im, p((443, 180, 713, 330)), "caisse_restaurant.jpg")
    rr(d, p((494, 342, 662, 370)), 14, (255, 210, 30))
    txt(d, p((578, 356)), "COMPAREZ LES SOLUTIONS", 8.5, (30, 30, 25), True, anchor="ma")
    txt(d, p((443, 390)), "À chaque commerce sa solution", 16, (35, 40, 50), True)
    for i, (head, sub) in enumerate([
        ("L'étude de votre besoin", "Un diagnostic rapide pour choisir la caisse adaptée à votre activité."),
        ("L'encaissement rapide", "Des terminaux tactiles fluides pour vos équipes et vos clients."),
        ("La gestion des ventes", "Suivez vos journées, vos stocks et vos indicateurs en temps réel."),
    ]):
        yy = 428 + i * 57
        d.rectangle(AB((443, yy, 474, yy + 31)), fill=(242, 243, 245))
        checkbox(d, 453, yy + 10, 11)
        txt(d, p((485, yy)), head, 11.5, (25, 30, 40), True)
        txt(d, p((485, yy + 17)), sub, 7.5, (125, 130, 140))
    rr(d, p((443, 636, 713, 752)), 3, (46, 46, 46))
    paragraph(d, p((461, 653)),
              "Votre projet caisse chiffré en 1 minute, par des installateurs partenaires !",
              9.5, 235, (255, 210, 30), True, 13, 2)
    txt(d, p((461, 687)), "Trouvez la caisse qui correspond à votre point de vente", 8, (200, 200, 200))
    rr(d, p((461, 708, 587, 731)), 12, (46, 46, 46), (255, 210, 30), .8)
    txt(d, p((524, 719)), "J'en profite", 8, (255, 210, 30), True, anchor="ma")
    rr(d, p((594, 708, 696, 731)), 12, (46, 46, 46), (255, 210, 30), .8)
    txt(d, p((645, 719)), "Être rappelé", 8, (255, 210, 30), True, anchor="ma")

    rr(d, p((743, 96, 1004, 677)), 3, WHITE, (235, 235, 240), .6)
    photo(im, p((749, 102, 998, 222)), "caffe_terrasse.jpg")
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle(AB((749, 102, 998, 222)), fill=(4, 25, 60, 115))
    im.paste(Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB"))
    d = ImageDraw.Draw(im)
    txt(d, p((760, 110)), "Comparateur", 10, WHITE, True)
    txt(d, p((841, 111)), "pro", 10, (140, 210, 255), True)
    paragraph(d, p((760, 140)), "Valorisez votre point de vente\navec une caisse tactile",
              12.5, 225, WHITE, True, 17, 2)
    txt(d, p((760, 240)), "BON À SAVOIR", 8, BLUE, True)
    paragraph(d, p((760, 255)),
              "Une caisse tactile s'adapte à votre activité : restauration, commerce ou artisanat.",
              7, 225, (60, 65, 75), False, 10, 2)
    paragraph(d, p((760, 282)),
              "Comparez plusieurs devis : matériel, logiciel, formation et service après-vente varient d'un fournisseur à l'autre.",
              6.5, 225, (60, 65, 75), False, 9, 4)
    rr(d, p((749, 480, 998, 567)), 3, (16, 36, 74))
    txt(d, p((760, 490)), "Optimisez votre encaissement et préparez", 8, WHITE, True)
    txt(d, p((760, 502)), "votre installation avec un installateur partenaire", 7.5, WHITE)
    photo(im, p((760, 518, 876, 558)), "caisse_installation.jpg")
    photo(im, p((880, 518, 990, 558)), "caisse_boutique.jpg")
    rr(d, p((826, 556, 922, 568)), 5, (16, 36, 74), (120, 150, 200), .5)
    txt(d, p((874, 561)), "Comparer les offres", 5.5, WHITE, True, anchor="ma")

    for x, w, title in [(748, 119, "Quel budget prévoyez-vous ?"),
                        (874, 126, "Quel équipement recherchez-vous ?")]:
        rr(d, p((x, 695, x + w, 784)), 4, WHITE, (225, 228, 235), .6)
        txt(d, p((x + 8, 703)), title, 7, (35, 40, 50), True, w - 22)
        for i in range(4):
            yy = 718 + i * 12
            radio(d, x + 10, yy, 7)
            d.rectangle(AB((x + 23, yy + 1, x + w - 10, yy + 6)), fill=(225, 228, 234))
        rr(d, p((x + w - 36, 771, x + w - 7, 782)), 1, (255, 205, 20))
        d.ellipse(AB((x + 7, 695, x + 17, 705)), fill=(230, 230, 230))
        txt(d, p((x + 12, 702)), "×", 6, (90, 90, 90), True, anchor="ma")

    out = TMP / "center7.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------- page 6
def make_page6() -> Path:
    """CRM screenshot showing a cash-register lead (the call-centre photo below it is kept)."""
    box = (405, 160, 1050, 520)
    im, p = new_canvas(box)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, im.width, im.height], fill=(218, 218, 218))

    # Application chrome
    d.rectangle(AB((405, 163, 1050, 213)), fill=(220, 220, 220))
    txt(d, p((416, 171)), "HelloLead", 12, (45, 50, 60), True)
    txt(d, p((492, 171)), "PRO", 5.5, BLUE, True)
    for x, label in [(530, "Moteur"), (590, "Paramétrage"), (670, "Statistiques"),
                     (760, "Fichiers Agences"), (862, "Marché HelloLead")]:
        txt(d, p((x, 172)), label, 6.6, (70, 75, 85))
    d.line(AB((405, 184, 1050, 184)), fill=(195, 195, 195), width=pt(.6))
    txt(d, p((655, 188)), "Campagne : Caisses tactiles", 6.2, (80, 85, 95))
    d.rectangle(AB((405, 196, 1050, 215)), fill=(32, 77, 132))
    txt(d, p((416, 200)), "Conduites d'Acheteurs", 6.6, WHITE, True)

    # Left column: lead record
    d.rectangle(AB((405, 215, 520, 520)), fill=(235, 235, 235))
    txt(d, p((413, 221)), "Société", 6.4, (45, 50, 60), True)
    for i, name in enumerate(["CAISSE DU CENTRE", "RESTAURANT LE MARCHE", "BOULANGERIE DES HALLES",
                              "SNACK ATLANTIQUE", "CAISSE DU CENTRE"]):
        rr(d, p((410, 233 + i * 20, 515, 250 + i * 20)), 1,
           (205, 220, 240) if i == 0 else (245, 245, 245))
        txt(d, p((414, 237 + i * 20)), name, 5.8, (45, 50, 60))
    txt(d, p((413, 337)), "Acheteur", 6.4, (45, 50, 60), True)
    txt(d, p((413, 350)), "Madame", 5.8, (70, 75, 85))
    txt(d, p((413, 361)), "CLAIRE", 5.8, (70, 75, 85))
    txt(d, p((413, 372)), "MARTIN", 5.8, (70, 75, 85))
    txt(d, p((413, 388)), "Direction générale > DG", 5.6, (70, 75, 85))
    txt(d, p((413, 400)), "email@exemple.fr", 5.6, BLUE)
    for i, line in enumerate(["Siret 852 147 963 00018", "NAF 56.10A - Restauration",
                              "Date de création : juin 2019", "Effectif 10 à 19",
                              "Professionnel", "Site Web"]):
        txt(d, p((413, 416 + i * 12)), line, 5.8, (70, 75, 85))

    # Centre: qualification questionnaire
    d.rectangle(AB((520, 215, 820, 520)), fill=WHITE)
    txt(d, p((530, 222)), "DEMANDE DE DEVIS : Caisse tactile", 7.2, (200, 45, 45), True)
    txt(d, p((530, 236)), "Avez-vous un projet de caisse tactile dans moins de 6 mois ?", 6.3, (45, 50, 60))
    radio(d, 534, 248, 7)
    txt(d, p((545, 247)), "Oui", 6, (45, 50, 60))
    radio(d, 568, 248, 7)
    txt(d, p((579, 247)), "Non", 6, (45, 50, 60))
    txt(d, p((534, 262)), "Quel type de caisse recherchez-vous ?  [Obligatoire]", 6.2, (45, 50, 60), True)
    for i, (label, checked) in enumerate([
        ("Caisse tactile avec logiciel de gestion", True),
        ("Terminal de paiement", True),
        ("Caisse avec gestion des stocks", False),
        ("Application de suivi des ventes", False),
        ("Bornes de commande", False),
    ]):
        checkbox(d, 536, 274 + i * 11, 6.5, checked)
        txt(d, p((548, 273 + i * 11)), label, 5.8, (60, 65, 75))
    txt(d, p((534, 334)), "Vous envisagez cet équipement à titre :  [Obligatoire]", 6.2, (45, 50, 60), True)
    radio(d, 536, 346, 6.5)
    txt(d, p((547, 345)), "Professionnel", 5.8, (60, 65, 75))
    radio(d, 600, 346, 6.5)
    txt(d, p((611, 345)), "Particulier", 5.8, (60, 65, 75))
    txt(d, p((534, 362)), "Nombre de points de vente  [Obligatoire]", 6.2, (45, 50, 60), True)
    for i, (label, checked) in enumerate([("1 point de vente", False),
                                          ("2 points de vente", False),
                                          ("3 points de vente et plus", True)]):
        radio(d, 536, 374 + i * 11, 6.5)
        if checked:
            d.ellipse(AB((537.5, 375.5 + i * 11, 540.5, 378.5 + i * 11)),
                      fill=(80, 90, 105))
        txt(d, p((548, 373 + i * 11)), label, 5.8, (60, 65, 75))
    txt(d, p((534, 411)), "Propriétaire de l'établissement ?  [Obligatoire]", 6.2, (45, 50, 60), True)
    radio(d, 536, 423, 6.5)
    txt(d, p((547, 422)), "Oui", 5.8, (60, 65, 75))
    radio(d, 568, 423, 6.5)
    txt(d, p((579, 422)), "Non", 5.8, (60, 65, 75))
    txt(d, p((534, 438)), "Échéance du projet  [Obligatoire]", 6.2, (45, 50, 60), True)
    for i, label in enumerate(["Moins de 3 mois", "3 à 6 mois", "Plus de 6 mois"]):
        radio(d, 536, 450 + i * 11, 6.5)
        txt(d, p((548, 449 + i * 11)), label, 5.8, (60, 65, 75))
    txt(d, p((534, 489)), "Disponibilité pour un appel : Demain à 11:00", 6, (45, 50, 60), True)

    # Right column: matching result
    d.rectangle(AB((820, 215, 1050, 520)), fill=WHITE)
    txt(d, p((832, 223)), "Résultat du matching :", 6.2, (45, 50, 60), True)
    d.rectangle(AB((832, 235, 1038, 252)), outline=(200, 75, 75), width=pt(.8))
    checkbox(d, 836, 239, 7)
    txt(d, p((848, 238)), "CAISSES ENREGISTREUSES TACTILES (B2B)", 5.6, (190, 60, 60), True)
    rr(d, p((832, 264, 938, 292)), 2, (105, 165, 80))
    txt(d, p((840, 271)), "Besoin réel et projet", 6.4, WHITE, True)
    txt(d, p((840, 281)), "immédiat", 6.4, WHITE, True)
    rr(d, p((942, 264, 1038, 292)), 2, (215, 135, 25))
    txt(d, p((948, 271)), "Besoin réel mais", 6.4, WHITE, True)
    txt(d, p((948, 281)), "société incorrecte", 6.4, WHITE, True)
    txt(d, p((832, 310)), "Critères détectés", 6.4, (45, 50, 60), True)
    for i, line in enumerate(["Projet de renouvellement", "3 points de vente",
                              "Échéance : 3 à 6 mois", "Décideur identifié",
                              "Créneau d'appel confirmé"]):
        txt(d, p((836, 324 + i * 13)), f"•  {line}", 6, (70, 80, 95))

    out = TMP / "center6.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------- PDF text
# Each list has exactly one entry per original baseline of the right-hand block.
RIGHT_LINES = {
    3: [  # 25 lines, Poppins 13
        ("Type de solution :", True), ("Caisse tactile avec logiciel de gestion", False),
        ("Profil de l’acheteur :", True), ("Professionnel (B2B), dirigeant", False),
        ("Type d’activité :", True), ("Boulangerie, point de vente de quartier", False),
        ("Nombre de points de vente :", True), ("1 point de vente", False),
        ("Besoin principal :", True), ("Accélérer l’encaissement, suivre les ventes", False),
        ("Budget envisagé :", True), ("2 000 € à 5 000 €", False),
        ("Sous quel délai souhaitez-vous être", True), ("équipé ?", True),
        ("Dans 1 à 3 mois", False),
        ("Entreprise : BOULANGERIE DES HALLES", False), ("Siret : 91247836500019", False),
        ("Activité : (Boulangerie artisanale", False), ("et pâtisserie avec un point de vente", False),
        ("Contact :", False), ("Adresse : 12 rue de la Paix", False),
        ("Ville : Paris", False), ("Code Postal : 75002", False),
        ("Tél :", False), ("Mail :", False),
    ],
    4: [  # 15 lines, DejaVu 11.3 / 10.3
        ("Type de solution :", True), ("Caisse tactile restaurant", False),
        ("Nombre de points de vente :", True), ("1 établissement", False),
        ("Échéance du projet :", True), ("Dans 1 à 3 mois", False),
        ("Entreprise : LE BISTROT DU PORT", False),
        ("Siret : 90246813500027", False), ("Activité : (Restauration traditionnelle", False),
        ("avec service au comptoir et", False), ("salle de 40 couverts)", False),
        ("Contact :", False), ("Adresse : 9 avenue du Littoral", False),
        ("Ville : Saint-Malo", False), ("Code postal : 35400", False),
        ("Tél :", False), ("Mail :", False),
    ],
    5: [  # 24 lines, Poppins 13
        ("Quel type de caisse ?", True), ("Caisse tactile avec terminal de paiement", False),
        ("Vous envisagez cette installation :", True), ("pour votre point de vente (B2B)", False),
        ("Statut et type de commerce :", True), ("Commerçant, commerce alimentaire", False),
        ("Nombre de points de vente :", True), ("2 points de vente", False),
        ("Sous quel délai souhaitez-vous être", True), ("équipée ?", True),
        ("Sous 3 mois", False), ("Logiciel souhaité :", True),
        ("Gestion des stocks et des ventes", False),
        ("Nom : MARTIN (exemple fictif)", False), ("Siret : 85120479300018", False),
        ("Projet : (Renouvellement de la caisse", False), ("de deux points de vente)", False),
        ("Contact :", False), ("Adresse : 16 rue des Tilleuls", False),
        ("Ville : La Roche-sur-Yon", False), ("Code Postal : 85000", False),
        ("Tél :", False), ("Mail :", False),
    ],
    7: [  # 24 lines, Poppins 13
        ("Êtes-vous déjà équipé d’une caisse ?", True), ("Oui, ancienne caisse", False),
        ("Type d’activité à équiper :", True), ("Restauration rapide, 3 points de vente", False),
        ("Nombre de terminaux souhaités :", True), ("3 caisses tactiles", False),
        ("Budget envisagé pour l’équipement :", True), ("8 000 € à 15 000 €", False),
        ("Souhaitez-vous un logiciel de", True), ("gestion des ventes ?", True),
        ("Oui", False), ("Échéance du projet :", True),
        ("Dans 3 à 6 mois", False),
        ("Entreprise : SNACK ATLANTIQUE", False), ("Siret : 90579135700043", False),
        ("Activité : (Restauration rapide", False), ("et vente à emporter sur trois", False),
        ("points de vente)", False), ("Contact :", False),
        ("Adresse : 310 chemin des Vergers", False), ("Ville : Aix-en-Provence", False),
        ("Code Postal : 13100", False), ("Tél :", False),
        ("Mail :", False),
    ],
    6: [  # 21 lines, Poppins 13
        ("Catégorie CRM du besoin :", True), ("Caisses enregistreuses tactiles", False),
        ("Logiciel de caisse / B2B", False),
        ("Type de projet et statut :", True), ("Renouvellement, professionnel (B2B)", False),
        ("Nombre de points de vente :", True), ("3 points de vente", False),
        ("Équipement actuel :", True), ("Caisse classique", False),
        ("Disponibilité pour un appel :", True), ("Demain à 11:00", False),
        ("Entreprise : BRASSERIE DES ALPES", False), ("Siret : 90135792400035", False),
        ("Activité : (Café, bar et restauration", False), ("avec trois points de vente)", False),
        ("Contact :", False), ("Adresse : 18 rue des Sources", False),
        ("Ville : Annecy", False), ("Code Postal : 74000", False),
        ("Tél :", False), ("Mail :", False),
    ],
}

CENTER_BOXES = {3: (505, 130, 1045, 755), 4: (470, 85, 970, 760),
                5: (402, 170, 1062, 645), 6: (405, 160, 1050, 520),
                7: (425, 90, 1010, 795)}
RIGHT_X = {3: 1090, 4: 1000, 5: 1080, 6: 1070, 7: 1070}
MAXW = {3: 285, 4: 295, 5: 285, 6: 298, 7: 298}
BARS = {
    3: [(1155, 663, 1230, 683), (1124, 742, 1218, 760), (1131, 763, 1321, 781),
        (1132, 774, 1319, 778)],
    4: [(1070, 677, 1175, 689), (1045, 745, 1133, 757), (1051, 762, 1193, 774)],
    5: [(1148, 629, 1300, 649), (1116, 707, 1210, 725), (1124, 729, 1288, 746)],
    6: [(1107, 745, 1201, 763), (1115, 764, 1280, 782), (1141, 665, 1221, 685),
        (1115, 776, 1228, 780)],
    7: [(1139, 661, 1194, 681), (1107, 741, 1201, 759), (1114, 762, 1279, 780),
        (1115, 773, 1278, 777)],
}


def rgb(value):
    return ((value >> 16 & 255) / 255, (value >> 8 & 255) / 255, (value & 255) / 255)


def fit_size(text, size, min_size, bold, pn):
    path = FONT_BOLD if (bold and pn == 4) else FONT_REG
    f = ImageFont.truetype(path, pt(size))
    s = size
    while s > min_size and f.getlength(text) > pt(MAXW[pn]):
        s -= 0.3
        f = ImageFont.truetype(path, pt(s))
    return s


def rebuild():
    doc = fitz.open(SOURCE)
    font_buffers = {name: doc.extract_font(xref)[3]
                    for xref, name in [(219, "popR"), (225, "popB"), (268, "djR"), (274, "djR")]}
    font_buffers["djR"] = doc.extract_font(274)[3]
    font_buffers["djB"] = doc.extract_font(268)[3]
    centers = {pn: fn() for pn, fn in {3: make_page3, 4: make_page4,
                                       5: make_page5, 6: make_page6,
                                       7: make_page7}.items()}

    for pn in (3, 4, 5, 6, 7):
        page = doc[pn - 1]
        spans = [s for b in page.get_text("dict")["blocks"] if b["type"] == 0
                 for l in b["lines"] for s in l["spans"]]
        cx0, cy0, cx1, cy1 = CENTER_BOXES[pn]
        rx = RIGHT_X[pn]
        right_from = 450 if pn == 4 else (330 if pn == 6 else 240)
        right_spans = [s for s in spans if s["bbox"][0] >= rx and s["bbox"][1] > right_from]
        annotation = ([s for s in spans if s["bbox"][0] >= 800 and
                       ("lien du RCS" in s["text"] or "vers landing" in s["text"]
                        or "page (formulaire)" in s["text"])]
                      if pn == 3 else [])

        for s in spans:
            x0, y0, x1, y1 = s["bbox"]
            in_right = s in right_spans
            in_center = x1 > cx0 and x0 < cx1 and y1 > cy0 and y0 < cy1
            keep = s in annotation or (pn != 3 and not in_right and not in_center)
            if in_right or (pn != 3 and in_center) or s in annotation:
                page.add_redact_annot(fitz.Rect(x0 - 1.5, y0 - 1.5, x1 + 2.5, y1 + 1.5),
                                      fill=False, cross_out=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                              text=fitz.PDF_REDACT_TEXT_REMOVE)

        # Erase the grey masking bars: the adapted lead examples have their own
        # (fictional) data, so the old masks would only cross out new text.
        for bar in BARS.get(pn, []):
            page.draw_rect(fitz.Rect(*bar), color=None,
                           fill=(244 / 255, 245 / 255, 251 / 255), overlay=True)

        # Fonts are registered after redaction so the resources are preserved.
        for name, buf in font_buffers.items():
            page.insert_font(fontname=name, fontbuffer=buf)

        # New centre visual replaces the solar mock-ups.
        page.insert_image(fitz.Rect(*CENTER_BOXES[pn]), filename=str(centers[pn]), overlay=True)
        for s in annotation:
            page.insert_text(s["origin"], s["text"], fontname="popR", fontsize=s["size"],
                             color=rgb(s["color"]))

        # Rebuild the right-hand lead example, line by line, on the original baselines.
        x = {3: 1098.9, 4: 1011.0, 5: 1091.2, 6: 1082.2, 7: 1081.9}[pn]
        y_positions = [s["origin"][1] for s in right_spans]
        lines = RIGHT_LINES[pn]
        if pn == 4:
            assert len(lines) == len(y_positions), (len(lines), len(y_positions))
        for i, (text, is_bold) in enumerate(lines[:len(y_positions)]):
            if not text:
                continue
            size = (11.3 if is_bold else 10.3) if pn == 4 else 13.0
            size = fit_size(text, size, 9.0 if pn == 4 else 10.5, is_bold, pn)
            name = ("djB" if pn == 4 else "popB") if is_bold else ("djR" if pn == 4 else "popR")
            color = rgb(BLUEHEX if is_bold else (0x171717 if pn == 4 else 0))
            page.insert_text((x, y_positions[i]), text, fontname=name, fontsize=size, color=color)

    doc.set_metadata({"title": "HelloLead | Caisses enregistreuses tactiles",
                      "author": "HelloLead",
                      "subject": "Génération de leads B2B - caisses enregistreuses tactiles"})
    doc.subset_fonts()
    doc.save(OUTPUT, garbage=4, deflate=True)
    print(f"Written {OUTPUT}")


if __name__ == "__main__":
    rebuild()
