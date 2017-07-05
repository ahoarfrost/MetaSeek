from flask_restful import fields

# This marshal is used when returning brief information about a list of datasets
# in the context of a search or a summary:
# GetAllDatasets, SearchDatasets, GetDiscovery, GetAllDiscoveries,
summarizedDatasetFields = {
    # fields that are summarized in summarizeColumn
    'investigation_type':fields.String,
    'library_source':fields.String,
    'env_package':fields.String,
    'library_strategy':fields.String,
    'library_screening_strategy':fields.String,
    'library_construction_method':fields.String,
    'study_type':fields.String,
    'sequencing_method':fields.String,
    'instrument_model':fields.String,
    'geo_loc_name':fields.String,
    'env_biome':fields.String,
    'env_feature':fields.String,
    'env_material':fields.String,
    'avg_read_length_maxrun':fields.Float,
    'gc_percent_maxrun':fields.Float,
    'meta_latitude':fields.Float,
    'meta_longitude':fields.Float,
    'library_reads_sequenced_maxrun':fields.Integer,
    'total_num_bases_maxrun':fields.Integer,
    'download_size_maxrun':fields.Integer,
    # additional important dataset-specific fields
    'id':fields.Integer,
    'db_source_uid':fields.String,
    'db_source':fields.String,
    'sample_title':fields.String,
    'biosample_link':fields.String,
    'uri': fields.Url('getdataset')
}

fullDatasetFields = {
    'id':fields.Integer,
    'db_source_uid':fields.String,
    'db_source':fields.String,
    'expt_link':fields.String,
    'expt_id':fields.String,
    'expt_title':fields.String,
    'expt_design_description':fields.String,
    'library_name':fields.String,
    'library_strategy':fields.String,
    'library_source':fields.String,
    'library_screening_strategy':fields.String,
    'library_construction_method':fields.String,
    'library_construction_protocol':fields.String,
    'sequencing_method':fields.String,
    'instrument_model':fields.String,
    'submission_id':fields.String,
    'organization_name':fields.String,
    'organization_address':fields.String,
    'organization_contacts':fields.String,
    'study_id':fields.String,
    'bioproject_id':fields.String,
    'study_title':fields.String,
    'study_type':fields.String,
    'study_type_other':fields.String,
    'study_abstract':fields.String,
    'study_links':fields.String,
    'study_attributes':fields.String,
    'sample_id':fields.String,
    'biosample_id':fields.String,
    'sample_title':fields.String,
    'ncbi_taxon_id':fields.String,
    'taxon_scientific_name':fields.String,
    'taxon_common_name':fields.String,
    'sample_description':fields.String,
    'num_runs_in_accession':fields.Integer,
    'run_ids_maxrun':fields.String,
    'library_reads_sequenced_maxrun':fields.Integer,
    'total_num_bases_maxrun':fields.Integer,
    'download_size_maxrun':fields.Integer,
    'avg_read_length_maxrun':fields.Float,
    'baseA_count_maxrun':fields.Integer,
    'baseC_count_maxrun':fields.Integer,
    'baseG_count_maxrun':fields.Integer,
    'baseT_count_maxrun':fields.Integer,
    'baseN_count_maxrun':fields.Integer,
    'gc_percent_maxrun':fields.Float,
    'run_quality_counts_maxrun':fields.String,
    'biosample_uid':fields.String,
    'biosample_link':fields.String,
    'metadata_publication_date':fields.DateTime(dt_format='rfc822'),
    'biosample_package':fields.String,
    'biosample_models':fields.String,
    'sample_attributes':fields.String,
    'investigation_type':fields.String,
    'env_package':fields.String,
    'project_name':fields.String,
    'lat_lon':fields.String,
    'latitude':fields.String,
    'longitude':fields.String,
    'meta_latitude':fields.Float,
    'meta_longitude':fields.Float,
    'geo_loc_name':fields.String,
    'collection_date':fields.String,
    'collection_time':fields.String,
    'env_biome':fields.String,
    'env_feature':fields.String,
    'env_material':fields.String,
    'depth':fields.String,
    'elevation':fields.String,
    'altitude':fields.String,
    'target_gene':fields.String,
    'target_subfragment':fields.String,
    'ploidy':fields.String,
    'num_replicons':fields.String,
    'estimated_size':fields.String,
    'ref_biomaterial':fields.String,
    'propagation':fields.String,
    'assembly':fields.String,
    'finishing_strategy':fields.String,
    'isol_growth_condt':fields.String,
    'experimental_factor':fields.String,
    'specific_host':fields.String,
    'subspecific_genetic_lineage':fields.String,
    'tissue':fields.String,
    'sex':fields.String,
    'sample_type':fields.String,
    'age':fields.String,
    'dev_stage':fields.String,
    'biomaterial_provider':fields.String,
    'host_disease':fields.String,
    'date_scraped':fields.DateTime(dt_format='rfc822'),
    'uri': fields.Url('getdataset')
}
