from django.http import JsonResponse
from django.shortcuts import render


def response(request, code, message, status):
    if request.path.startswith("/api/"):
        return JsonResponse({"error": {"code": code, "message": message}}, status=status)
    return render(request, "verse/error.html", {"message": message}, status=status)


def csrf_failure(request, reason=""):
    return response(request, "csrf_failed", "页面凭证已失效，请刷新页面后重试。", 403)


def bad_request(request, exception):
    return response(request, "bad_request", "请求无效。", 400)


def permission_denied(request, exception):
    return response(request, "permission_denied", "无权执行该操作。", 403)


def not_found(request, exception):
    return response(request, "not_found", "找不到该页面。", 404)


def server_error(request):
    return response(request, "server_error", "服务暂时不可用，请稍后重试。", 500)
