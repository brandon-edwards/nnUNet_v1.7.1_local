import argparse

from nnunet.paths import default_plans_identifier

from fedsim_data_setup import setup_fedsim_data
from fedsim_model_setup import trim_data_and_setup_fedsim_models

def main(postopp_pardir, first_three_digit_task_num, init_model_path, init_model_info_path, task_name, network, network_trainer, fold, plans_identifier=default_plans_identifier, timestamp_selection='latest', num_institutions=1, cuda_device='0'):
    """
    Generates symlinks to be used for NNUnet training, assuming we already have a 
    dataset on file coming from MLCommons RANO experiment data prep.

    Also creates the json file for the data, as well as runs nnunet preprocessing.

    should be run using a virtual environment that has nnunet version 1 installed.

    args:
    postopp_src_pardir(str)     : Parent directory for postopp data.  
                                    Should have 'data' and 'labels' subdirectories with structure:
                                    ├── data
                                    │   ├── AAAC_0
                                    │   │   ├── 2008.03.30
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t1c.nii.gz
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t1n.nii.gz
                                    │   │   │   ├── AAAC_0_2008.03.30_brain_t2f.nii.gz
                                    │   │   │   └── AAAC_0_2008.03.30_brain_t2w.nii.gz
                                    │   │   └── 2008.12.17
                                    │   │       ├── AAAC_0_2008.12.17_brain_t1c.nii.gz
                                    │   │       ├── AAAC_0_2008.12.17_brain_t1n.nii.gz
                                    │   │       ├── AAAC_0_2008.12.17_brain_t2f.nii.gz
                                    │   │       └── AAAC_0_2008.12.17_brain_t2w.nii.gz
                                    │   ├── AAAC_1
                                    │   │   ├── 2008.03.30_duplicate
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t1c.nii.gz
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t1n.nii.gz
                                    │   │   │   ├── AAAC_1_2008.03.30_duplicate_brain_t2f.nii.gz
                                    │   │   │   └── AAAC_1_2008.03.30_duplicate_brain_t2w.nii.gz
                                    │   │   └── 2008.12.17_duplicate
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t1c.nii.gz
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t1n.nii.gz
                                    │   │       ├── AAAC_1_2008.12.17_duplicate_brain_t2f.nii.gz
                                    │   │       └── AAAC_1_2008.12.17_duplicate_brain_t2w.nii.gz
                                    │   ├── AAAC_extra
                                    │   │   └── 2008.12.10
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t1c.nii.gz
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t1n.nii.gz
                                    │   │       ├── AAAC_extra_2008.12.10_brain_t2f.nii.gz
                                    │   │       └── AAAC_extra_2008.12.10_brain_t2w.nii.gz
                                    │   ├── data.csv
                                    │   └── splits.csv
                                    ├── labels
                                    │   ├── AAAC_0
                                    │   │   ├── 2008.03.30
                                    │   │   │   └── AAAC_0_2008.03.30_final_seg.nii.gz
                                    │   │   └── 2008.12.17
                                    │   │       └── AAAC_0_2008.12.17_final_seg.nii.gz
                                    │   ├── AAAC_1
                                    │   │   ├── 2008.03.30_duplicate
                                    │   │   │   └── AAAC_1_2008.03.30_duplicate_final_seg.nii.gz
                                    │   │   └── 2008.12.17_duplicate
                                    │   │       └── AAAC_1_2008.12.17_duplicate_final_seg.nii.gz
                                    │   └── AAAC_extra
                                    │       └── 2008.12.10
                                    │           └── AAAC_extra_2008.12.10_final_seg.nii.gz
                                    └── report.yaml

    first_three_digit_task_num(str) : Should start with '5'. If fedsim == N, all N task numbers starting with this number will be used.
    init_model_path (str)           : path to initial (pretrained) model file [default None] - must be provided if init_model_info_path is.
                                      [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION. OTHERWISE ARCHITECTURE IS CHOSEN USING COLLABORATOR 0 DATA.]
    init_model_info_path(str)       : path to initial (pretrained) model info pikle file [default None]- must be provided if init_model_path is.
                                      [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION. OTHERWISE ARCHITECTURE IS CHOSEN USING COLLABORATOR 0 DATA.]
    task_name(str)                  : Name of task that is part of the task name
    network(str)                    : NNUnet network to be used
    network_trainer(str)            : NNUnet network trainer to be used
    fold(str)                       : Fold to train on, can be a sting indicating an int, or can be 'all'
    plans_identifier(str)           : Used in the plans file naming.
    task_name(str)                  : Any string task name.
    timestamp_selection(str)        : Indicates how to determine the timestamp to pick, only 'earliest' and 'latest' are supported.
                                      for each subject ID at the source: 'latest' and 'earliest' are the only ones supported so far
    num_institutions(int)           : Number of simulated institutions to shard the data into.
    """

    # some argument inspection
    task_digit_length = len(str(first_three_digit_task_num))
    if task_digit_length != 3:
         raise ValueError(f'The number of digits in {first_three_digit_task_num} should be 3, but it is: {task_digit_length} instead.')
    if str(first_three_digit_task_num)[0] != '5':
         raise ValueError(f"The three digit task number: {first_three_digit_task_num} should start with 5 to avoid NNUnet repository tasks, but it starts with {first_three_digit_task_num[0]}")    
    if init_model_path or init_model_info_path:
          if not init_model_path or not init_model_info_path:
                raise ValueError(f"If either init_model_path or init_model_info_path are provided, they both must be.")
          


    # task_folder_info is a zipped lists indexed over tasks (collaborators)
    #                  zip(task_nums, tasks, nnunet_dst_pardirs, nnunet_images_train_pardirs, nnunet_labels_train_pardirs)
    tasks= setup_fedsim_data(postopp_pardir=postopp_pardir, 
                             first_three_digit_task_num=first_three_digit_task_num, 
                             task_name=task_name, 
                             timestamp_selection=timestamp_selection, 
                             num_institutions=num_institutions)
    # trim 2d data if not working with 2d model, and distribute common model architecture across simulated collaborators
    trim_data_and_setup_fedsim_models(tasks=tasks, 
                                      network=network, 
                                      network_trainer=network_trainer, 
                                      plans_identifier=plans_identifier, 
                                      fold=fold, 
                                      init_model_path=init_model_path, 
                                      init_model_info_path=init_model_info_path, 
                                      cuda_device=cuda_device)

