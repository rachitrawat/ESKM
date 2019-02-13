# ESKM
Python implementation of distributed SSH key manager

## Abstract
Large enterprises often face difficulty in managing the high number of SSH keys. In this
report, we study and implement ESKM - a distributed enterprise SSH key manager.
ESKM is a secure and fault-tolerant logically-centralized SSH key manager. In ESKM
architecture, SSH private keys are never stored at any single node. Instead, each node
only stores a share of the private key. These shares are refreshed at regular intervals for
enforced security. For signing, the system uses k-out-of-n threshold RSA signatures.

### How to?
1. Build patched OpenSSL [(src)](https://github.com/rachitrawat/openssl_1.0.2n) with support for threshold RSA signatures 
2. Use given CC_1.py template for your Control Cluster backend
3. Use given SM.py template for your Security Manager backend

Technical Report: [Link](https://github.com/rachitrawat/ESKM/blob/master/readme.pdf) </br>
Original Paper: [Link](https://eprint.iacr.org/2018/389.pdf)
