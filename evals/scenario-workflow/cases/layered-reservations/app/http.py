from app.contracts import Reserve, Cancel

def reserve(payload, actor, service):
    return service.reserve(Reserve.validate(payload, actor))

def cancel(payload, actor, service):
    return service.cancel(Cancel.validate(payload, actor))
