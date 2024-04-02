
import os
import subprocess

from nnunet.dataset_conversion.utils import generate_dataset_json

"""
This script is similar to the fedsim_data_setup, but does not assume the data
being used is from the medperf data prep pipeline.
In fact regular BraTS is assumed.

I use some fedsim code but simply set num_institutions to 1
"""


num_to_modality = {'_0000': '_t1.nii.gz',
                   '_0001': '_t2.nii.gz',
                   '_0002': '_t1ce.nii.gz',
                   '_0003': '_flair.nii.gz'}


def subject_to_mask_path(pardir, subject):
    mask_fname = f'{subject}_seg.nii.gz'
    return os.path.join(pardir, subject, mask_fname)


def create_task_folder(task_num, task_name):
    """
    Creates the task folder
    """

    task = f'Task{str(task_num)}_{task_name}'

    # The NNUnet data path is obtained from an environmental variable
    nnunet_dst_pardir = os.path.join(os.environ['nnUNet_raw_data_base'], 'nnUNet_raw_data', f'{task}')
        
    nnunet_images_train_pardir = os.path.join(nnunet_dst_pardir, 'imagesTr')
    nnunet_labels_train_pardir = os.path.join(nnunet_dst_pardir, 'labelsTr')

    if os.path.exists(nnunet_images_train_pardir) and os.path.exists(nnunet_labels_train_pardir):
        raise ValueError(f"Train images pardirs: {nnunet_images_train_pardir} and {nnunet_labels_train_pardir} both already exist. Please move them both and rerun to prevent overwriting.")
    elif os.path.exists(nnunet_images_train_pardir):
        raise ValueError(f"Train images pardir: {nnunet_images_train_pardir} already exists, please move and run again to prevent overwriting.")
    elif os.path.exists(nnunet_labels_train_pardir):
        raise ValueError(f"Train labels pardir: {nnunet_labels_train_pardir} already exists, please move and run again to prevent overwriting.")
    
    os.makedirs(nnunet_images_train_pardir, exist_ok=False)
    os.makedirs(nnunet_labels_train_pardir, exist_ok=False) 

    return task, nnunet_dst_pardir, nnunet_images_train_pardir, nnunet_labels_train_pardir
    

def symlink_one_subject(brats_subject, brats_pardir, nnunet_images_train_pardir, nnunet_labels_train_pardir):
    brats_subject_dirpath = os.path.join(brats_pardir, brats_subject)
            
    # Copy label first
    label_src_path = os.path.join(brats_subject_dirpath, brats_subject + '_seg.nii.gz')
    label_dst_path = os.path.join(nnunet_labels_train_pardir, brats_subject + '.nii.gz')
    os.symlink(src=label_src_path, dst=label_dst_path)

    # Copy images
    for num in num_to_modality:
        src_path = os.path.join(brats_subject_dirpath, brats_subject + num_to_modality[num])
        dst_path = os.path.join(nnunet_images_train_pardir,brats_subject + num + '.nii.gz')
        os.symlink(src=src_path, dst=dst_path)


def setup_data(brats_pardir, task_num, task_name):
    """
    Generates symlinks to be used for NNUnet training, assuming we already have a 
    dataset on file in BraTS format.

    Also creates the json file for the data, as well as runs nnunet preprocessing.

    should be run using a virtual environment that has nnunet version 1 installed.

    args:
    brats_pardir(str)     : Parent directory for postopp data.  
                                    Should have subdirectories with structure:
                                    │   ├── Subject1
                                    │   │   ├── 'Subject1_t1.nii.gz',
                                    |   |   |---'Subject1_t2.nii.gz',
                                    |   |   |---'Subject1_t1ce.nii.gz',
                                    |   |   |---'Subject1_flair.nii.gz'
                                    |   |-- Subject2
                                    |   |   |---Subj...
                                    |   | .
                                    |   | .

    task_num(str):                 : Should start with '5'.
    task_name(str)                 : Any string task name.

    Returns:
    task, nnunet_dst_pardir, nnunet_images_train_pardir, nnunet_labels_train_pardir 
    """

    task, nnunet_dst_pardir, nnunet_images_train_pardir, nnunet_labels_train_pardir = create_task_folder(task_num=task_num, task_name=task_name)
    
    brats_subjects = list(os.listdir(brats_pardir))   
        
    print(f"\n######### CREATING SYMLINKS TO BraTS DATA FOR TASK {task} #########\n") 
    for brats_subject in brats_subjects:
        symlink_one_subject(brats_subject=brats_subject, 
                            brats_pardir=brats_pardir, 
                            nnunet_images_train_pardir=nnunet_images_train_pardir, 
                            nnunet_labels_train_pardir=nnunet_labels_train_pardir)
        
    # Generate json file for the dataset
    print(f"\n######### GENERATING DATA JSON FILE FOR TASK {task} #########\n")
    json_path = os.path.join(nnunet_dst_pardir, 'dataset.json')
    labels = {0: 'Background', 1: 'Necrosis', 2: 'Edema', 3: 'Cavity', 4: 'Enhancing Tumor'}  # For BraTS22, the cavity is actually non-existing but NNUnet wants consecutive labels
    # labels = {0: 'Background', 1: 'Necrosis', 2: 'Edema'}
    generate_dataset_json(output_file=json_path, imagesTr_dir=nnunet_images_train_pardir, imagesTs_dir=None, modalities=tuple(num_to_modality.keys()),
                        labels=labels, dataset_name='BraTS22')
    
    # Now call the os process to preprocess the data
    print(f"\n######### OS CALL TO PREPROCESS DATA FOR TASK {task} #########\n")
    subprocess.run(["nnUNet_plan_and_preprocess",  "-t",  f"{task_num}", "--verify_dataset_integrity"])