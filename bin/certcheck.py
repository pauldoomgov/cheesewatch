#!/usr/bin/env python3
# Enumerate a certificate and trust chain

import contextlib
import datetime
import socket
import sys
import json
from OpenSSL import SSL


@contextlib.contextmanager
def open_tls_socket(hostname):
    port = 443
    if ":" in hostname:
        (hostname, port) = hostname.split(":")

    context = SSL.Context(method=SSL.TLSv1_METHOD)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock = SSL.Connection(context=context, socket=sock)
    sock.settimeout(5)
    sock.set_tlsext_host_name(hostname.encode())
    try:
        sock.connect((hostname, port))
        sock.setblocking(1)
        sock.do_handshake()

        yield sock

    finally:
        sock.shutdown()
        sock.close()


def fetch_cert_expiration_time(sock):
    notafter = sock.get_peer_certificate().get_notAfter().decode("ascii")
    return datetime.datetime.strptime(notafter, "%Y%m%d%H%M%SZ").isoformat()


def nice_subject(cert_subject):
    # Remove surrounding noise - Just return a subject path
    # In: "<X509Name object '/C=US/O=Let's Encrypt/CN=R3'>""
    # Out: "/C=US/O=Let's Encrypt/CN=R3"
    return "'".join(cert_subject.__str__().split("'")[1:-1])


def enumerate_cert_chain(sock, chain={}):
    for cert in sock.get_peer_cert_chain():
        subject = nice_subject(cert.get_subject())
        chain[subject] = {
            "serial": cert.get_serial_number(),
            "issuer": nice_subject(cert.get_issuer()),
        }

    return chain


def main():
    if len(sys.argv) < 2:
        sys.stderr.write(
            "Please specify at least one FQDN (with option port) to connect to\n"
        )
        sys.exit(1)

    out = {}

    for hostname in sorted(sys.argv[1:]):
        with open_tls_socket(hostname) as sock:
            out[hostname] = {
                "expiration": fetch_cert_expiration_time(sock),
                "chain": enumerate_cert_chain(sock),
            }

    # All that to get a fully sorted record dump.  :sigh:
    print(json.dumps(out, indent=4))

    sys.exit(0)


if __name__ == "__main__":
    main()
