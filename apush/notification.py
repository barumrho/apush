import struct
import sys
from time import time
try:
    import json
except ImportError:
    import simplejson as json

class Notification(object):
    '''Notification payload

    Keyword arguments:
    - alert: str or dict following Apple's extended format
    - badge: number to display on app icon badge
    - identifier: integer to identify this notification, used for errors
    - expiry: timestamp since UNIX epoch, default: 1 year
    - extra: dict of data to send to the app
    '''
    def __init__(self, token, **kwargs):
        if len(token) != 32:
            raise ValueError, u'Token must be a 32-byte binary string.'

        self.token = token
        self.alert = kwargs.get('alert')
        self.badge = kwargs.get('badge')
        self.sound = kwargs.get('sound')
        self.identifier = kwargs.get('identifier', 0)
        self.expiry = kwargs.get('expiry', long(time() + 365 * 86400))
        self.extra = kwargs.get('extra')

    def __str__(self):
        '''Return string representation of the payload.'''
        aps = {}
        if self.alert:
            aps['alert'] = self.alert

        if self.badge is not None:
            aps['badge'] = self.badge

        if self.sound:
            aps['sound'] = self.sound

        data = {'aps': aps}
        if self.extra:
            data.update(self.extra)

        encoded = json.dumps(data)
        length = len(encoded)

        if length > 256:
            raise ValueError, u'Payload exceeds 256-byte limit'

        return struct.pack('!bIIH32sH%(length)ds' % {'length': length},
                           1, self.identifier, self.expiry,
                           32, self.token, length, encoded)

