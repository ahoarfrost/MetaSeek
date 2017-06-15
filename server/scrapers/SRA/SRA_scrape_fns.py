import urllib
from lxml import etree
import json

def get_retstart_list(url):
    #define retstarts need for get_uid_list eutilities requests - since can only get 100,000 at a time, need to make multiple queries to get total list
    #find out count of UIDs going to pull from SRA
    g = urllib.urlopen(url)
    count_tree = etree.parse(g)
    g.close()
    count_xml = count_tree.getroot()
    num_uids = count_xml.findtext("Count")
    print 'number of publicly available UIDs in SRA: %s' % num_uids
    num_queries = 1+int(num_uids)/100000  #number of queries to do, with shifting retstart
    retstart_list = [i*100000 for i in range(num_queries)]
    print 'retstarts to use: %s' % retstart_list
    return retstart_list

def get_uid_list(ret_list):
    #scrape UIDs into list
    uid_list = []
    for retstart in ret_list:
        f = urllib.urlopen('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=sra&term=public&field=ACS&tool=metaseq&email=metaseekcloud%40gmail.com&retmax=100000&retstart='+str(retstart))
        uid_tree = etree.parse(f)
        f.close()
        uid_xml = uid_tree.getroot()
        print "appending %s accessions" % len(uid_xml.find("IdList").findall("Id"))
        #add uids to list of accessions
        for id in uid_xml.find("IdList").iterchildren():
            value = id.text
            uid_list.append(value)
    return uid_list

def get_batches(uid_list):
    starts = range(0,len(uid_list),500)
    ends = range(500,len(uid_list),500)
    ends.append(len(uid_list))
    batches = [list(a) for a in zip(starts, ends)]
    return batches