if __name__ == '__main__':

        argparser = argparse.ArgumentParser()
        argparser.add_argument(
            '--postopp_pardir',
            type=str,
            help="Parent directory to postopp data (should have 'data' and 'labels' subdirectories).")
        argparser.add_argument(
            '--first_three_digit_task_num',
            type=int,
            help="Should start with '5'. If fedsim == N, all N task numbers starting with this number will be used.")
        argparser.add_argument(
            '--init_model_path',
            type=str,
            default=None,
            help="Path to initial (pretrained) model file [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION. OTHERWISE ARCHITECTURE IS CHOSEN USING COLLABORATOR 0's DATA.].")
        argparser.add_argument(
            '--init_model_info_path',
            type=str,
            default=None,
            help="Path to initial (pretrained) model info file [ONLY USE IF YOU KNOW THE MODEL ARCHITECTURE MAKES SENSE FOR THE FEDERATION. OTHERWISE ARCHITECTURE IS CHOSEN USING COLLABORATOR 0's DATA.].")
        argparser.add_argument(
            '--task_name',
            type=str,
            help="Part of the NNUnet data task directory name. With 'first_three_digit_task_num being 'XXX', the directory name becomes: .../nnUNet_raw_data_base/nnUNet_raw_data/TaskXXX_<task_name>.")
        argparser.add_argument(
            '--network',
            type=str,
            default='3d_fullres',
            help="NNUnet network to be used.")
        argparser.add_argument(
            '--network_trainer',
            type=str,
            default='nnUNetTrainerV2',
            help="NNUnet network trainer to be used.")
        argparser.add_argument(
            '--fold',
            type=str,
            default='0',
            help="Fold to train on, can be a sting indicating an int, or can be 'all'.")
        argparser.add_argument(
            '--timestamp_selection',
            type=str,
            default='latest',
            help="Indicates how to determine the timestamp to pick for each subject ID at the source: 'latest' and 'earliest' are the only ones supported so far.")        
        argparser.add_argument(
            '--num_institutions',
            type=int,
            default=1,
            help="Number of symulated insitutions to shard the data into.")
        argparser.add_argument(
            '--cuda_device',
            type=str,
            default='0',
            help="Used for the setting of os.environ['CUDA_VISIBLE_DEVICES']")     

        args = argparser.parse_args()

        kwargs = vars(args)

        main(**kwargs)
