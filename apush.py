import ssl
import struct
import sys
from time import time
from socket import socket, AF_INET, SOCK_STREAM
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

        if self.badge:
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


GATEWAY = 'gateway.push.apple.com'
GATEWAY_SANDBOX = 'gateway.sandbox.push.apple.com'
GATEWAY_PORT = 2195

FEEDBACK = 'feedback.push.apple.com'
FEEDBACK_SANDBOX = 'feedback.sandbox.push.apple.com'
FEEDBACK_PORT = 2196

ERROR_NONE = 0
ERROR_PROCESSING = 1
ERROR_MISSING_TOKEN = 2
ERROR_MISSING_TOPIC = 3
ERROR_MISSING_PAYLOAD = 4
ERROR_INVALID_TOKEN_SIZE = 5
ERROR_INVALID_TOPIC_SIZE = 6
ERROR_INVALID_PAYLOAD_SIZE = 7
ERROR_INVALID_TOKEN = 8
ERRROR_UNKNOWN = 255


class Service(object):
    '''Apple push notification service.

    If you need to send more than one push notification, it is
    recommended to queue messages and flush. It will try to use only one
    connection to send all the push notifications, but if any error
    occurs (e.g. invalid token) the rest will be sent with a new
    connection.

    IMPORTANT: When a message is queued and flushed, identifier
    attirbute will be overriden in order to make sure all the
    queued notifications are sent. Errors are found in errors attribute
    as an array of tuples (status, identifier, token).
    '''
    def __init__(self, certfile, sandbox=True, timeout=5):
        '''Initialize service.

        Arguments
        - certfile: path to certificate in .pem format

        Optional
        - sandbox: Use sandbox gateway, True by default
        - timeout: Timeout to use to receive error response,
                   5 seconds by default
        '''
        self.certfile = certfile
        self.sandbox = sandbox
        self.errors = []
        self.timeout = 5
        self._socket = None
        self._feedback = None
        self._queue = []

    def __del__(self):
        self.disconnect()

    def _connect(self, addr):
        s = socket(AF_INET, SOCK_STREAM)
        s = ssl.wrap_socket(s, certfile=self.certfile,
                            ssl_version=ssl.PROTOCOL_SSLv3)
        s.connect(addr)
        return s

    @property
    def gateway(self):
        if not self._socket:
            if self.sandbox:
                addr = (GATEWAY_SANDBOX, GATEWAY_PORT)
            else:
                addr = (GATEWAY, GATEWAY_PORT)

            self._socket = self._connect(addr)
        return self._socket

    @property
    def feedback_service(self):
        if not self._feedback:
            if self.sandbox:
                addr = (FEEDBACK_SANDBOX, FEEDBACK_PORT)
            else:
                addr = (FEEDBACK, FEEDBACK_PORT)

            self._feedback = self._connect(addr)
        return self._feedback

    def disconnect(self):
        '''Close both sockets.'''
        if self._socket:
            self._socket.close()
            self._socket = None

        if self._feedback:
            self._feedback.close()
            self._feedback = None

    def queue(self, message):
        '''Queue a message to be sent.

        Overrides message identifier.
        '''
        message.identifier = len(self._queue)
        self._queue.append(message)

    def flush(self):
        '''Process all the messages in the queue.

        At the end, it will check for errors from Apple. If an error is
        found, messages that were not sent will be resent. Repeating
        until every message is attempted.

        '''
        sent = 0
        while sent < len(self._queue):
            for m in self._queue[sent:]:
                self.gateway.send(str(m))

            self.gateway.settimeout(5)
            try:
                error = self.gateway.recv(6)
                if len(error) == 6:
                    error = struct.unpack("!bbI", error)
                    index = error[2]
                    token = self._queue[index].token
                    self.errors.append((error[1], error[2], token))
                    sent = index + 1

                self.disconnect()
            except ssl.SSLError:
                # Timed out, meaning no error
                self._queue = []
                break

    def send(self, message):
        '''Send a single push notification.'''
        self.queue(message)
        self.flush()

    @property
    def feedbacks(self):
        '''Retrieve feedbacks from feedback service.

        Return an array of tuples (timestamp, token).
        '''
        feedbacks = []
        while True:
            fb = self.feedback_service.recv(4 + 2 + 32)
            if len(fb) < 38:
                break

            fb = struct.unpack("!IH32s", fb)
            feedbacks.append(fb[0], fb[2])

        self.disconnect()
        return feedbacks

