from flask_restx import Resource, Namespace

from ccdh.apis.harmonization.schemas import DataElementSchema, MappingSetSchema
from ccdh.config import neo4j_graph
from ccdh.mdr.mdr_graph import MdrGraph

ns = Namespace('harmonization', description='CCDH Value Harmonization')
mdr_graph = MdrGraph(neo4j_graph())

data_element_schema = DataElementSchema()
data_elements_schema = DataElementSchema(many=True)
mapping_set_schema = MappingSetSchema()


@ns.route('/data-elements/<context>/<entity>/<attribute>')
@ns.response(404, 'Data Element not found')
@ns.param('context', 'The context of the data element')
@ns.param('entity', 'The entity that the data element is defined in')
@ns.param('attribute', 'The entity attribute name of the data element')
class DataElement(Resource):
    @ns.doc('get_data_element')
    def get(self, context, entity, attribute):
        return data_element_schema.dump(mdr_graph.find_data_element(context, entity, attribute))


@ns.route('/data-elements/<context>/<entity>')
@ns.response(404, 'Data Elements not found')
@ns.param('context', 'The context of the data element')
@ns.param('entity', 'The entity that the data element is defined in')
class DataElementList(Resource):
    @ns.doc('get_data_element_list')
    def get(self, context, entity):
        return data_elements_schema.dump(mdr_graph.find_data_elements(context, entity))


@ns.route('/mapping/data-element/<context>/<entity>/<attribute>')
@ns.response(404, 'Mapping not found for data element')
@ns.param('context', 'The context of the data element')
@ns.param('entity', 'The entity that the data element is defined in')
@ns.param('attribute', 'The entity attribute name of the data element')
class DataElementMapping(Resource):
    @ns.doc('get_mapping_data_element')
    @ns.produces(['application/json', 'text/tab-separated-values+sssom'])
    def get(self, context, entity, attribute):
        return mapping_set_schema.dump(mdr_graph.find_permissible_value_mappings(context, entity, attribute))


@ns.route('/mapping/data-element/<context>/<entity>')
@ns.response(404, 'Mapping not found for data element')
@ns.param('context', 'The context of the data element')
@ns.param('entity', 'The entity that the data element is defined in')
class EntityMapping(Resource):
    @ns.doc('get_mapping_data_element')
    @ns.produces(['application/json', 'text/tab-separated-values+sssom'])
    def get(self, context, entity):
        return mapping_set_schema.dump(mdr_graph.find_permissible_value_mappings(context, entity, None, pagination=False))


@ns.route('/mapping/data-element/<context>')
@ns.response(404, 'Mapping not found for data element')
@ns.param('context', 'The context of the data element')
class ContextMapping(Resource):
    @ns.doc('get_mapping_data_element')
    @ns.produces(['application/json', 'text/tab-separated-values+sssom'])
    def get(self, context):
        return mapping_set_schema.dump(mdr_graph.find_permissible_value_mappings(context, None, None, pagination=False))
