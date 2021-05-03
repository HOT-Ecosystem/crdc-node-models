from sssom.io import from_dataframe, Mapping as SssomMapping
import pandas as pd
from fastapi import APIRouter, File, UploadFile, Request, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict
from pydantic.main import BaseModel
from datetime import date
from prefixcommons.curie_util import contract_uri

from ccdh.api.utils import uri_to_curie
from ccdh.config import neo4j_graph
from ccdh.importers import Importer
from ccdh.db.mdr_graph import MdrGraph
from ccdh.api.namespaces import NAMESPACES

mdr_graph = MdrGraph(neo4j_graph())


class Mapping(BaseModel):
    # subject_id: Optional[str]
    subject_match_field: str
    subject_label: str
    predicate_id: Optional[str]
    object_id: Optional[str]
    object_label: Optional[str]
    object_match_field: Optional[str]
    creator_id: Optional[str]
    comment: Optional[str]
    mapping_date: Optional[date]


class MappingSet(BaseModel):
    creator_id: str
    license: str
    mapping_provider: str
    curie_map: Dict[str, str] = {
        'NCIT': 'http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl#',
    }
    mappings: List[Mapping] = []


router = APIRouter(
    prefix='/mappings',
    tags=['Mappings'],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.get('/nodes/{context}/{entity}/{attribute}', response_model=MappingSet,
            responses={
                200: {
                    "content": {
                        'text/tab-separated-values+sssom': {}
                    },
                    "description": "Return the JSON mapping set or a TSV file.",
                }
            })
async def get_data_element_mapping(context: str, entity: str, attribute: str, request: Request) -> MappingSet:
    mapping_set = mdr_graph.find_mappings_of_data_element(context, entity, attribute, pagination=False)
    mapping_set.mappings = list(map(lambda x: x.__dict__, mapping_set.mappings))
    if request.headers['accept'] == 'text/tab-separated-values+sssom':
        return StreamingResponse(generate_sssom_tsv(MappingSet.parse_obj(mapping_set.__dict__)), media_type='text/tab-separated-values+sssom')
    else:
        return mapping_set.__dict__


@router.get('/crdc-h/{context}/{object_class}/{property}', response_model=MappingSet,
            responses={
                200: {
                    "content": {
                        'text/tab-separated-values+sssom': {}
                    },
                    "description": "Return the JSON mapping set or a TSV file.",
                }
            })
async def get_data_element_concept_mapping(context: str, object_class: str, property: str, request: Request) -> MappingSet:
    mapping_set = mdr_graph.find_mappings_of_data_element_concept(context, object_class, property, pagination=False)
    mapping_set.mappings = list(map(map_mapping, mapping_set.mappings))
    if request.headers['accept'] == 'text/tab-separated-values+sssom':
        return StreamingResponse(generate_sssom_tsv(MappingSet.parse_obj(mapping_set.__dict__)), media_type='text/tab-separated-values+sssom')
    else:
        return mapping_set.__dict__


@router.post('/upload')
async def upload_mappings(file: UploadFile = File(...)):
    if file.content_type == 'text/tab-separated-values':
        df = pd.read_csv(file.file, sep='\t', comment='#').fillna('')
        msd = from_dataframe(df, NAMESPACES, {})
        Importer(neo4j_graph()).import_mapping_set(msd.mapping_set, NAMESPACES)
        return {"filename": file.filename, 'mappings': len(msd.mapping_set.mappings)}
    else:
        raise HTTPException(status_code=404, detail=f"content type not supported: {file.content_type}")


def generate_sssom_tsv(data):
    data_dict = dict(data)
    for key in data_dict:
        if key == 'mappings':
            row_num = 0
            for mapping in data_dict[key]:
                if row_num == 0:
                    yield '\t'.join(dict(mapping).keys()) + '\n'
                row_num += 1
                yield '\t'.join([str(i) if i else '' for i in dict(mapping).values()]) + '\n'
        elif key == 'curie_map':
            yield '#curie_map:\n'
            for curie, uri in data_dict[key].items():
                yield f'#  {curie}: "{uri}"\n'
        else:
            yield f'#{key}: {data_dict[key]}\n'


def map_mapping(mapping: SssomMapping) -> Dict:
    if mapping.object_id:
        mapping.object_id = uri_to_curie(mapping.object_id, NAMESPACES)
    return mapping.__dict__



