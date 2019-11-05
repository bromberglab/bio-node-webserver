from django_eventstream import send_event as send_stream_event


def send_event(type, data):
    send_stream_event("event", "event", {"type": type, "data": data})
