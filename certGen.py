import os

from OpenSSL import crypto

if not os.path.exists("certificates"):
    os.makedirs("certificates")

TYPE_RSA = crypto.TYPE_RSA
TYPE_DSA = crypto.TYPE_DSA


def createKeyPair(type, bits):
    """
    Create a public/private key pair.
    Arguments: type - Key type, must be one of TYPE_RSA and TYPE_DSA
               bits - Number of bits to use in the key
    Returns:   The public/private key pair in a PKey object
    """
    pkey = crypto.PKey()
    pkey.generate_key(type, bits)
    return pkey


def createCertRequest(pkey, digest="sha1", **name):
    """
    Create a certificate request.
    Arguments: pkey   - The key to associate with the request
               digest - Digestion method to use for signing, default is md5
               **name - The name of the subject of the request, possible
                        arguments are:
                          C     - Country name
                          ST    - State or province name
                          L     - Locality name
                          O     - Organization name
                          OU    - Organizational unit name
                          CN    - Common name
                          emailAddress - E-mail address
    Returns:   The certificate request in an X509Req object
    """
    req = crypto.X509Req()
    subj = req.get_subject()

    for (key, value) in name.items():
        setattr(subj, key, value)

    req.set_pubkey(pkey)
    req.sign(pkey, digest)
    return req


def createCertificate(req, issuerCert, issuerKey, serial, notBefore, notAfter, digest="sha1"):
    """
    Generate a certificate given a certificate request.
    Arguments: req        - Certificate request to use
               issuerCert - The certificate of the issuer
               issuerKey  - The private key of the issuer
               serial     - Serial number for the certificate
               notBefore  - Timestamp (relative to now) when the certificate
                            starts being valid
               notAfter   - Timestamp (relative to now) when the certificate
                            stops being valid
               digest     - Digest method to use for signing, default is md5
    Returns:   The signed certificate in an X509 object
    """
    cert = crypto.X509()
    cert.set_serial_number(serial)
    cert.gmtime_adj_notBefore(notBefore)
    cert.gmtime_adj_notAfter(notAfter)
    cert.set_issuer(issuerCert.get_subject())
    cert.set_subject(req.get_subject())
    cert.set_pubkey(req.get_pubkey())
    cert.sign(issuerKey, digest)
    return cert


# generate CA self-signed certificate
cakey = createKeyPair(TYPE_DSA, 2048)
careq = createCertRequest(cakey, CN='Certificate Authority')
cacert = createCertificate(careq, careq, cakey, 0, 0, 60 * 60 * 24 * 365 * 5)  # five years
open('certificates/CA.pkey', 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, cakey).decode('ascii'))
open('certificates/CA.cert', 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cacert).decode('ascii'))

# generate CA signed certificate for Security Manager
pkey = createKeyPair(TYPE_RSA, 2048)
req = createCertRequest(pkey, CN="Security Manager")
cert = createCertificate(req, cacert, cakey, 1, 0, 60 * 60 * 24 * 365 * 5)  # five years
open('certificates/sm.pkey', 'w').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode('ascii'))
open('certificates/sm.cert', 'w').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('ascii'))

# generate CA signed certificate for CC node i
for i in range(1, 4):
    pkey = createKeyPair(TYPE_RSA, 2048)
    req = createCertRequest(pkey, CN="Node " + str(i))
    cert = createCertificate(req, cacert, cakey, 1, 0, 60 * 60 * 24 * 365 * 5)  # five years
    open('certificates/CC_' + str(i) + '.pkey', 'w').write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey).decode('ascii'))
    open('certificates/CC_' + str(i) + '.cert', 'w').write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('ascii'))
