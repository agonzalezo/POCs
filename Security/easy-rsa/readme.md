Certificates
============
### Basic easyrsa usage to generate CA and sign certificates.

## Install ## 
- Install easyrsa from repo [Github](https://github.com/OpenVPN/easy-rsa/releases/tag/v3.1.7)

## Create a PKI and CA ## 
- These commands generate a pki folder and a CA key pair to sign other certificates. 
- > ./easyrsa init-pki
- > ./easyrsa build-ca

## Generate and sign children certificate. ## 
- > ./easyrsa build-server-full {certificate.name}

## More ##
- you can generate a other CA to generate Request and Sign with the principal CA.
- > ./easyrsa --pki=test init-pki
- > ./easyrsa --pki=test build-ca
- > ./easyrsa --pki=test gen-req {certificate.name}
- And with the principal CA Sign it.
- > ./easyrsa sign-req server {certificate.name}

- In the sign step you can add alternatives names to the certificate using options.
- > ./easyrsa --san=DNS:*.netsys.uno sign-req server aws.netsys.local