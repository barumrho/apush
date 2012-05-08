apush
=====

### A simple Apple push notification service provider in Python.

Important: `Service` overrides `identifier` attribute of `Notification` object.
Instead, errors include token.


```python
from apush import Service, Notification, ERROR_INVALID_TOKEN

token = 'hex-encoded token'.decode('hex')
service = Service('/path/to/certificate.pem')
notification = Notification(token, alert='A new notification', badge=1)
service.send(notification)
```

For several notifications, use `queue` and `flush`.
```python
for n in notifications:
    service.queue(n)

service.flush()
```

Check for errors after sending notifications.
```python
def remove(token):
    '''Remove token from database.'''
    ...

for (status, identifier, token) in service.errors:
    if status == ERROR_INVALID_TOKEN:
        remove(token)
```

Check feedback service for invalid tokens.
```python
for (timestamp, token) in service.feedbacks:
    remove(token)
```
