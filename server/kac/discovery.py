from zeroconf import ServiceInfo, Zeroconf
import socket


_zeroconf = None
_info = None


def discovery_register(app):
    return
    # global _zeroconf, _info

    # desc = {}
    # _info = ServiceInfo("_http._tcp.local.",
    #                     "kac._http._tcp.local.",
    #                     socket.inet_aton(socket.gethostbyname(socket.getfqdn())), 8000, 0, 0,
    #                     desc, socket.getfqdn())

    # _zeroconf = Zeroconf()
    # _zeroconf.register_service(_info)


def discovery_unregister(app):
    return
    # global _zeroconf, _info
    # _zeroconf.unregister_service(_info)
    # _zeroconf.close()
