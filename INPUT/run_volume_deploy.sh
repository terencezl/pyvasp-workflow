for i in Sc_sv; do
# for i in Sc_sv Ti_sv V_sv Cr_pv Mn_pv Fe Co Ni Cu Zn; do
    cp INPUT/run_volume_spec.yaml run_volume_spec_$i.yaml
    sed -i "/elem_types/c elem_types: [$i, N]" run_volume_spec_$i.yaml
    cp INPUT/run_volume.job run_volume.job.temp
    sed -i "/python/c python INPUT/run_volume.py run_volume_spec_$i.yaml" run_volume.job.temp
    qsub run_volume.job.temp
    rm run_volume.job.temp
done
