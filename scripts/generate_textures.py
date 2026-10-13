"""Deterministic, original PBR maps. Python 3 + numpy + Pillow; no external art."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'textures'
OUT.mkdir(parents=True, exist_ok=True)
N = 512
rng = np.random.default_rng(1847)
y, x = np.mgrid[0:N, 0:N] / N

def noise(w, h):
    a = Image.fromarray(rng.integers(0, 256, (h, w), dtype=np.uint8))
    return np.asarray(a.resize((N, N), Image.Resampling.BICUBIC)).astype(float) / 255

def save(name, a):
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255)).save(OUT / (name + '.png'), optimize=True)

def maps(name, color, rough, metal, height, strength):
    # Rows run downward in PNG; UV v runs upward. glTF/OpenGL tangent +Y.
    dy, dx = np.gradient(height)
    v = np.stack((-dx * strength, dy * strength, np.ones_like(dx)), axis=-1)
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    save(name + '_BaseColor', color)
    save(name + '_Roughness', rough)
    save(name + '_Metallic', metal)
    save(name + '_Normal', v * .5 + .5)
    save(name + '_ORM', np.stack((np.ones_like(rough), rough, metal), axis=-1))

warp = .002 * np.sin(y * 14) + .001 * np.sin(y * 31 + x * 10)
grain = (np.sin((x + warp) * 620) * .5 + .5) ** 9
long = noise(110, 5)
pores = noise(240, 32)
cloud = noise(9, 12)
height = .35 * long - .11 * grain + .1 * pores
base = np.array([.255, .145, .067]) + ((long-.5)*.10 + (cloud-.5)*.07 - grain*.023)[..., None]
rough = np.clip(.65 + (long-.5)*.17 + grain*.09, .40, .9)
maps('Madera_limpia', base, rough, np.zeros_like(x), height, 1.5)

marks = Image.new('L', (N, N))
d = ImageDraw.Draw(marks)
for i in range(95):
    a, b = rng.integers(0, N, 2)
    d.line((int(a), int(b), int(a+rng.integers(-12, 12)), int(b+rng.integers(4, 65))), fill=int(rng.integers(80, 220)), width=int(rng.integers(1, 3)))
scars = np.asarray(marks.filter(ImageFilter.GaussianBlur(.45))) / 255
weather = np.clip((noise(14, 10)-.45)*2.2, 0, 1)
worn = base * (1-weather[...,None]*.24) + weather[...,None] * np.array([.19,.19,.17]) + scars[...,None]*.15
maps('Madera_desgastada', worn, np.clip(rough + weather*.19 + scars*.12, 0, 1), np.zeros_like(x), height - scars*.2, 2.5)

for name, tint, rbase in [('Acero', [.48,.51,.54], .46), ('Bronce', [.49,.31,.13], .43)]:
    cloud = noise(12, 12)
    fine = noise(210, 210)
    patina = np.clip((cloud-.55)*1.4, 0, .4)
    color = np.array(tint) + ((cloud-.5)*.11 + (fine-.5)*.045)[...,None]
    height = (fine-.5)*.018 + (cloud-.5)*.10
    rough = rbase + (cloud-.5)*.17 + (fine-.5)*.08
    metal = np.ones_like(x) * .97
    if name == 'Bronce':
        color = color*(1-patina[...,None]) + patina[...,None]*np.array([.13,.23,.18])
        # Fine chased lines; this is a normal-map relief, not modeled geometry.
        chased = np.exp(-((np.abs(np.sin((x+y)*np.pi*18)))/.15)**2)
        height += chased*.07
        rough += patina*.23
        metal -= patina*.35
    else:
        scratches = noise(180, 3)
        height += (scratches-.5)*.035
        rough += (scratches-.5)*.06
    maps(name, color, rough, metal, height, 3 if name=='Bronce' else 1.4)
print('20 PNG maps generated at 512 × 512 in', OUT)
