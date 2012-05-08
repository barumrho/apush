apush
=====

A Simple Apple Push Notification Service Provider.

```python
from apush import Service, Notification, ERROR_INVALID_TOKEN

token = 'hex-encoded token'.decode('hex')
service = Service('/path/to/certificate.pem')
notification = Notification(token, alert='A new notification', badge=1)
service.send(notification)

# For several notifications
for n in notifications:
    service.queue(n)

service.flush()

# Check errors
for (status, identifier, token) in service.errors:
    if status == ERROR_INVALID_TOKEN:
        remove(token)


# Check feedback service for invalid tokens
for (timestamp, token) in service.feedbacks:
    remove(token)

```
