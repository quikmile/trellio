from .jsonprotocol import TrellioProtocol


def get_trellio_protocol(handler):
    return TrellioProtocol(handler)
