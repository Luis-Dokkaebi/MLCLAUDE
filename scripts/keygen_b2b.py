# scripts/keygen_b2b.py
# ===================================================================
# HERRAMIENTA INTERNA DEL PROVEEDOR — NUNCA se distribuye al cliente.
# Firma licencias con la llave privada RSA-2048.
# ===================================================================

from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import base64
import json
import datetime
import os
import sys


class B2B_Keygen:
    def __init__(self, private_key_path: str = None):
        """Carga la llave privada RSA-2048 del proveedor."""
        if private_key_path is None:
            # Buscar en el mismo directorio que este script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            private_key_path = os.path.join(script_dir, "tu_llave_maestra_privada.pem")

        if not os.path.exists(private_key_path):
            print(f"ERROR FATAL: No se encontro la llave privada en: {private_key_path}")
            print("Ejecute primero: python scripts/generar_llaves_maestras.py")
            sys.exit(1)

        with open(private_key_path, "rb") as f:
            self.private_key = RSA.import_key(f.read())

        print("[KEYGEN] Llave privada RSA-2048 cargada exitosamente.\n")

    def emitir_licencia(self, client_hardware_id: str, dias_validez: int = 365, max_camaras: int = 4) -> str:
        """
        Genera una licencia Base64 firmada criptograficamente.

        Args:
            client_hardware_id: El Machine ID SHA-256 del hardware del cliente.
            dias_validez: Duracion de la suscripcion en dias.
            max_camaras: Limite de camaras simultáneas (upselling B2B).

        Returns:
            String Base64 — la licencia lista para enviar al cliente.
        """
        # 1. Calcular Fecha de Vencimiento (Epoch UTC)
        fecha_expiracion = datetime.datetime.now() + datetime.timedelta(days=dias_validez)
        epoch_expiracion = int(fecha_expiracion.timestamp())

        # 2. Crear el Contrato (Payload JSON minificado)
        payload = {
            "hw_id": client_hardware_id,
            "exp": epoch_expiracion,
            "tier": "enterprise",
            "max_cams": max_camaras
        }
        payload_str = json.dumps(payload, separators=(',', ':'))

        # 3. Firmar el Contrato con RSA-2048 (imposible de falsificar sin llave privada)
        hash_obj = SHA256.new(payload_str.encode('utf-8'))
        firma = pkcs1_15.new(self.private_key).sign(hash_obj)

        # 4. Empaquetar: Payload + Separador + Firma → Base64
        licencia_cruda = payload_str.encode('utf-8') + b"||SIGNATURE||" + firma
        licencia_final_base64 = base64.b64encode(licencia_cruda).decode('utf-8')

        print("=" * 60)
        print("      NUEVA SUSCRIPCION B2B EMITIDA CON EXITO")
        print("=" * 60)
        print(f"  Machine ID:  {client_hardware_id[:20]}...{client_hardware_id[-10:]}")
        print(f"  Valido hasta: {fecha_expiracion.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Max Camaras:  {max_camaras}")
        print(f"  Tier:         ENTERPRISE")
        print("-" * 60)
        print("  LLAVE DE ACTIVACION (copiar y enviar al cliente):")
        print("-" * 60)
        print(licencia_final_base64)
        print("-" * 60)

        return licencia_final_base64


if __name__ == "__main__":
    keygen = B2B_Keygen()

    print("=" * 60)
    print("   OFICINA EFICIENCIA VMS — PORTAL DE EMISIÓN B2B")
    print("=" * 60)

    if len(sys.argv) > 1:
        hw_cliente = sys.argv[1]
    else:
        hw_cliente = input("Pegue el Machine ID SHA-256 del cliente: ").strip()

    if not hw_cliente:
        print("Error: El Machine ID no puede estar vacio.")
        sys.exit(1)

    dias = input("Dias de suscripcion (default=365): ").strip()
    dias = int(dias) if dias else 365

    cams = input("Limite de camaras (default=4): ").strip()
    cams = int(cams) if cams else 4

    keygen.emitir_licencia(hw_cliente, dias, cams)
