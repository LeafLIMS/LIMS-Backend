from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings

from rest_framework import routers

from lims.users.views import ObtainAuthToken, UserViewSet, GroupViewSet, PermissionViewSet

from lims.shared.views import OrganismViewSet

from lims.orders.views import OrderViewSet
from lims.addressbook.views import AddressViewSet
from lims.pricebook.views import PriceBookViewSet

from lims.inventory.views import (InventoryViewSet, 
        SetViewSet, MeasureViewSet, ItemTypeViewSet, LocationViewSet)
from lims.codonusage.views import CodonUsageTableViewSet
from lims.projects.views import (ProjectViewSet, ProductViewSet,
        DesignViewSet, ElementViewSet, ElementLabelViewSet)
from lims.workflows.views import WorkflowViewSet, ActiveWorkflowViewSet, TaskViewSet

from lims.equipment.views import EquipmentViewSet, EquipmentReservationViewSet

from lims.crm.views import CRMUserView, CRMProjectView

router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet, base_name='orders')
router.register(r'addresses', AddressViewSet, base_name='addresses')
router.register(r'pricebooks', PriceBookViewSet, base_name='pricebooks')
router.register(r'codonusage', CodonUsageTableViewSet, base_name='codonusage')

router.register(r'users', UserViewSet, base_name='users')
router.register(r'groups', GroupViewSet, base_name='groups')
router.register(r'permissions', PermissionViewSet, base_name='permissions')

router.register(r'inventory', InventoryViewSet, base_name='inventory')
router.register(r'inventorysets', SetViewSet, base_name='inventorysets')
router.register(r'organisms', OrganismViewSet, base_name='organisms')
router.register(r'measures', MeasureViewSet, base_name='measures')
router.register(r'itemtypes', ItemTypeViewSet, base_name='itemtypes')
router.register(r'locations', LocationViewSet, base_name='locations')

router.register(r'equipment', EquipmentViewSet, base_name='equipment')
router.register(r'equipmentreservation', EquipmentReservationViewSet, base_name='equipmentreservation')

router.register(r'designs', DesignViewSet, base_name='designs')
router.register(r'designelements', ElementViewSet, base_name='designelements')
router.register(r'designelementlabels', ElementLabelViewSet, base_name='designelementlabels')

router.register(r'projects', ProjectViewSet, base_name='projects')
router.register(r'products', ProductViewSet, base_name='products')
router.register(r'attachments', AttachmentViewSet, base_name='attachments')
router.register(r'workflows', WorkflowViewSet, base_name='workflows')
router.register(r'activeworkflows', ActiveWorkflowViewSet, base_name='activeworkflows')
router.register(r'workflowtasks', TaskViewSet, base_name='workflowtasks')

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^users/token/', ObtainAuthToken.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^crm/user/', CRMUserView.as_view()),
    url(r'^crm/project/', CRMProjectView.as_view()),
    url(r'^docs/', include('rest_framework_swagger.urls')),
    url(r'^', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 
