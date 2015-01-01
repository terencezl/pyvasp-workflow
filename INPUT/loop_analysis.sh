for i in 7 8 9 10 11 12; do
    cp INPUT/run_elastic_spec.yaml run_elastic_spec_kp$i.yaml
    sed -i "/divisions/c \ \ divisions: [$i, $i, $i]" run_elastic_spec_kp$i.yaml
    cp INPUT/run_elastic.job run_elastic.job.temp
    sed -i "/python/c python INPUT/run_elastic.py run_elastic_spec_kp$i.yaml" run_elastic.job.temp
    qsub run_elastic.job.temp
    rm run_elastic.job.temp
done
