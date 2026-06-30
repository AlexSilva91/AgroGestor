from .audit import registrar_acao


class AuditLogMiddleware:
    MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    IGNORED_PREFIXES = ("/static/", "/admin/jsi18n/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.method in self.MUTATING_METHODS
            and getattr(request, "user", None)
            and request.user.is_authenticated
            and not request.path.startswith(self.IGNORED_PREFIXES)
        ):
            try:
                registrar_acao(
                    request,
                    descricao=f"{request.method} {request.path}",
                    status_code=getattr(response, "status_code", None),
                )
            except Exception:
                pass

        return response
