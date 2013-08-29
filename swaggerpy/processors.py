#
# Copyright (c) 2013, Digium, Inc.
#

"""Swagger processors enrich the Swagger data model to make templating easier.
"""


class ParsingContext(object):
    """Context information for parsing.

    This object is immutable. To change contexts (like adding an item to the
    stack), use the next() and next_stack() functions to build a new one.
    """

    def __init__(self):
        self.type_stack = []
        self.id_stack = []
        self.args = {'context': self}

    def __repr__(self):
        zipped = zip(self.type_stack, self.id_stack)
        strs = ["%s=%s" % (t, i) for (t, i) in zipped]
        return "ParsingContext(stack=%r)" % strs

    def is_empty(self):
        return not self.type_stack and not self.id_stack

    def push(self, obj_type, json, id_field):
        """Pushes a new self-identifying object into the context.

        @type obj_type: str
        @param obj_type: Specifies type of object json represents
        @type json: Jsonified
        @param json: Current Jsonified object.
        @type id_field: str
        @param id_field: Field name in json that identifies it.
        """
        if id_field not in json.get_field_names():
            raise SwaggerError("Missing id_field: %s" % id_field, self)
        self.push_str(obj_type, json, str(json[id_field]))

    def push_str(self, obj_type, json, id_string):
        """Pushes a new object into the context.

        @type obj_type: str
        @param obj_type: Specifies type of object json represents
        @type json: Jsonified
        @param json: Current Jsonified object.
        @type id_string: str
        @param id_string: Identifier of the given json.
        """
        self.type_stack.append(obj_type)
        self.id_stack.append(id_string)
        self.args[obj_type] = json

    def pop(self):
        """Pops the most recent object out of the context
        """
        del self.args[self.type_stack.pop()]
        self.id_stack.pop()


class SwaggerError(Exception):
    """Raised when an error is encountered mapping the JSON objects into the
    model.
    """

    def __init__(self, msg, context, cause=None):
        """Ctor.

        @param msg: String message for the error.
        @param context: ParsingContext object
        @param cause: Optional exception that caused this one.
        """
        super(Exception, self).__init__(msg, context, cause)


class SwaggerProcessor(object):
    """Post processing interface for Swagger API's.

    This processor can add fields to model objects for additional
    information to use in the templates.
    """

    def apply(self, resources):
        context = ParsingContext()
        resources_url = resources['url'] or 'json:resource_listing'
        context.push_str('resources', resources, resources_url)
        self.process_resource_listing(**context.args)
        for api in resources.apis:
            context.push('listing_api', api, 'path')
            self.process_resource_listing_api(**context.args)
            context.pop()

            api_url = api['url'] or 'json:api_declaration'
            context.push_str('api_declaration', api.api_declaration, api_url)
            self.process_api_declaration(**context.args)
            for resource_api in api.api_declaration.apis:
                context.push('resource_api', resource_api, 'path')
                self.process_resource_api(**context.args)
                for operation in resource_api.operations:
                    context.push('operation', operation, 'nickname')
                    self.process_operation(**context.args)
                    for parameter in operation.parameters:
                        context.push('parameter', parameter, 'name')
                        self.process_parameter(**context.args)
                        context.pop()
                    for response in operation.error_responses:
                        context.push('error_response', response, 'code')
                        self.process_error_response(**context.args)
                        context.pop()
                    context.pop()
                context.pop()
            for model in api.api_declaration.models:
                context.push('model', model, 'id')
                self.process_model(**context.args)
                for prop in model.properties:
                    context.push('prop', prop, 'name')
                    self.process_property(**context.args)
                    context.pop()
                context.pop()
            context.pop()
        context.pop()
        assert context.is_empty(), "Expected %r to be empty" % context

    def process_resource_listing(self, resources, context):
        """Post process a resources.json object.

        @param resources: ResourceApi object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_resource_listing_api(self, resources, listing_api, context):
        """Post process entries in a resource.json's api array.

        @param resources: Resource listing object
        @param listing_api: ResourceApi object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_api_declaration(self, resources, api_declaration, context):
        """Post process a resource object.

        This is parsed from a .json file reference by a resource listing's
        'api' array.

        @param api_declaration: resource object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_resource_api(self, resources, api_declaration, api, context):
        """Post process entries in a resource's api array

        @param api: API object
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_operation(self, resources, resource, api, operation, context):
        """Post process an operation on an api.

        @param operation: Operation object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_parameter(self, resources, resource, api, operation, parameter,
                          context):
        """Post process a parameter on an operation.

        @param parameter: Parameter object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_error_response(self, resources, resource, api, operation,
                               error_response, context):
        """Post process an errorResponse on an operation.

        @param error_response: Response object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_model(self, resources, api_declaration, model, context):
        """Post process a model from a resources model dictionary.

        @param model: Model object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_property(self, resources, api_declaration, model, prop,
                         context):
        """Post process a property from a model.

        @param prop: Property object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass

    def process_type(self, swagger_type, context):
        """Post process a type.

        @param swagger_type: ResourceListing object.
        @type context: ParsingContext
        @param context: Current context in the API.
        """
        pass


class WebsocketProcessor(SwaggerProcessor):
    """Process the WebSocket extension for Swagger
    """

    def process_resource_api(self, resources, api_declaration, api, context):
        is_websocket = lambda op: op.is_websocket
        api.has_websocket = filter(is_websocket, api.operations) != []

    def process_operation(self, resources, resource, api, operation, context):
        operation.is_websocket = operation['upgrade'] == 'websocket'

        if operation.is_websocket:
            if operation.httpMethod != 'GET':
                raise SwaggerError(
                    "upgrade: websocket is only valid on GET operations",
                    context)
