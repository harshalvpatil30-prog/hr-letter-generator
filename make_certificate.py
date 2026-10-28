import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12

PASSWORD = b"123456789"      

# 1. Generate the private key
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# 2. Describe who this certificate belongs to
name = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "IN"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ShreeGURU Consulting"),
    x509.NameAttribute(NameOID.COMMON_NAME, "ShreeGURU HR"),
])

# 3. Build and sign the certificate (self-signed: issuer = subject)
now = datetime.datetime.now(datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now)
    .not_valid_after(now + datetime.timedelta(days=365 * 5))
    .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
    .add_extension(
        x509.KeyUsage(
            digital_signature=True, content_commitment=True,
            key_encipherment=False, data_encipherment=False,
            key_agreement=False, key_cert_sign=False, crl_sign=False,
            encipher_only=False, decipher_only=False,
        ),
        critical=True,
    )
    .sign(key, hashes.SHA256())
)

# 4. Save private key + certificate together in a password-protected .p12 file
p12_bytes = pkcs12.serialize_key_and_certificates(
    name=b"acme-hr", key=key, cert=cert, cas=None,
    encryption_algorithm=serialization.BestAvailableEncryption(PASSWORD),
)
with open("assets/hr_signer.p12", "wb") as f:
    f.write(p12_bytes)

# 5. Save the PUBLIC certificate separately (safe to share, used to "trust" it)
with open("assets/hr_signer.cer", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.DER))

print("Created assets/hr_signer.p12 and assets/hr_signer.cer")