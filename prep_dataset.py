import os
import glob
from pickle import load
import tf_keras as tfk
import numpy as np
import random
import tensorflow as tf
import utils
from dataset import get_pause_features, get_intervention_features, get_compare_features
import tensorflow_probability as tfp

# Define tfp distribution

tfd = tfp.distributions

def build_distribution_lambda(t):
    return tfd.Normal(loc=t[..., :1], scale=tf.math.softplus(t[..., 1:]) + 1e-6)

@tf.function(reduce_retracing=True)
def predict_model(model, feature):
    feature=tf.convert_to_tensor(feature,dtype=tf.float32)
    return model(feature, training=False)


def find_closest_id(mmse_target, metadata_file):
    with open(metadata_file, 'r') as file:
        lines = file.readlines()[1:]  # Skip the header

    mmse_diffs = []
    for line in lines:
        id_, _, _, mmse = line.strip().split(';')
        mmse = int(mmse)
        mmse_diffs.append((id_.strip(), abs(mmse - mmse_target)))

    min_diff = min([diff for _, diff in mmse_diffs])
    closest_ids = [id_ for id_, diff in mmse_diffs if diff == min_diff]


    selected_id = random.choice(closest_ids)
    return selected_id


def prepare_data(dataset_dir, target_mmse):
    if target_mmse >27:
        target_mmse = 27
    # Determine which type of data to use based on MMSE score
    is_cc = target_mmse > 27
    data_type = 'cc' if is_cc else 'cd'
    metadata_file = os.path.join(dataset_dir, f'{data_type}_meta_data.txt')
    selected_id = find_closest_id(target_mmse, metadata_file)
    # Load subject files for the selected type only
    subject_files = sorted(glob.glob(os.path.join(dataset_dir, f'transcription/{data_type}/{selected_id}*.cha')))
    # Extract just the ID part without trying to split on multiple delimiters
    subjects = np.array([os.path.splitext(os.path.basename(f))[0] for f in subject_files])
    # Load Intervention Data
    files = sorted(glob.glob(os.path.join(dataset_dir, f'transcription/{data_type}/{selected_id}*.cha')))

    all_speakers = [get_intervention_features(filename, 11) for filename in files]
    X_intervention = np.array(all_speakers).astype(np.float32)
    y_intervention = np.zeros((len(all_speakers), 2))
    y_intervention[:, 0 if is_cc else 1] = 1
    print(f"Intervention data prepared with shapes: {X_intervention.shape}, {y_intervention.shape}")
    # Load regression values
    y_reg = utils.get_regression_values(metadata_file)
    # Find the index of the selected_id in subjects array
    selected_idx = np.where(subjects == selected_id)[0]
    if len(selected_idx) == 0:
        raise ValueError(f"Selected ID {selected_id} not found in subjects array. Available subjects: {subjects}")
    # Take the first index since we should only have one match
    y_reg_selected = np.array([y_reg[selected_idx[0]]])
    print(f"Regression values selected: {y_reg_selected}")
    # Load Pause Data
    transcription_files = sorted(glob.glob(os.path.join(dataset_dir, f'transcription/{data_type}/{selected_id}*.cha')))
    audio_files = sorted(
        glob.glob(os.path.join(dataset_dir, f'Full_wave_enhanced_audio/{data_type}/{selected_id}*.wav')))
    all_counts = [get_pause_features(t_f, a_f) for t_f, a_f in zip(transcription_files, audio_files)]
    X_pause = np.array(all_counts).astype(np.float32)
    y_pause = np.zeros((len(all_counts), 2))
    y_pause[:, 0 if is_cc else 1] = 1
    print(f"Pause data prepared with shape: {X_pause.shape}")
    # Load Compare Data
    compare_files = sorted(glob.glob(os.path.join(dataset_dir, f'compare/{data_type}/compare_{selected_id}*.csv')))
    X_compare = np.array([get_compare_features(f) for f in compare_files]).astype(np.float32)
    y_compare = np.zeros((len(compare_files), 2))
    y_compare[:, 0 if is_cc else 1] = 1
    print(f"Compare data prepared with shapes: {X_compare.shape}, {y_compare.shape}")
    return {
        'intervention': X_intervention,
        'pause': X_pause,
        'compare': X_compare,
        'y_clf': y_intervention,
        'y_reg': y_reg_selected,
        'subjects': subjects
    }
