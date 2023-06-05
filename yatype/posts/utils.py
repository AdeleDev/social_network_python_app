from django.core.paginator import Paginator


def get_page_obj(request, post_list):
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
