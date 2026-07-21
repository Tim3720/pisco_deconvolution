import h5py



# Safely gets a group and ensures it has the right type
def get_group(file: h5py.File, group_name: str):
    if group_name not in file:
        raise ValueError(f"Group '{group_name}' not found in file " + file.filename)

    group = file[group_name]
    if not isinstance(group, h5py.Group):
        raise ValueError(f"Group '{group_name}' is not a group")

    return group

# Safely gets a dataset and ensures it has the right type
def get_dataset(group: h5py.Group, dataset_name: str):
    if dataset_name not in group:
        raise ValueError(f"Dataset '{dataset_name}' not found in file")

    dataset = group[dataset_name]
    if not isinstance(dataset, h5py.Dataset):
        raise ValueError(f"Dataset '{dataset_name}' is not a dataset")

    return dataset
