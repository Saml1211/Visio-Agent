class CollaborationProtocol:
    EVENT_TYPES = [
        "cursor_move",
        "shape_add",
        "connector_update",
        "style_change"
    ]
    
    def serialize(self, event):
        return {
            "type": event['type'],
            "user": event['user'],
            "timestamp": datetime.now().isoformat(),
            "data": event['data']
        } 