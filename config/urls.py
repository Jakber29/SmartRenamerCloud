"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from core import views



def healthz(_):  # simple sanity check
    return JsonResponse({"ok": True})

def home(_):
    return HttpResponse("Django is running ✅")




urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/",  auth_views.LoginView.as_view(),  name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Dashboard uses the shared base + sidebar
    path("", views.dashboard, name="dashboard"),
    
    # File Manager
    path("files/", views.file_manager, name="file_manager"),
    path("files/upload/", views.upload_file, name="upload_file"),
    path("files/preview/<int:file_id>/", views.preview_file, name="preview_file"),
    path("files/download/<int:file_id>/", views.download_file, name="download_file"),
    path("files/delete/<int:file_id>/", views.delete_file, name="delete_file"),
    path("files/rename/", views.rename_file, name="rename_file"),
    path("files/save-notes/", views.save_notes, name="save_notes"),
    
    # Projects
    path("projects/", views.projects_list, name="projects_list"),
    path("projects/create/", views.create_project, name="create_project"),
    path("projects/update/<int:project_id>/", views.update_project, name="update_project"),
    path("projects/delete/<int:project_id>/", views.delete_project, name="delete_project"),
    path("api/projects/<int:project_id>/superintendents/", views.get_project_superintendents, name="get_project_superintendents"),
    path("api/projects/<int:project_id>/assign-superintendents/", views.assign_project_superintendents, name="assign_project_superintendents"),
    
    # Vendors
    path("vendors/", views.vendors_list, name="vendors_list"),
    path("vendors/create/", views.create_vendor, name="create_vendor"),
    path("vendors/update/<int:vendor_id>/", views.update_vendor, name="update_vendor"),
    path("vendors/delete/<int:vendor_id>/", views.delete_vendor, name="delete_vendor"),
    path("api/vendors/update-classes/", views.update_vendor_classes, name="update_vendor_classes"),
    
    # Autocomplete APIs
    path("api/autocomplete/projects/", views.autocomplete_projects, name="autocomplete_projects"),
    path("api/autocomplete/vendors/", views.autocomplete_vendors, name="autocomplete_vendors"),
    
    # Transactions
    path("transactions/", views.transactions_list, name="transactions_list"),
    path("api/transactions/create/", views.create_transaction, name="create_transaction"),
    path("api/transactions/<int:transaction_id>/update/", views.update_transaction, name="update_transaction"),
    path("api/transactions/<int:transaction_id>/delete/", views.delete_transaction, name="delete_transaction"),
    path("api/transactions/clear-all/", views.clear_all_transactions, name="clear_all_transactions"),
    path("api/transactions/clear-matches/", views.clear_all_matches, name="clear_all_matches"),
    path("api/transactions/upload-csv/", views.upload_csv_transactions, name="upload_csv_transactions"),
    
    # Bills
    path("bills/", views.bills_list, name="bills_list"),
    path("api/bills/matching-transactions/", views.get_matching_transactions, name="get_matching_transactions"),
    path("api/bills/create/", views.create_bill, name="create_bill"),
    path("api/bills/unmatch/", views.unmatch_transaction, name="unmatch_transaction"),
    
    # Users (Admin only)
    path("users/", views.users_list, name="users_list"),
    path("api/users/create/", views.create_user, name="create_user"),
    path("api/users/update-card/", views.update_user_card, name="update_user_card"),
    path("api/users/update-groups/", views.update_user_groups, name="update_user_groups"),
    path("api/users/delete/", views.delete_user, name="delete_user"),
    path("api/users/impersonate/", views.impersonate_user, name="impersonate_user"),
    path("api/users/stop-impersonation/", views.stop_impersonation, name="stop_impersonation"),
    path("api/users/change-password/", views.change_user_password, name="change_user_password"),
    path("api/users/toggle-status/", views.toggle_user_status, name="toggle_user_status"),
    
    # Classes (Admin only)
    path("classes/", views.classes_list, name="classes_list"),
    path("api/classes/create/", views.create_class, name="create_class"),
    path("api/classes/update/", views.update_class, name="update_class"),
    path("api/classes/delete/", views.delete_class, name="delete_class"),
    
    # Settings (Admin only)
    path("settings/", views.settings_list, name="settings_list"),
    
    # Approvals
    path("approvals/", views.approvals_list, name="approvals_list"),
    path("api/approvals/update/", views.update_file_approval, name="update_file_approval"),

    path("healthz", healthz),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
