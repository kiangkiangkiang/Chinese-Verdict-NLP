import os

# 6/19
learning_rate = 5e-05
for i in range(6):
    os.system(
        f"python3 ../../information_extraction/model/finetune.py  \
        --device gpu:3 \
        --logging_steps 10 \
        --save_steps 500 \
        --eval_steps 500 \
        --seed 1000 \
        --model_name_or_path uie-base  \
        --train_path ../../information_extraction/data/arrange_final_data_mean/training_data.txt \
        --dev_path ../../information_extraction/data/arrange_final_data_mean/eval_data.txt  \
        --test_path ../../information_extraction/data/arrange_final_data_mean/testing_data.txt  \
        --max_seq_len 768  \
        --read_data_method chunk \
        --per_device_eval_batch_size 8 \
        --per_device_train_batch_size  8 \
        --multilingual True \
        --num_train_epochs 5 \
        --learning_rate {learning_rate} \
        --label_names 'start_positions' 'end_positions' \
        --do_train \
        --do_eval \
        --do_export \
        --output_dir ../../information_extraction/results/ckp_arrange_final_data_mean_768_epochs5_seed_1000_lr{learning_rate}\
        --overwrite_output_dir \
        --disable_tqdm True \
        --metric_for_best_model eval_f1 \
        --load_best_model_at_end  True \
        --save_total_limit 1"
    )
    learning_rate = learning_rate / 2