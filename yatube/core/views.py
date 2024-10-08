from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def permission_denied_view(request, exception):
    return render(request, 'core/403csrf.html', status=403)
