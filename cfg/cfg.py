import yaml
import os

def cfg():
    # Construct the path to cfg.yaml relative to this file's location
    dir_path = os.path.dirname(os.path.realpath(__file__))
    cfg_path = os.path.join(dir_path, "cfg.yaml")
    
    with open(cfg_path, 'r') as stream:
        cfg = yaml.safe_load(stream)
    return cfg