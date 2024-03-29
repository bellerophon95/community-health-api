import json


def create_delivery(state, event):
    data = json.loads(event.data)
    return {
        'id': event.delivery_id,
        'budget': data['budget'],
        'notes': data['notes'],
        'status': 'created'
    }
