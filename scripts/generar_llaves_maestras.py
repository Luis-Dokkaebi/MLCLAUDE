# scripts/generar_llaves_maestras.py
# ===================================================================
# CONFIDENCIAL — Solo se ejecuta 1 vez para crear el par de llaves.
# La llave privada NUNCA se distribuye. La pública se embebe en drm.py
# ===================================================================
from Crypto.PublicKey import RSA
import os

def generar_par_de_llaves(output_dir=None):
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generando par de llaves RSA-2048 para DRM B2B...")
    key = RSA.generate(2048)

    # 1. Llave Privada — SECRETA (nunca se compila en el .exe)
    private_path = os.path.join(output_dir, "tu_llave_maestra_privada.pem")
    with open(private_path, "wb") as f:
        f.write(key.export_key())
    print(f"  [PRIVADA] Guardada en: {private_path}")

    # 2. Llave Publica — Se embebe en src/security/drm.py
    public_path = os.path.join(output_dir, "llave_publica_clientes.pem")
    with open(public_path, "wb") as f:
        f.write(key.publickey().export_key())
    print(f"  [PUBLICA] Guardada en: {public_path}")

    print("\n¡Éxito! Guarde 'tu_llave_maestra_privada.pem' en una USB segura.")
    print("La llave pública será incrustada automáticamente en drm.py por el agente.\n")

    return private_path, public_path

if __name__ == "__main__":
    generar_par_de_llaves()