def get_srx_metadata(batch_uid_list):
    print "Querying API and parsing XML..."
    s_parse_time = datetime.now()
    srx_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&tool=metaseq&email=metaseekcloud%40gmail.com'
    for key in batch_uid_list:
        #this makes url with end &id=###&id=###&id=### - returns a set of links in order of sra uids
        srx_url = srx_url+'&id='+str(key)
    #srx_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=sra&tool=metaseq&email=metaseekcloud%40gmail.com&id='+str(batch_uid_list)[1:-1]
    s = urllib.urlopen(srx_url)
    sra_tree = etree.parse(s)
    s.close()
    sra_xml = sra_tree.getroot()
    print "...parsing done for %s srxs in %s" % (len(batch_uid_list),(datetime.now()-s_parse_time))

    sra_samples = sra_xml.findall("EXPERIMENT_PACKAGE")
    sdict = {}

    #if the length of sra_samples != length of batch_uid_list, then one or more of the uids did not return an efetch (maybe it's not public even though it shows up in esearch); if this is the case, raise EfetchError
    if len(sra_samples)!=len(batch_uid_list):
        raise EfetchError('length srx batch does not equal length returned efetches! skipping this batch')

    for which,sra_sample in enumerate(sra_samples): #the order of experiment_packages ARE in order of sra ids given - that's good
        srx_dict = {}
        srx_uid = str(batch_uid_list[which])
        print "--scraping srx metadata for sample uid %s, %s out of %s" % (srx_uid, which+1,len(sra_samples))

        srx_dict['db_source_uid'] = srx_uid
        srx_dict['db_source'] = 'SRA'
        srx_dict['expt_link'] = "https://www.ncbi.nlm.nih.gov/sra/"+str(srx_uid)

        #There are 7 top tag groups. Have to scrape data a little different for each: ['EXPERIMENT','SUBMISSION','Organization','STUDY','SAMPLE','Pool','RUN_SET']

        ###EXPERIMENT -
        if sra_sample.find("EXPERIMENT").find("IDENTIFIERS").findtext("PRIMARY_ID") is not None:
            srx_dict['expt_id'] = sra_sample.find("EXPERIMENT").find("IDENTIFIERS").findtext("PRIMARY_ID")
        if sra_sample.find("EXPERIMENT").findtext("TITLE") is not None:
            srx_dict['expt_title'] = sra_sample.find("EXPERIMENT").findtext("TITLE")
        if sra_sample.find("EXPERIMENT").find("STUDY_REF").find("IDENTIFIERS") is not None:
            if sra_sample.find("EXPERIMENT").find("STUDY_REF").find("IDENTIFIERS").findtext("PRIMARY_ID") is not None:
                srx_dict["study_id"] = sra_sample.find("EXPERIMENT").find("STUDY_REF").find("IDENTIFIERS").findtext("PRIMARY_ID")
        if sra_sample.find("EXPERIMENT").find("DESIGN").findtext("DESIGN_DESCRIPTION") is not None:
            srx_dict['expt_design_description'] = sra_sample.find("EXPERIMENT").find("DESIGN").findtext("DESIGN_DESCRIPTION")
        try:
            srx_dict['sample_id'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("SAMPLE_DESCRIPTOR").get("accession")
        except AttributeError:
            pass
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_NAME") is not None:
            srx_dict['library_name'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_NAME")
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_STRATEGY") is not None:
            srx_dict['library_strategy'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_STRATEGY")
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_SOURCE").lower() is not None:
            srx_dict['library_source'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_SOURCE").lower()
        ###change library_selection to MIxS field library_screening_strategy (cv for SRA, not for MIxS)
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_SELECTION") is not None:
            srx_dict['library_screening_strategy'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_SELECTION")
        ###change library_layout to MIxS field library_construction_method - cv single | paired
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_LAYOUT") is not None:
            srx_dict['library_construction_method'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").find("LIBRARY_LAYOUT").getchildren()[0].tag.lower()
        if sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_CONSTRUCTION_PROTOCOL") is not None:
            srx_dict['library_construction_protocol'] = sra_sample.find("EXPERIMENT").find("DESIGN").find("LIBRARY_DESCRIPTOR").findtext("LIBRARY_CONSTRUCTION_PROTOCOL")
        ###change platform to MIxS field sequencing_method - cv in SRA (not in MIxS)
        if sra_sample.find("EXPERIMENT").find("PLATFORM").getchildren() is not None:
            if len(testxml.find("EXPERIMENT_PACKAGE").find("EXPERIMENT").find("PLATFORM").getchildren())>1:
                #find the one that's actually a tag
                for platform in testxml.find("EXPERIMENT_PACKAGE").find("EXPERIMENT").find("PLATFORM").getchildren():
                    if type(platform.tag) is str:
                        srx_dict['sequencing_method'] = platform.tag.lower()
            else:
                srx_dict['sequencing_method'] = sra_sample.find("EXPERIMENT").find("PLATFORM").getchildren()[0].tag.lower()
            if sra_sample.find("EXPERIMENT").find("PLATFORM").getchildren()[0].findtext("INSTRUMENT_MODEL") is not None:
                srx_dict['instrument_model'] = sra_sample.find("EXPERIMENT").find("PLATFORM").getchildren()[0].findtext("INSTRUMENT_MODEL")

        ###SUBMISSION - just need the submission id
        if sra_sample.find("SUBMISSION").find("IDENTIFIERS").findtext("PRIMARY_ID") is not None:
            srx_dict['submission_id'] = sra_sample.find("SUBMISSION").find("IDENTIFIERS").findtext("PRIMARY_ID")

        ###Organization - name, address, and contact
        if sra_sample.find("Organization") is not None:
            try:
                if sra_sample.find("Organization").findtext("Name") is not None:
                    srx_dict['organization_name'] = sra_sample.find("Organization").findtext("Name")
            except AttributeError:
                pass
            try:
                if sra_sample.find("Organization").find("Address") is not None:
                    address = ''
                    for line in sra_sample.find("Organization").find("Address").iterchildren():
                        address = address+line.text+', '
                    address = address[:-2]
                    srx_dict['organization_address'] = address
            except AttributeError:
                pass
            try:
                if len(sra_sample.find("Organization").findall("Contact"))>0:
                    contacts = []
                    for contact in sra_sample.find("Organization").findall("Contact"):
                        try:
                            name = contact.find("Name").find("First").text+' '+contact.find("Name").find("Last").text
                        except AttributeError:
                            name=''
                        email = contact.get('email')
                        contacts.append(name+', '+email)
                    srx_dict['organization_contacts'] = contacts
            except AttributeError:
                pass

        ###STUDY -
        if sra_sample.find("STUDY").find("IDENTIFIERS").findtext("PRIMARY_ID") is not None:
            srx_dict['study_id'] = sra_sample.find("STUDY").find("IDENTIFIERS").findtext("PRIMARY_ID")
        if len(sra_sample.find("STUDY").find("IDENTIFIERS").findall("EXTERNAL_ID"))>0:
            for external in sra_sample.find("STUDY").find("IDENTIFIERS").iterchildren("EXTERNAL_ID"):
                if external.get("namespace")=='BioProject':
                    srx_dict['bioproject_id'] = external.text
        if sra_sample.find("STUDY").find("DESCRIPTOR").findtext("STUDY_TITLE") is not None:
            srx_dict['study_title'] = sra_sample.find("STUDY").find("DESCRIPTOR").findtext("STUDY_TITLE")
        ###rename existing_study_type to study_type
        if sra_sample.find("STUDY").find("DESCRIPTOR").find("STUDY_TYPE") is not None:
            if sra_sample.find("STUDY").find("DESCRIPTOR").find("STUDY_TYPE").get("existing_study_type")=="Other":
                srx_dict['study_type'] = 'Other'
                if sra_sample.find("STUDY").find("DESCRIPTOR").find("STUDY_TYPE").get("add_study_type") is not None:
                    srx_dict['study_type_other'] = sra_sample.find("STUDY").find("DESCRIPTOR").find("STUDY_TYPE").get("add_study_type")
            else:
                srx_dict['study_type'] = sra_sample.find("STUDY").find("DESCRIPTOR").find("STUDY_TYPE").get("existing_study_type")
        if sra_sample.find("STUDY").find("DESCRIPTOR").findtext("STUDY_ABSTRACT"):
            srx_dict['study_abstract'] = sra_sample.find("STUDY").find("DESCRIPTOR").findtext("STUDY_ABSTRACT")
        if sra_sample.find("STUDY").find("STUDY_LINKS") is not None:
            study_links = {}
            for study_link in sra_sample.find("STUDY").find("STUDY_LINKS").iterchildren():
                if study_link.find("XREF_LINK") is not None:
                    study_links[study_link.find("XREF_LINK").findtext("DB")] = study_link.find("XREF_LINK").findtext("ID")
                if study_link.find("URL_LINK") is not None:
                    study_links[study_link.find("URL_LINK").findtext("LABEL")] = study_link.find("URL_LINK").findtext("URL")
            srx_dict['study_links'] = study_links
        if sra_sample.find("STUDY").find("STUDY_ATTRIBUTES") is not None:
            study_attributes = {}
            for attr in sra_sample.find("STUDY").find("STUDY_ATTRIBUTES").iterchildren():
                study_attributes[attr.findtext("TAG")] = attr.findtext("VALUE")
            srx_dict['study_attributes'] = study_attributes

        ###SAMPLE - get some BioSample stuff that's in easier format here: sample id, biosample id (if exists; it should but sometimes doesn't); also title, sample name stuff, and description; rest get from biosample scraping
        try:
            if sra_sample.find("SAMPLE").find("IDENTIFIERS").findtext("PRIMARY_ID") is not None:
                srx_dict['sample_id'] = sra_sample.find("SAMPLE").find("IDENTIFIERS").findtext("PRIMARY_ID")
            if len(sra_sample.find("SAMPLE").find("IDENTIFIERS").findall("EXTERNAL_ID"))>0:
                for external in sra_sample.find("SAMPLE").find("IDENTIFIERS").iterchildren("EXTERNAL_ID"):
                    if external.get("namespace")=='BioSample':
                        srx_dict['biosample_id'] = external.text
            if sra_sample.find("SAMPLE").findtext("TITLE") is not None:
                srx_dict['sample_title'] = sra_sample.find("SAMPLE").findtext("TITLE")
            if sra_sample.find("SAMPLE").find("SAMPLE_NAME") is not None:
                if sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("TAXON_ID") is not None:
                    srx_dict['host_taxon_id'] = sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("TAXON_ID")
                if sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("SCIENTIFIC_NAME") is not None:
                    srx_dict['taxon_scientific_name'] = sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("SCIENTIFIC_NAME")
                if sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("COMMON_NAME") is not None:
                    srx_dict['taxon_common_name'] = sra_sample.find("SAMPLE").find("SAMPLE_NAME").findtext("COMMON_NAME")
            if sra_sample.find("SAMPLE").findtext("DESCRIPTION") is not None:
                srx_dict['sample_description'] = sra_sample.find("SAMPLE").findtext("DESCRIPTION")
        except AttributeError:
            print "Sample scraping didn't work for srx uid %s, skipping" % (srx_uid)
            pass


        ###Pool - skip, redundant

        ###RUN_SET - record stats for each run as list, for best run (maxrun, run for which total_num_reads is largest) as single value
        run_ids = []
        total_num_reads = []
        total_num_bases = []
        download_size = []
        avg_read_length = []
        baseA_count = []
        baseC_count = []
        baseG_count = []
        baseT_count = []
        baseN_count = []
        gc_percent = []
        read_quality_counts = []

        if len(sra_sample.find("RUN_SET").findall("RUN"))>0:
            srx_dict['num_runs_in_accession'] = len(sra_sample.find("RUN_SET").findall("RUN"))
            for run in sra_sample.find("RUN_SET").findall("RUN"):
                run_ids.append(run.get("accession"))
                total_num_reads.append(int(run.get("total_spots")) if run.get("total_spots") is str else None)
                total_num_bases.append(int(run.get("total_bases")) if run.get("total_bases") is str else None)
                download_size.append(int(run.get("size")) if run.get("size") is str else None)
                if run.find("Bases") is not None:
                    for base in run.find("Bases").findall("Base"):
                        if base.get("value")=="A":
                            baseA_count.append(int(base.get("count")))
                            countA = int(base.get("count"))
                        if base.get("value")=="C":
                            baseC_count.append(int(base.get("count")))
                            countC = int(base.get("count"))
                        if base.get("value")=="G":
                            baseG_count.append(int(base.get("count")))
                            countG = int(base.get("count"))
                        if base.get("value")=="T":
                            baseT_count.append(int(base.get("count")))
                            countT = int(base.get("count"))
                        if base.get("value")=="N":
                            baseN_count.append(int(base.get("count")))
                            countN = int(base.get("count"))
                    gc_percent.append(float(countG+countC)/float(countC+countG+countA+countT))
                if run.find("Run") is not None:
                    try:
                        avg_read_length.append(float(run.get("total_bases"))/(float(run.find("Run").get("spot_count"))+float(run.find("Run").get("spot_count_mates"))))
                    except TypeError:
                        avg_read_length.append(None)
                    qual_count = {}
                    if run.find("Run").find("QualityCount") is not None:
                        for qual in run.find("Run").find("QualityCount").findall("Quality"):
                            qual_count[qual.get("value")] = int(qual.get("count"))
                    read_quality_counts.append(qual_count)


            max_index = total_num_reads.index(max(total_num_reads))

            srx_dict['run_ids'] = run_ids
            if max_index<=(len(run_ids)-1):
                srx_dict['run_ids_maxrun'] = run_ids[max_index]
            srx_dict['total_num_reads'] = total_num_reads
            if max_index<=(len(total_num_reads)-1):
                srx_dict['total_num_reads_maxrun'] = total_num_reads[max_index]
            srx_dict['total_num_bases'] = total_num_bases
            if max_index<=(len(total_num_bases)-1):
                srx_dict['total_num_bases_maxrun'] = total_num_bases[max_index]
            srx_dict['download_size'] = download_size
            if max_index<=(len(download_size)-1):
                srx_dict['download_size_maxrun'] = download_size[max_index]
            srx_dict['avg_read_length'] = avg_read_length
            if max_index<=(len(avg_read_length)-1):
                srx_dict['avg_read_length_maxrun'] = avg_read_length[max_index]
            srx_dict['baseA_count'] = baseA_count
            if max_index<=(len(baseA_count)-1):
                srx_dict['baseA_count_maxrun'] = baseA_count[max_index]
            srx_dict['baseC_count'] = baseC_count
            if max_index<=(len(baseC_count)-1):
                srx_dict['baseC_count_maxrun'] = baseC_count[max_index]
            srx_dict['baseG_count'] = baseG_count
            if max_index<=(len(baseG_count)-1):
                srx_dict['baseG_count_maxrun'] = baseG_count[max_index]
            srx_dict['baseT_count'] = baseT_count
            if max_index<=(len(baseT_count)-1):
                srx_dict['baseT_count_maxrun'] = baseT_count[max_index]
            srx_dict['baseN_count'] = baseN_count
            if max_index<=(len(baseN_count)-1):
                srx_dict['baseN_count_maxrun'] = baseN_count[max_index]
            srx_dict['gc_percent'] = gc_percent
            if max_index<=(len(gc_percent)-1):
                srx_dict['gc_percent_maxrun'] = gc_percent[max_index]
            srx_dict['read_quality_counts'] = read_quality_counts
            if max_index<=(len(read_quality_counts)-1):
                srx_dict['read_quality_counts_maxrun'] = read_quality_counts[max_index]


        sdict[srx_uid] = srx_dict

    return sdict


#takes list of SRX UIDs to query (batch_uid_list), and sdict into which to insert link uids;
#return sdict with 'biosample_uid', 'pubmed_uids', and/or 'nuccore_uids' inserted; and link dict with lists of biosample_uids, pubmed_uids, and nuccore_uids to scrape
def get_links(batch_uid_list, sdict):
    print "sending elink request and parsing XML..."
    e_parse_time = datetime.now()
    elink_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=sra&db=biosample,pubmed,nuccore&tool=metaseq&email=metaseekcloud%40gmail.com'
    for key in batch_uid_list:
        #this makes url with end &id=###&id=###&id=### - returns a set of links in order of sra uids
        elink_url = elink_url+'&id='+str(key)
    #run api request and parse xml
    e = urllib.urlopen(elink_url)
    link_tree = etree.parse(e)
    e.close()
    link_xml = link_tree.getroot()
    print "...parsing done in %s" % (datetime.now()-e_parse_time)

    print "finding links..."
    #scrape elink info
    #note if there's no biosample link, <LinkSetDb> with <DbTo>=='biosample' just won't exist
    biosample_uids = []
    pubmed_uids = []
    nuccore_uids = []

    linksets = link_xml.findall("LinkSet")
    for linkset in linksets:
        srx_uid = linkset.find("IdList").findtext("Id")
        #links from each target db will be in a tab called "LinkSetDb"
        if len(linkset.findall("LinkSetDb"))>0:
            for link in linkset.findall("LinkSetDb"):
                id_set = []
                if link.findtext("DbTo")=='biosample':
                    #for all Links, get Ids
                    for uid in link.findall("Link"):
                        id_set.append(int(uid.findtext("Id")))
                    biosample_uids.extend(id_set)
                    sdict[srx_uid]['biosample_uid'] = id_set
                elif link.findtext("DbTo")=='pubmed':
                    for uid in link.findall("Link"):
                        id_set.append(int(uid.findtext("Id")))
                    pubmed_uids.extend(id_set)
                    sdict[srx_uid]['pubmed_uids'] = id_set
                elif link.findtext("DbTo")=='nuccore':
                    for uid in link.findall("Link"):
                        id_set.append(int(uid.findtext("Id")))
                    nuccore_uids.extend(id_set)
                    sdict[srx_uid]['nuccore_uids'] = id_set

    biosample_uids = list(set(biosample_uids))
    pubmed_uids = list(set(pubmed_uids))
    nuccore_uids = list(set(nuccore_uids))

    linkdict = {'biosample_uids':biosample_uids,'pubmed_uids':pubmed_uids,'nuccore_uids':nuccore_uids}
    print "number of biosamples to scrape: %s" % len(linkdict['biosample_uids'])
    print "number of pubmeds to scrape: %s" % len(linkdict['pubmed_uids'])
    print "number of nuccores to scrape: %s" % len(linkdict['nuccore_uids'])

    return sdict,linkdict

def extract_and_merge_mixs_fields(source_dict, parent_dict, rules_json):
    #source_dict e.g. bdict[bio_dict]['sample_attributes']; parent_dict e.g. bio_dict
    #read in rules from json
    with open('rules.json') as json_rules:
        rules = json.load(json_rules)
        json_rules.close()

    for rule_set in rules.keys():
        #find which redundant fields in rule set exist in sample_attributes
        matches = [x for x in rules[rule_set] if x in source_dict.keys()]
        if len(matches)>0:
            #pick replacement as lowest index (highest priority) field ##**MAKE SURE YOU ENTER YOUR RULE SET LIST IN ORDER OF PRIORITY IN THE JSON FILE**##
            replacement = rules[rule_set][min([rules[rule_set].index(j) for j in matches])]

            #add column (key:value field) to bio_dict with appropriate MIxS key field
            parent_dict[rule_set] = source_dict[replacement]

            #not going to remove the replacement field in the dict, for e.g. where units are in the old field name ('age_in_years'); you'll be able to see it in the sample_attributes of the dataset details
            #del source_dict[replacement]

            #choosing to leave any additional lower-priority matches in sample_attributes
            ##TODO: ERROR FLAG IF THERE ARE >1 MATCHES?

    return parent_dict


def get_biosample_metadata(batch_uid_list,bdict):
    #some stuff already captured with SRA - just get publication_date, Models, Package, and Attributes
    #and links?
    print "Querying API and parsing XML..."
    b_parse_time = datetime.now()
    biosample_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=biosample&tool=metaseq&email=metaseekcloud%40gmail.com&id='+str(batch_uid_list)[1:-1]
    b = urllib.urlopen(biosample_url)
    bio_tree = etree.parse(b)
    b.close()
    bio_xml = bio_tree.getroot()
    print "...parsing done for %s biosamples in %s" % (len(batch_uid_list),(datetime.now()-b_parse_time))

    biosamples = bio_xml.findall("BioSample")

    for which,biosample in enumerate(biosamples):
        print "--scraping biosample metadata for sample %s out of %s" % (which+1,len(biosamples))
        bio_dict = {}

        bio_id = biosample.get("id")
        bio_dict['biosample_uid'] = bio_id
        bio_dict['biosample_link'] = "https://www.ncbi.nlm.nih.gov/biosample/"+str(bio_id)
        #publication date
        if biosample.get('publication_date') is not None:
            bio_dict['metadata_publication_date'] = datetime.strptime(biosample.get('publication_date'), '%Y-%m-%dT%H:%M:%S.%f')
        #if Package exists, probably don't need Models (but get them anyway); from package/models will parse investigation_type and env_package
        if biosample.findtext("Package") is not None:
            bio_dict['biosample_package'] = biosample.findtext("Package")
        if biosample.find("Models") is not None:
            models = []
            for model in biosample.find("Models").findall("Model"):
                models.append(model.text)
            bio_dict['biosample_models'] = models

        #Attributes - loop through attributes; save all as dict in single column (parse later)
        if biosample.find("Attributes") is not None:
            attr = {}
            for attribute in biosample.find("Attributes").findall("Attribute"):
                attr_value = attribute.text
                if attr_value=="missing" or attr_value=="Missing" or attr_value=="not applicable" or attr_value=="Not Applicable" or attr_value=="N/A": #if value is any of several None standins, change to None
                    attr_value = None
                if attribute.get("harmonized_name") is not None:
                    attr[attribute.get("harmonized_name")] = attr_value
                elif attribute.get("attribute_name") is not None:
                    attr[attribute.get("attribute_name")] = attr_value
            bio_dict['sample_attributes'] = attr

        #extract MIxS sample attributes from the 'sample_attributes' dict field and add as own field in bio_dict, where applicable
        bio_dict = extract_and_merge_mixs_fields(source_dict=bio_dict['sample_attributes'], parent_dict=bio_dict, rules_json="rules.json")

        ##TODO: parse investigation_type and env_package from 'biosample_models' and 'biosample_package' fields, if they exist (and check against sample attribute if extracted)

        bdict[bio_id] = bio_dict

    return bdict



def get_pubmed_metadata(batch_uid_list,pdict):
    #some stuff already captured with SRA - just get publication_date, Models, Package, and Attributes
    #and links?
    print "Querying API and parsing XML..."
    p_parse_time = datetime.now()
    pub_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&tool=metaseq&email=metaseekcloud%40gmail.com&id='+str(pubmed_batch_uids)[1:-1]
    p = urllib.urlopen(pub_url)
    pub_tree = etree.parse(p)
    p.close()
    pub_xml = pub_tree.getroot()
    print "...parsing done for %s pubmeds in %s" % (len(pubmed_batch_uids),(datetime.now()-p_parse_time))

    pubmeds = pub_xml.findall("DocSum")

    for which,pubmed in enumerate(pubmeds):
        pub_dict = {}
        pub_id = pubmed.findtext("Id") #str(batch_uid_list[which])
        print "--scraping pubmed metadata for sample %s,  %s out of %s" % (pub_id, which+1,len(pubmeds))

        pub_dict['pubmed_uid'] = pub_id
        pub_dict['pubmed_link'] = "https://www.ncbi.nlm.nih.gov/pubmed/"+str(pub_id)

        if pubmed.find("Item[@Name='PubDate']").text is not None:
            try:
                pub_dict['pub_publication_date'] = datetime.strptime(pubmed.find("Item[@Name='PubDate']").text,"%Y %b %d")
            except ValueError:
                try:
                    pub_dict['pub_publication_date'] = datetime.strptime(pubmed.find("Item[@Name='PubDate']").text,"%Y %b")
                except ValueError:
                    pass

        if pubmed.find("Item[@Name='AuthorList']") is not None:
            authors = []
            for author in pubmed.find("Item[@Name='AuthorList']").findall("Item[@Name='Author']"):
                authors.append(author.text)
            pub_dict['pub_authors'] = authors

        if pubmed.findtext("Item[@Name='Title']") is not None:
            pub_dict['pub_title'] = pubmed.findtext("Item[@Name='Title']")
        if pubmed.findtext("Item[@Name='Volume']") is not None:
            pub_dict['pub_volume'] = pubmed.findtext("Item[@Name='Volume']")
        if pubmed.findtext("Item[@Name='Issue']") is not None:
            pub_dict['pub_issue'] = pubmed.findtext("Item[@Name='Issue']")
        if pubmed.findtext("Item[@Name='Pages']") is not None:
            pub_dict['pub_pages'] = pubmed.findtext("Item[@Name='Pages']")
        if pubmed.findtext("Item[@Name='Source']") is not None:
            pub_dict['pub_journal'] = pubmed.findtext("Item[@Name='Source']")
        if pubmed.findtext("Item[@Name='DOI']") is not None:
            pub_dict['pub_doi'] = pubmed.findtext("Item[@Name='DOI']")

        pdict[pub_id] = pub_dict

    return pdict


def get_nuccore_metadata(batch_uid_list,ndict):
    for which,nuccore in enumerate(batch_uid_list):
        print "--scraping nuccore metadata for sample %s out of %s" % (which+1,len(batch_uid_list))
        nuc_dict = {}

        nuc_id = str(nuccore)
        nuc_dict['nuccore_uid'] = nuc_id
        nuc_dict['nuccore_link'] = 'https://www.ncbi.nlm.nih.gov/nuccore/'+nuc_id

        ndict[nuc_id] = nuc_dict

    return ndict


def merge_scrapes(sdict,bdict,pdict,ndict,rules_json):
    #read in rules_json
    with open(rules_json) as json_rules:
        rules = json.load(json_rules)
        json_rules.close()

    for srx in sdict.keys():
        if 'biosample_uid' in sdict[srx].keys():
            #add biosample metadata fields and values to sdict[srx]

            ##TODO: log an error if len(sdict[srx]['biosample_uid'])>1; otherwise, merge biosample scrapes
            if len(sdict[srx]['biosample_uid'])==1:
                #for bio in sdict[srx]['biosample_uid']:
                    #bio = str(bio)
                    #TAB EVERYTHING OUT ONE, use if else list append approach like below:
                    #if 'biosample_link' in bdict[bio].keys():
                    #    if 'biosample_link' in sdict[srx].keys(): #biosample_link
                    #        sdict[srx]['biosample_link'].append(bdict[bio]['biosample_link'])
                    #    else:
                    #        sdict[srx]['biosample_link'] = [bdict[bio]['biosample_link']]

                bio = str(sdict[srx]['biosample_uid'][0])
                if bio in bdict.keys():
                    #fields from biosample scrape need to add; don't need biosample_uid since already there
                    biosample_fields = ['biosample_link','metadata_publication_date','biosample_package','biosample_models','sample_attributes']
                    for biosample_field in biosample_fields:
                        if biosample_field in bdict[bio].keys():
                            sdict[srx][biosample_field] = bdict[bio][biosample_field]

                    #for rule in rules.keys(), see if it's in bdict[bio]; if it is, add it to sdict[srx]; (for sequencing_method, check if already exists )
                    for rule_set in rules.keys():
                            #if rule_set is sequencing_method, check if sequencing_method field in sdict[srx] dict already exists; only add if it doesn't
                            if rule_set=="sequencing_method":
                                if "sequencing_method" in sdict[srx].keys():
                                    continue
                            else:
                                #add column to sdict[srx] dict with appropriate MIxS key field
                                sdict[srx][rule_set] = bdict[bio][rule_set]

        if 'pubmed_uids' in sdict[srx].keys():
            #append pubmed metadata values to list metadata values for that field in sdict[srx] (if multiple pubmeds, e.g., for each field have list value for all pubmeds, like with run stuff)
            for pub in sdict[srx]['pubmed_uids']:
                pub = str(pub)
                if pub in pdict.keys():
                    #don't need pubmed_uid since already there
                    pubmed_fields = ['pubmed_link','pub_publication_date','pub_authors','pub_title','pub_volume','pub_issue','pub_pages','pub_journal','pub_doi']
                    for pubmed_field in pubmed_fields:
                        if pubmed_field in pdict[pub].keys():
                            if pubmed_field in sdict[srx].keys(): #if field already in sdict[srx], append new value to existing list
                                sdict[srx][pubmed_field].append(pdict[pub][pubmed_field])
                            else: #otherwise add new field with list value (length of one)
                                sdict[srx][pubmed_field] = [pdict[pub][pubmed_field]]

        if 'nuccore_uids' in sdict[srx].keys():
            #append nuccore metadata values to list metadata values for that field in sdict[srx]
            for nuc in sdict[srx]['nuccore_uids']:
                nuc = str(nuc)
                if nuc in ndict.keys():
                    #don't need nuccore_uid since already there - just add nuccore_link
                    if 'nuccore_link' in ndict[nuc].keys():
                        if 'nuccore_link' in sdict[srx].keys():
                            sdict[srx]['nuccore_link'].append(ndict[nuc]['nuccore_link'])
                        else:
                            sdict[srx]['nuccore_link'] = [ndict[nuc]['nuccore_link']]
    return sdict