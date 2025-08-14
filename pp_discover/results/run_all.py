import os
import yaml

from consolidate_imgs import consolidate_images
from consolidate_json import consolidate_json_logs
from dedup_imgs import deduplicate_images
from calc_phashes import update_metadata
from cluster_phash_hm import cluster_images
from tally_se import identify_social_engineering_clusters
from gather_mc_oi import process_directories
from count_clicks import count_chosen_elements
from clean import clean

with open('./config.yaml', 'r') as file:
    content = os.path.expandvars(file.read())
    config = yaml.safe_load(content)

if __name__ == "__main__":
    source_dir_list = config['general']['crawler_dir_names']
    for sd in source_dir_list:
        consolidate_images(sd)
        consolidate_json_logs(sd)
        deduplicate_images(sd)
        update_metadata(sd)
        cluster_images(sd)
        identify_social_engineering_clusters(sd)
        count_chosen_elements(sd)
    clean()
        
        