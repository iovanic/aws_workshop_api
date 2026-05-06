"""
Seed catalogue with the six fictional drones used in Next Drones Shop (Phase 2).

Usage (with DATABASE_URL set):
  uv run python -m app.seed
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.database import SessionLocal, init_db
from app.models import Product

DRONES_SEED = [
    {
        "id": "skhawk-x1",
        "name": "SkyHawk X1",
        "tagline": "Rendimiento aéreo con silencio asombroso",
        "description": (
            "El SkyHawk X1 está englobado con rotores plegables y batería de 45 min "
            "de vuelo simulada. Incluye modo cine 4K y retorno automático. Ideal para "
            "quienes quieren un primer toque pro sin miedo a aprender a pilotar en "
            "serio (con advertencias legales de siempre, claro)."
        ),
        "price": 329.00,
        "images": [
            "/images/sky_hawk_x1/sky_hawk_x1_1.png",
            "/images/sky_hawk_x1/sky_hawk_x1_2.png",
        ],
    },
    {
        "id": "nightviper-3000",
        "name": "NightViper 3000",
        "tagline": "Caza nocturna (solo en cielos permitidos)",
        "description": (
            "Diseñado con luces de navegación RGB programables y carcasa furtiva. "
            "Incluye sensores de proximidad y app para rutas con máscaras de luz. "
            "No vuela solo de verdad: tú pones las reglas y el mapa, nosotros el "
            "estilo y la ficción."
        ),
        "price": 499.00,
        "images": [
            "/images/night_viper_3000/night_viper_3000_1.png",
            "/images/night_viper_3000/night_viper_3000_2.png",
        ],
    },
    {
        "id": "cloudhopper-nano",
        "name": "CloudHopper Nano",
        "tagline": "Tan pequeño que casi se pierde de vista",
        "description": (
            "Un microcoptero con helipuerto de bolsillo. Pesa menos que un bocadillo "
            "y soporta viento moderado. Perfecto para interiores, selfies épicas y "
            "gatos confundidos. Batería intercambiable; pack de 3 baterías se vende "
            "aparte (en nuestra cabeza, al menos)."
        ),
        "price": 189.00,
        "images": [
            "/images/cloud_hopper_nano/cloud_hopper_nano_1.png",
            "/images/cloud_hopper_nano/cloud_hopper_nano_2.png",
        ],
    },
    {
        "id": "stormcopter-alpha",
        "name": "StormCopter Alpha",
        "tagline": "Resistencia a lluvia… en nuestro universo paralelo",
        "description": (
            "Carcasa reforzada, motores sin escobillas y módulo de carga (hasta 2 kg "
            "de sueños y envíos ficcionales). Incluye transmisor de largo alcance y "
            "gimbal de 3 ejes. La lluvia real sigue estando mojada: consulta clima y "
            "normativa local."
        ),
        "price": 629.00,
        "images": [
            "/images/storm_copter_alpha/storm_copter_alpha_1.png",
            "/images/storm_copter_alpha/storm_copter_alpha_2.png",
        ],
    },
    {
        "id": "aether-hexa",
        "name": "Aether Hexa",
        "tagline": "Seis brazos, cero piedad para la gravedad (virtual)",
        "description": (
            "Plataforma hexacóptero para carga estable y cine en movimiento. Ruedas "
            "de aterrizaje retraíbles, GPS simulado y perfiles de vuelo para "
            "creadores. Si buscas cine: aquí te damos cine, drones y puro invento."
        ),
        "price": 749.00,
        "images": [
            "/images/aether_hexa/aether_hexa_1.png",
            "/images/aether_hexa/aether_hexa_2.png",
        ],
    },
    {
        "id": "quantum-orb",
        "name": "Quantum Orb",
        "tagline": "Forma de esfera, alma de laboratorio inexistente",
        "description": (
            "Diseño esférico con sensores 360° y estabilizador reactivo. Incluye "
            "grabación 5.1 envolvente (en ficción) y retransmisión a gafas VR "
            "compatibles. El nombre suena a ciencia; el producto, a puro módelo "
            "Next Drones Shop."
        ),
        "price": 429.00,
        "images": [
            "/images/quantum_orb/quantum_orb_1.png",
            "/images/quantum_orb/quantum_orb_2.png",
        ],
    },
]


def seed_catalogue(db: Session) -> int:
    count = 0
    for row in DRONES_SEED:
        existing = db.get(Product, row["id"])
        if existing:
            for k, v in row.items():
                setattr(existing, k, v)
        else:
            db.add(Product(**row))
        count += 1
    db.commit()
    return count


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        n = seed_catalogue(db)
        print(f"Upserted {n} products.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
