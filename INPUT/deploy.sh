task="$1"
subdirname="$2"
shift 2

# for i in `cat INPUT/element.txt`; do
for i in Sc_sv Mn_pv Zn; do
# for i in Sc_sv Ti_sv V_sv Cr_pv Mn_pv Fe Co Ni Cu Zn   Y_sv Zr_sv Nb_sv Mo_pv Tc_pv Ru_pv Rh_pv Pd Ag Cd   Hf_pv Ta_pv W_pv Re Os Ir Pt Au; do
# for i in Cr_pv Fe; do
    cp INPUT/${task}_spec.yaml ${task}_spec_$i.yaml
    sed -i "/elem_types/c elem_types: [$i, N]" ${task}_spec_$i.yaml
    cp INPUT/${task}.job ${task}_$i.job
    sed -i "/python/c python INPUT/${task}.py ${task}_spec_$i.yaml ${subdirname} $@" ${task}_$i.job
    qsub ${task}_$i.job
    rm ${task}_$i.job
done
