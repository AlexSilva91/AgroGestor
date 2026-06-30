import json

from django.core.exceptions import ObjectDoesNotExist

from .models import Fazenda, LogAcao
from .permissions import farms_for_user, user_is_super_admin


SENSITIVE_KEYS = {
    "password",
    "confirm_password",
    "senha",
    "csrfmiddlewaretoken",
    "token",
    "authorization",
    "secret",
}


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def sanitize(value):
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                clean[key] = "***"
            else:
                clean[key] = sanitize(item)
        return clean
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def payload_from_request(request):
    if request.method == "GET":
        return sanitize(request.GET.dict())

    content_type = request.META.get("CONTENT_TYPE", "")
    try:
        if "application/json" in content_type:
            return sanitize(json.loads(request.body.decode("utf-8") or "{}"))
        if request.POST:
            return sanitize(request.POST.dict())
    except Exception:
        return {"raw": "<payload indisponivel>"}
    return {}


def farm_from_request(request, payload=None):
    payload = payload or {}
    farm_id = (
        payload.get("farm_id")
        or request.GET.get("farm_id")
        or request.session.get("active_farm_id")
        or getattr(request.user, "farm_id", None)
    )
    if not farm_id:
        return None
    try:
        farms = Fazenda.objects.all() if user_is_super_admin(request.user) else farms_for_user(request.user)
        return farms.get(id=farm_id)
    except (ObjectDoesNotExist, ValueError, TypeError):
        return None


def action_from_method(method):
    return {
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }.get(method.upper(), "OTHER")


def registrar_acao(request, acao=None, descricao="", farm=None, dados=None, status_code=None, tabela="HTTP"):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        user = None

    payload = sanitize(dados if dados is not None else payload_from_request(request))
    farm = farm or farm_from_request(request, payload)

    return LogAcao.objects.create(
        farm=farm,
        usuario=user,
        acao=acao or action_from_method(request.method),
        tabela_afetada=tabela,
        descricao=descricao,
        ip_usuario=client_ip(request),
        metodo=request.method,
        caminho=request.path[:255],
        status_code=status_code,
        user_agent=request.META.get("HTTP_USER_AGENT", "")[:2000],
        dados=payload,
    )
