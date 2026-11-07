from app.contracts import Reserve, Cancel

def handle(command, actor, service):
    model = Reserve if command["operation"] == "reserve" else Cancel
    return getattr(service, command["operation"])(model.validate(command, actor))
