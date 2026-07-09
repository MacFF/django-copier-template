from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from {{project_slug}}.base.choice_controllers import get_choices_setting, perform_import_controller


class ChoicesAPIView(APIView):
    pagination_class = []

    def post(self, request, *args, **kwargs):
        output = {}
        extra_key = []
        CHOICES_SETTING = get_choices_setting()

        for choice_request in request.data:
            choice_model = choice_request.get('model', None)
            if not choice_model:
                return Response({'message': '`model` key is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if (choice_info := CHOICES_SETTING.get(choice_model, None)) is not None:
                choice_key = choice_request.get('key', choice_model)
                filter_key = choice_request.get('filter', {})
                extra_key = choice_request.get('extra_key', [])
                controller_setting = choice_info.get('controller', None)

                choice_type = 'model' if 'model' in choice_info else 'enum'
                controller = perform_import_controller(controller_setting, choice_model, choice_type)
                if callable(controller):
                    controller = controller(
                        key=choice_model, 
                        filter=filter_key, 
                        extra_key=extra_key, 
                        choice_info=choice_info, 
                        request=request
                    )
                    output.update({choice_key: controller.data})
                else:
                    return Response(
                        {'message': f'Invalid controller for {choice_model}.'}, 
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )          
        return Response(output, status=status.HTTP_200_OK)
