'''
Util functions for reading and extracting data and other stuff
'''
import contextlib
import logging
import os
import re
import shutil
import sys
import wave
from datetime import datetime
from pathlib import Path
import numpy as np
from mutagen.mp3 import MP3


################# Utils #################

class EasyDict(dict):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def __getattr__(self, name): return self[name]
    def __setattr__(self, name, value): self[name] = value
    def __delattr__(self, name): del self[name] 

def create_directories(config):
    model_dir = Path(config.model_dir)
    for m in config.model_types:
        model_dir.joinpath(m).mkdir(parents=True, exist_ok=True)

################# PAUSE FEATURES #################

def clean_file(lines):
    return re.sub(r'[0-9]+[_][0-9]+', '', lines.replace("*INV:", "").replace("*PAR:", "")).strip().replace("\x15", "").replace("\n", "").replace("\t", " ").replace("[+ ", "[+").replace("[* ", "[*").replace("[: ", "[:").replace(" .", "").replace("'s", "").replace(" ?", "").replace(" !", "").replace(" ]", "]").lower()

def extra_clean(lines):
    lines = clean_file(lines)
    lines = lines.replace("[+exc]", "")
    lines = lines.replace("[+gram]", "")
    lines = lines.replace("[+es]", "")
    lines = re.sub(r'[&][=]*[a-z]+', '', lines) #remove all &=text
    lines = re.sub(r'\[[*][a-z]:[a-z][-|a-z]*\]', '', lines) #remove all [*char:char(s)]
    lines = re.sub(r'[^A-Za-z0-9\s_]+', '', lines) #remove all remaining symbols except underscore
    lines = re.sub(r'[_]', ' ', lines) #replace underscore with space
    return lines

def words_count(content):
    extra_cleaned = extra_clean(content).split(" ")
    return len(extra_cleaned) - extra_cleaned.count('')

def get_pauses_cnt(content):
    content = clean_file(content)

    cnt = 0
    pauses_list = []
    pauses = re.findall(r'&[a-z]+', content) #find all utterances
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'<[a-z_\s]+>', content) #find all <text>
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'\[/+\]', content) #find all [/+]
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'\([\.]+\)', content) #find all (.*)
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'\+[\.]+', content) #find all +...
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'[m]*hm', content) #find all mhm or hm
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'\[:[a-z_\s]+\]', content) #find all [:word]
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    pauses = re.findall(r'[a-z]*\([a-z]+\)[a-z]*', content) #find all wor(d)
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    temp = re.sub(r'\[[*][a-z]:[a-z][-|a-z]*\]', '', content)
    pauses = re.findall(r'[a-z]+:[a-z]+', temp) #find all w:ord
    cnt += len(pauses)
    pauses_list.append(len(pauses))

    return np.array(pauses_list)


################# INTERVENTION FEATURES #################

def get_n_interventions(content):
    content = content.split('\n')
    speakers = []

    for c in content:
        if 'INV' in c:
          speakers.append('INV')
        if 'PAR' in c:
          speakers.append('PAR')

    PAR_first_index = speakers.index('PAR')
    PAR_last_index = len(speakers) - speakers[::-1].index('PAR') - 1 
    speakers = speakers[PAR_first_index:PAR_last_index]
    return speakers.count('INV')


################# SPECTOGRAM FEATURES #################

def read_spectogram():
    return

################# REGRESSION FEATURES #################

def get_regression_values(metadata_filename):
    values = []
    with open(metadata_filename, 'r') as f:
        content = f.readlines()[1:]
        for idx, line in enumerate(content):
            # Get the second element (index 1) which is the age
            token = line.split('; ')[1].strip('\n')
            if token!='NA':
                values.append(int(token))
            else:
                values.append(30)

    return values

def get_classification_values(metadata_filename):
    values = []
    with open(metadata_filename, 'r') as f:
        content = f.readlines()[1:]
        for idx, line in enumerate(content):
            token = line.split('; ')[-2].strip('\n')
            if token!='NA':  values.append(int(token))
            else:   values.append(30) # NA fill value

    return values

