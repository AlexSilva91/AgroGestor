from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Fazenda, FazendaAcesso, FazendaModulo, ModuloSistema


WRITE_ACTIONS = {"create", "update", "delete", "manage"}


def user_is_super_admin(user):
    return bool(user and user.is_authenticated and user.is_superuser)


def user_farm_ids(user):
    if user_is_super_admin(user):
        return None

    farm_ids = set(
        FazendaAcesso.objects.filter(usuario=user, ativo=True).values_list("farm_id", flat=True)
    )
    if getattr(user, "farm_id", None):
        farm_ids.add(user.farm_id)
    return list(farm_ids)


def farms_for_user(user):
    if user_is_super_admin(user):
        return Fazenda.objects.all()
    return Fazenda.objects.filter(id__in=user_farm_ids(user))


def active_farm_id(request):
    farm_id = request.GET.get("farm_id") or request.session.get("active_farm_id")
    if farm_id:
        return str(farm_id)
    if getattr(request.user, "farm_id", None):
        return str(request.user.farm_id)
    farms = farms_for_user(request.user)
    if farms.count() == 1:
        return str(farms.first().id)
    return None


def active_farm_queryset(queryset, request, farm_field="farm"):
    farm_id = active_farm_id(request)
    if farm_id:
        return queryset.filter(**{f"{farm_field}_id": farm_id})
    return queryset


def tenant_queryset(queryset, user, farm_field="farm"):
    if user_is_super_admin(user):
        return queryset
    return queryset.filter(**{f"{farm_field}_id__in": user_farm_ids(user)})


def permitted_farm_ids(user, module, action="view"):
    if user_is_super_admin(user):
        return None

    ids = set()
    for access in FazendaAcesso.objects.filter(usuario=user, ativo=True).select_related("farm"):
        if has_farm_permission(user, access.farm, module, action):
            ids.add(access.farm_id)

    if getattr(user, "farm_id", None):
        farm = user.farm
        if has_farm_permission(user, farm, module, action):
            ids.add(user.farm_id)

    return list(ids)


def module_queryset(queryset, user, module, action="view", farm_field="farm"):
    if user_is_super_admin(user):
        return queryset
    return queryset.filter(**{f"{farm_field}_id__in": permitted_farm_ids(user, module, action)})


def tenant_get_or_404(queryset, user, farm_field="farm", **lookup):
    return get_object_or_404(tenant_queryset(queryset, user, farm_field), **lookup)


def get_request_farm(request, payload=None):
    payload = payload or {}
    farm_id = payload.get("farm_id") or request.GET.get("farm_id") or request.session.get("active_farm_id") or getattr(request.user, "farm_id", None)
    farms = farms_for_user(request.user)

    if farm_id:
        return farms.get(id=farm_id)

    if farms.count() == 1:
        return farms.first()

    if user_is_super_admin(request.user):
        farm = Fazenda.objects.order_by("criado_em").first()
        if farm:
            return farm

    raise ValidationError("Selecione uma fazenda para continuar.")


def _legacy_role_allows(user, farm, module, action):
    if getattr(user, "farm_id", None) != farm.id:
        return False

    if user.role in {"ADMIN", "FAZENDEIRO"}:
        return True

    return action == "view"


def has_farm_permission(user, farm, module, action):
    if user_is_super_admin(user):
        return True

    if not farm:
        return False

    modulo = ModuloSistema.objects.filter(codigo=module, ativo=True).first()
    if modulo and not FazendaModulo.objects.filter(farm=farm, modulo=modulo, liberado=True).exists():
        return False

    access = FazendaAcesso.objects.filter(usuario=user, farm=farm, ativo=True).first()
    if access:
        if access.perfil == "ADMIN":
            return True
        if module == "usuarios":
            return bool(access.can_manage_users)
        return bool(getattr(access, f"can_{action}_{module}", False))

    return _legacy_role_allows(user, farm, module, action)


def ensure_farm_permission(user, farm, module, action):
    if not has_farm_permission(user, farm, module, action):
        raise PermissionDenied("Você não tem permissão para executar esta ação nesta fazenda.")


def ensure_super_admin_confirmation(request):
    if request.method.upper() not in {"POST", "PUT", "PATCH", "DELETE"}:
        return
    if not user_is_super_admin(request.user):
        return
    if request.headers.get("X-Super-Admin-Confirm") == "1":
        return
    raise PermissionDenied("Confirmação de super admin obrigatória para alterar dados.")


def permission_error_response(exc):
    return JsonResponse({"success": False, "error": str(exc)}, status=403)
