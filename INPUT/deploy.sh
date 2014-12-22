for i in Ti_pv; do
    cp INPUT/run_volume_spec.yaml run_volume_spec_$i.yaml
    sed -i "/elem_types/c elem_types: [$i, N]" run_volume_spec_$i.yaml
    sed -i "/python/c python INPUT/run_volume.py run_volume_spec_$i.yaml" INPUT/run_volume.job
    qsub INPUT/run_volume.job
done
