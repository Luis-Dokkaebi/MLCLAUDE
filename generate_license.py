import json
import base64
import time
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

def generate_license(hw_id):
    with open('scripts/tu_llave_maestra_privada.pem', 'rb') as f:
        private_key = RSA.import_key(f.read())
    
    payload = {
        "hw_id": hw_id,
        "exp": int(time.time()) + 86400 * 365,  # 1 year
        "tier": "enterprise",
        "max_cams": 16
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    hash_obj = SHA256.new(payload_str.encode('utf-8'))
    firma = pkcs1_15.new(private_key).sign(hash_obj)
    raw = payload_str.encode('utf-8') + b"||SIGNATURE||" + firma
    return base64.b64encode(raw).decode('utf-8')

hw_id = "7271ed8e44ed87583ddc166a8861f1d78a35953469ebbfb66d905fa4d96764d6"
print(generate_license(hw_id))
