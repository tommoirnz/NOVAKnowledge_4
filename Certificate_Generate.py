# generate_cert.py
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime, ipaddress, socket

# This sets up the certificates for your mobile device otherwise voice will not work
# Then your URL will be https:// and not http://
# Advise you use chrome if you use a mobile device as you can bypass certificate problems

# Run this program ONCE ONLY to generate key.pem and cert.pem
# Your local IP is detected automatically.

# Then set Firewall to let us in:
# In Powershell ADMIN:
# New-NetFirewallRule -DisplayName "Nova Web 8080" -Direction Inbound -Protocol TCP -LocalPort 8080 -Action Allow

# Then use Chrome on phone or remote device. You may have to delete cache first
# Only then will speech recognition run from your mobile device!
# Otherwise, you can run with no microphone on http://


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


local_ip = get_local_ip()
print(f"Detected local IP: {local_ip}")

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME, local_ip),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.IPAddress(ipaddress.IPv4Address(local_ip)),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)

with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))

with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print(f"cert.pem and key.pem generated for {local_ip}")
print(f"Access Nova at: https://{local_ip}:8080")