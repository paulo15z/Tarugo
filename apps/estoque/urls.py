from rest_framework.routers import DefaultRouter
from .views import MaterialTypeViewSet, LocationViewSet, MDFSheetViewSet, CutOffViewSet

router = DefaultRouter()
router.register(r'material-types', MaterialTypeViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'mdf-sheets', MDFSheetViewSet)
router.register(r'cut-offs', CutOffViewSet)

urlpatterns = router.urls