def negloglik(y, p_y):
    return -p_y.log_prob(y)

def predict(mmse_param):
    data = prepare_data("DementiaBank/0extra/ADReSS-IS2020-train/ADReSS-IS2020-data/train", mmse_param)  # Example MMSE target
    sc = load(open(os.path.join('m/models/class', 'compare/scaler_{}.pkl'.format(3)), 'rb'))
    pca = load(open(os.path.join('m/models/class', 'compare/pca_{}.pkl'.format(3)), 'rb'))
    compare_x = sc.transform(data['compare'])
    print(f"Shape after scaling: {compare_x.shape}")
    compare_x = pca.transform(compare_x)
    print(f"Shape after PCA: {compare_x.shape}")
    probs = []
    voted_predictions = []
    saved_model_class = []
    features = []
    model_types = ['compare', 'intervention', 'pause']
    print("Model_types", model_types)
    for m in model_types:
        print("M", m)
        model_files = sorted(glob.glob(os.path.join('m/models/class', '{}/*.keras'.format(m))))
        print("Model_files", model_files)
        saved_models = list(
            map(lambda x: tfk.models.load_model(x, custom_objects={'negloglik': negloglik}, safe_mode=False),
                model_files))
        saved_model_class = saved_models
        for m in model_types:
            if m == 'compare':
                # Ensure the feature tensor has the correct shape
                if compare_x.shape[1] > 11:
                    compare_x = compare_x[:, :11]
                features.append(compare_x)
            else:
                features.append(data[m])
    for model, feature in zip(saved_model_class, features):
        pred = predict_model(model, feature)
        probs.append(pred)
        print("Hello")
    probs = np.stack(probs, axis=1)

    print("you got no probs", probs)
    saved_model_regression = []
    sc = load(open(os.path.join('m/models/regr', 'compare/scaler_{}.pkl'.format(10)), 'rb'))
    pca = load(open(os.path.join('m/models/regr', 'compare/pca_{}.pkl'.format(10)), 'rb'))
    compare_x = sc.transform(data['compare'])
    print(f"Shape after scaling: {compare_x.shape}")
    compare_x = pca.transform(compare_x)
    print(f"Shape after PCA: {compare_x.shape}")
    # for m in model_types:
    #     model_files = sorted(glob.glob(os.path.join('m/models/regr', '{}/*.keras'.format(m))))
    #     saved_models = list(map(lambda x: tfk.models.load_model(x, custom_objects={
    #         'DistributionLambda': tfp.layers.DistributionLambda,
    #         'build_distribution_lambda': build_distribution_lambda,
    #         'negloglik': negloglik,
    #     }, safe_mode=False), model_files))
    #     saved_model_regression = saved_models
    #     if m == 'compare':
    #         # Ensure the feature tensor has the correct shape
    #         if compare_x.shape[1] > 11:
    #             compare_x = compare_x[:, :11]
    #         features.append(compare_x)
    #     else:
    #         features.append(data[m])
    # preds = []
    # for model, feature in zip(saved_model_regression, features):
    #     predictions = model(feature)
    #     r_probs = predictions.mean().numpy()
    #     preds.append(r_probs)
    # preds = np.stack(preds, axis=1)
    # voted_predictions = np.min(preds, axis=1)
    # print("Voted predictions:", voted_predictions)
    # # Define the mapping range
    # old_min, old_max = 514, 1235  # Original range of voted predictions
    # new_min, new_max = 0, 27  # Target MMSE range

    stage = probs[0][0][0]
    if stage >0.03 and stage <0.05:
        stage = 3
        dementia='AD'
    elif stage >0.05 and stage <0.07:
        stage = 2
        dementia='AD'
    elif stage >0.07 and stage <0.09:
        stage = 1
        dementia='AD'
    elif stage >0.09 and stage <0.10:
        stage = 0
        dementia='AD'
    else:
        stage = 4
        dementia=' No AD'
    return dementia, stage

@tf.function(reduce_retracing=True)
def predict_model(model, feature):
    feature=tf.convert_to_tensor(feature,dtype=tf.float32)
    return model(feature)