def get_audio_length(filename):
    with contextlib.closing(wave.open(filename,'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames / float(rate)
    return duration

def get_mp3_audio_length(filename):
    audio = MP3(filename)
    duration = audio.info.length
    return duration

def get_timestamped_dir(base_dir):
    """
    Append timestamp to directory path.
    Args:
        base_dir (str): Base directory path
    Returns:
        str: Directory path with timestamp
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base_dir}_{timestamp}"


def update_config_paths(config):
    """
    Update config paths with timestamps.
    Args:
        config: Configuration object
    Returns:
        config: Updated configuration object
    """
    # Update model directory
    base_model_dir = config.model_dir
    config.model_dir = get_timestamped_dir(base_model_dir)

    # Update log directories
    base_log_dir = config.log_dir
    config.log_dir = get_timestamped_dir(base_log_dir)

    # Update tensorboard log directory
    base_tensorboard_dir = config.tensorboard_log_dir
    config.tensorboard_log_dir = get_timestamped_dir(base_tensorboard_dir)

    return config


def ensure_directories_exist(config):
    """
    Ensure all directories in config exist.
    Args:
        config: Configuration object
    """
    directories = [
        config.model_dir,
        config.log_dir,
        config.tensorboard_log_dir
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def initialize_timestamped_dirs(config):
    """
    Initialize all directories with timestamps.
    Args:
        config: Configuration object
    Returns:
        config: Updated configuration object
    """
    config = update_config_paths(config)
    ensure_directories_exist(config)
    return config


def _setup_logger():
    """Setup logging configuration"""
    logger = logging.getLogger('DirectoryHandler')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class DirectoryHandler:
    """Utility class to handle directory operations safely"""

    def __init__(self):
        self.logger = _setup_logger()

    def ensure_directory(self, directory_path):
        """
        Ensure a directory exists, create if it doesn't.
        Returns the absolute path of the directory.
        """
        try:
            directory_path = os.path.abspath(directory_path)
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Ensured directory exists: {directory_path}")
            return directory_path
        except Exception as e:
            self.logger.error(f"Error creating directory {directory_path}: {str(e)}")
            raise

    def create_timestamped_directory(self, base_path, prefix=""):
        """Create a timestamped directory within the base path"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        dir_name = f"{prefix}_{timestamp}" if prefix else timestamp
        full_path = os.path.join(base_path, dir_name)
        return self.ensure_directory(full_path)

    def create_experiment_directories(self, base_experiment_dir):
        """
        Create all necessary directories for an experiment.
        Returns a dictionary of created directory paths.
        """
        dirs = {
            'base': base_experiment_dir,
            'models': os.path.join(base_experiment_dir, 'models'),
            'logs': os.path.join(base_experiment_dir, 'logs'),
            #'tensorboard': os.path.join(base_experiment_dir, 'tensorboard'),
            'results': os.path.join(base_experiment_dir, 'results'),
            'analysis': os.path.join(base_experiment_dir, 'analysis'),
            'checkpoints': os.path.join(base_experiment_dir, 'checkpoints'),
            'artifacts': os.path.join(base_experiment_dir, 'artifacts')
        }

        created_dirs = {}
        for key, path in dirs.items():
            created_dirs[key] = self.ensure_directory(path)

        return created_dirs

    def clean_directory(self, directory_path, create_new=True):
        """
        Clean a directory by removing all its contents.
        Optionally recreate it after cleaning.
        """
        try:
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path)
                self.logger.info(f"Cleaned directory: {directory_path}")

            if create_new:
                self.ensure_directory(directory_path)
        except Exception as e:
            self.logger.error(f"Error cleaning directory {directory_path}: {str(e)}")
            raise

    def validate_directory_structure(self, required_dirs):
        """
        Validate that all required directories exist.
        Creates any missing directories.
        """
        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
                self.ensure_directory(dir_path)

        if missing_dirs:
            self.logger.warning(f"Created missing directories: {', '.join(missing_dirs)}")

        return missing_dirs

    def get_latest_directory(self, base_path, prefix=""):
        """Get the most recent timestamped directory in the base path"""
        try:
            directories = [d for d in os.listdir(base_path)
                         if os.path.isdir(os.path.join(base_path, d))
                         and (not prefix or d.startswith(prefix))]

            if not directories:
                return None

            return max(directories, key=lambda x: os.path.getctime(os.path.join(base_path, x)))
        except Exception as e:
            self.logger.error(f"Error getting latest directory in {base_path}: {str(e)}")
            return None

